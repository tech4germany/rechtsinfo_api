import boto3
from invoke import task
import uvicorn

from rip_api import gesetze_im_internet
from rip_api.gesetze_im_internet.download import location_from_string
from rip_api.db import session_scope


@task(
    help={
        "data-location": "Where to store downloaded law data (local path or S3 prefix url)"
    }
)
def download_laws(c, data_location):
    """
    Check for updates to law zip files on gesetze-im-internet.de and download them.
    """
    gesetze_im_internet.download_laws(location_from_string(data_location))


@task(
    help={
        "data-location": "Where law data has been downloaded (local path or S3 prefix url)",
        "gii-slug": "The slug of the law you want to ingest (as used in gesetze-im-internet.de URLs)",
    }
)
def ingest_law(c, data_location, gii_slug):
    """
    Process a single law's directory and store/update it in the DB.
    """
    with session_scope() as session:
        gesetze_im_internet.ingest_law(session, location_from_string(data_location), gii_slug)


@task(
    help={
       "data-location": "Where law data has been downloaded (local path or S3 prefix url)"
    }
)
def ingest_data_from_location(c, data_location):
    """
    Process downloaded laws and store/update them in the DB.
    """
    with session_scope() as session:
        gesetze_im_internet.ingest_data_from_location(session, location_from_string(data_location))


@task(
    help={
        "data-location": "Where to store downloaded law data (local path or S3 prefix url)"
    }
)
def update_all_laws(c, data_location):
    """
    Run the full import pipeline for gesetze-im-internet.de.
    """
    download_laws(c, data_location)
    ingest_data_from_location(c, data_location)


@task(
    help={
        "law-abbr": "The abbreviation of the law you want to generate (slugified)"
    }
)
def generate_json_example(c, law_abbr):
    """
    Generate JSON response for a single law and store it in the `example_json` directory.
    """
    with session_scope() as session:
        json = gesetze_im_internet.law_json_from_slug(session, law_abbr.lower(), pretty=True)

    with open(f"example_json/{law_abbr.lower()}.json", "w") as f:
        f.write(json + "\n")


@task
def generate_json_examples(c):
    """
    Generate JSON response for a predefined set of laws and store them in the `example_json` directory.
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
        generate_json_example(c, law_abbr)


@task
def start_api_server_dev(c):
    """Start API server in development mode."""
    uvicorn.run("rip_api.api:app", host="127.0.0.1", port=5000, log_level="info", reload=True)


def update_lambda_fn(function_name, s3_key):
    boto3.client("lambda").update_function_code(
        FunctionName=function_name, S3Bucket=gesetze_im_internet.ASSET_BUCKET, S3Key=s3_key
    )


@task
def build_and_upload_lambda_deps_layer(c):
    """Build and package all Python dependencies in a docker container and upload to S3."""
    print("Warning! This will run `terraform apply`. Abort if this is not what you want!")
    prompt = input("Proceed? [Y/n]")
    if prompt.strip() in ('n', 'N'):
        exit(1)

    # Build local zip file.
    c.run("./build_lambda_deps_layer_zip.sh")
    # Upload to s3.
    boto3.client("s3").upload_file("./lambda_deps.zip", gesetze_im_internet.ASSET_BUCKET, "lambda_deps_layer.zip")
    # Rm local file.
    c.run("rm ./lambda_deps.zip")
    # Use terraform to create new layer version (layers are immutable and can only be replaced, not updated).
    c.run("terraform taint aws_lambda_layer_version.deps_layer")
    c.run("terraform apply")


@task
def build_and_upload_lambda_function(c):
    """Create zip file containing application code and upload to S3."""
    s3_key = "lambda_function.zip"
    # Build local zip file.
    c.run("./build_lambda_function_zip.sh")
    # Upload to s3.
    boto3.client("s3").upload_file("./lambda_function.zip", gesetze_im_internet.ASSET_BUCKET, s3_key)
    # Rm local file.
    c.run("rm ./lambda_function.zip")
    # Update Lambda functions.
    for fn in ("fellows-2020-rechtsinfo-Api", "fellows-2020-rechtsinfo-DownloadLaws", "fellows-2020-rechtsinfo-IngestLaws"):
        update_lambda_fn(fn, s3_key)
