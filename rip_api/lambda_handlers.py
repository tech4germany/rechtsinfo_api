import boto3
from mangum import Mangum

from . import ASSET_BUCKET, db, gesetze_im_internet
from .api import app

api = Mangum(app, log_level="debug")

DATA_LOCATION = f"s3://{ASSET_BUCKET}/public/gesetze_im_internet"


def download_laws(event, context):
    location = gesetze_im_internet.download.location_from_string(DATA_LOCATION)
    gesetze_im_internet.download_laws(location)
    boto3.client("lambda").invoke(FunctionName="fellows-2020-rechtsinfo-IngestLaws", InvocationType="Event")


def ingest_laws(event, context):
    with db.session_scope() as session:
        location = gesetze_im_internet.download.location_from_string(DATA_LOCATION)
        gesetze_im_internet.ingest_data_from_location(session, location)
        gesetze_im_internet.generate_and_upload_bulk_law_files(session)
