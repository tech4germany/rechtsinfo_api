import glob

import boto3
from invoke import task
import tqdm
import uvicorn

from rip_api import gesetze_im_internet
from rip_api.db import session_scope


@task(
    help={
        "data-dir": "Path where to store downloaded law data"
    }
)
def update_all_laws(c, data_dir):
    """
    Run the full import pipeline for gesetze-im-internet.de.
    """
    with session_scope() as session:
        gesetze_im_internet.update_all(session, data_dir)


@task(
    help={
        "data-dir": "Path where law data has been downloaded",
        "gii-slug": "The slug of the law you want to ingest (as used in gesetze-im-internet.de URLs)",
    }
)
def ingest_law(c, data_dir, gii_slug):
    """
    Process a single law's directory and store it in the DB.
    """
    with session_scope() as session:
        gesetze_im_internet.ingest_law(session, data_dir, gii_slug)


@task(
    help={
       "data-dir": "Path where law data has been downloaded"
    }
)
def ingest_data_dir(c, data_dir):
    """
    Process a whole data directory of laws and store them in the DB.
    """
    with session_scope() as session:
        for law_dir in tqdm.tqdm(glob.glob(f"{data_dir}/*/")):
            gii_slug = law_dir.split("/")[-2]
            gesetze_im_internet.ingest_law(session, data_dir, gii_slug)
            session.flush()


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


LAMBDA_ASSET_BUCKET = "fellows-2020-rechtsinfo-assets"


@task
def build_and_upload_lambda_deps_layer(c):
    """Build and package all Python dependencies in a docker container and upload to S3."""
    c.run("./build_lambda_deps_layer_zip.sh")
    boto3.client("s3").upload_file("./lambda_deps.zip", LAMBDA_ASSET_BUCKET, "lambda_deps_layer.zip")
    c.run("rm ./lambda_deps.zip")


@task
def build_and_upload_lambda_function(c):
    """Create zip file containing application code and upload to S3."""
    c.run("./build_lambda_function_zip.sh")
    boto3.client("s3").upload_file("./lambda_function.zip", LAMBDA_ASSET_BUCKET, "lambda_function.zip")
    c.run("rm ./lambda_function.zip")
