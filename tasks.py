import boto3
from invoke import task, Collection
from sqlalchemy.exc import OperationalError
import sqlalchemy_utils
import uvicorn

from rip_api import ASSET_BUCKET, db, gesetze_im_internet
from rip_api.gesetze_im_internet.download import location_from_string

ns = Collection()


# Database tasks

@task
def db_init(c):
    """
    Set up database. (Set DB url with the DB_URI env variable.)
    """
    try:
        db._engine.connect().execute('select 1')
    except OperationalError:
        sqlalchemy_utils.create_database(db.db_uri)

    db_migrate(c)


@task
def db_migrate(c):
    """
    Bring database up to date with the latest schema.
    """
    c.run("alembic upgrade head")


ns.add_collection(Collection(
    'database',
    init=db_init,
    migrate=db_migrate
))


# Tests

@task
def run_tests(c):
    """Run project test suite."""
    c.run("pytest")


ns.add_task(run_tests, 'tests')


# Ingest tasks

@task(
    help={
        "data-location": "Where to store downloaded law data (local path or S3 prefix url)"
    }
)
def download_laws(c, data_location):
    """
    Download any updated law files from gesetze-im-internet.de.
    """
    gesetze_im_internet.download_laws(location_from_string(data_location))


@task(
    help={
       "data-location": "Where law data has been downloaded (local path or S3 prefix url)"
    }
)
def ingest_data_from_location(c, data_location):
    """
    Process downloaded laws and store/update them in the DB.
    """
    with db.session_scope() as session:
        gesetze_im_internet.ingest_data_from_location(session, location_from_string(data_location))


ns.add_collection(Collection(
    'ingest',
    download_laws=download_laws,
    ingest_data=ingest_data_from_location
))


# Dev tasks

@task
def start_api_server(c):
    """Start API server in development mode."""
    uvicorn.run("rip_api.api:app", host="127.0.0.1", port=5000, log_level="info", reload=True)


ns.add_collection(Collection(
    'dev',
    start_api_server=start_api_server
))


# Example JSON tasks

@task(
    help={
        "law-abbr": "The abbreviation of the law you want to generate (slugified)"
    }
)
def json_generate(c, law_abbr):
    """
    Update JSON response for a single law in example_json/.
    """
    with db.session_scope() as session:
        law = db.find_law_by_slug(session, law_abbr)
        if not law:
            raise Exception(f'Could not find law by slug "{law_abbr}". Has it been ingested yet?')
        gesetze_im_internet.write_law_json_file(session, law, "example_json")


@task
def json_generate_all(c):
    """
    Update JSON response for a all laws in example_json/.
    """
    for law_abbr in [
        "a_kae", "aag", "aaueg_aendg", "abfaev", "abv", "abwv", "agg", "aktg", "alg", "amg", "ao", "arbgg", "arbschg",
        "arbzg", "asylg", "aufenthg", "aufenthv", "baeausbv_2004", "baederfangausbv", "bafoeg", "bahnvorschranwg",
        "bakredsitzbek", "bapostg", "bartschv", "baugb", "baunvo", "bbg", "bdsg", "beeg", "betrvg", "bgb", "bgbeg", "burlg",
        "erbstdv", "estg", "gastg", "gbo", "gg", "gkg", "gmbhg", "gvg", "gwb", "gwg", "haftpflg", "heizkostenv", "hgb", "hwo",
        "ifg", "ifsg", "inso", "irg", "jfdg", "juschg", "krwg", "kschg", "kunsturhg", "kwg", "luftsig", "mabv", "markeng",
        "muschg", "owig", "partg", "patg", "pferdewmeistprv", "prodhaftg", "puag", "rog", "rpflg", "scheckg", "sgb_1",
        "sgb_2", "sgb_3", "sgb_4", "sgb_5", "sgb_6", "skaufg", "stgb", "stpo", "stvo", "stvollzg", "tierschg", "tkg", "tmg",
        "tvg", "urhg", "uschadg", "ustdv", "uwg", "vag", "vereinsg", "vgv", "vvg_infov", "vwvfg", "waffg", "wistrg_1954",
        "wogg", "zpo", "zvg", "zwvwv"
    ]:
        json_generate(c, law_abbr)


ns.add_collection(Collection(
    'example_json',
    generate=json_generate,
    **{'generate-all': json_generate_all}
))


# Deployment-related tasks

@task
def update_bulk_law_files(c):
    """
    Generate and upload bulk law files.
    """
    with db.session_scope() as session:
        gesetze_im_internet.generate_and_upload_bulk_law_files(session)


def update_lambda_fn(function_name, s3_key):
    boto3.client("lambda").update_function_code(
        FunctionName=function_name, S3Bucket=ASSET_BUCKET, S3Key=s3_key
    )


@task
def update_lambda_deps_layer(c):
    """Build Python dependencies in docker and upload to S3."""
    print("Warning! This will run `terraform apply`. Abort if this is not what you want!")
    prompt = input("Proceed? [Y/n]")
    if prompt.strip() in ('n', 'N'):
        exit(1)

    # Build local zip file.
    c.run("./build_lambda_deps_layer_zip.sh")
    # Upload to s3.
    gesetze_im_internet.upload_file_to_s3("./lambda_deps.zip", "lambda_deps_layer.zip")
    # Rm local file.
    c.run("rm ./lambda_deps.zip")
    # Use terraform to create new layer version (layers are immutable and can only be replaced, not updated).
    c.run("[ -e .terraform ] || terraform init")
    c.run("terraform taint aws_lambda_layer_version.deps_layer")
    c.run("terraform apply")

    print("IMPORTANT: Make sure to commit and push any changes to `terraform.tfstate` and `terraform.tfstate.backup`!")


@task
def update_lambda_function(c):
    """Create application zip file and upload to S3."""
    function_s3_key = "lambda_function.zip"

    # Build local zip file.
    c.run("./build_lambda_function_zip.sh")
    # Upload to s3.
    gesetze_im_internet.upload_file_to_s3("./lambda_function.zip", function_s3_key)
    # Rm local file.
    c.run("rm ./lambda_function.zip")
    # Update Lambda functions.
    for fn in ("fellows-2020-rechtsinfo-Api", "fellows-2020-rechtsinfo-DownloadLaws", "fellows-2020-rechtsinfo-IngestLaws"):
        update_lambda_fn(fn, function_s3_key)


ns.add_collection(Collection(
    'deploy',
    update_bulk_law_files=update_bulk_law_files,
    update_lambda_deps_layer=update_lambda_deps_layer,
    update_lambda_function=update_lambda_function
))
