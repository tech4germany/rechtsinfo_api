from mangum import Mangum

from . import db, gesetze_im_internet
from .api import app

api = Mangum(app)

DATA_LOCATION = f"s3://{gesetze_im_internet.ASSET_BUCKET}/downloads/gesetze_im_internet"


def download_laws(event, context):
    location = gesetze_im_internet.download.location_from_string(DATA_LOCATION)
    gesetze_im_internet.download_laws(location)


def ingest_laws(event, context):
    with db.session_scope() as session:
        location = gesetze_im_internet.download.location_from_string(DATA_LOCATION)
        gesetze_im_internet.ingest_data_from_location(session, location)
