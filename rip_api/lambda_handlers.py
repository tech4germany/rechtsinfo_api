from mangum import Mangum

from . import db, gesetze_im_internet
from .api import app

api = Mangum(app)

DATA_DIR = f"s3://{gesetze_im_internet.ASSET_BUCKET}/downloads/gesetze_im_internet"


def download_laws(event, context):
    with db.session_scope() as session:
        gesetze_im_internet.download_laws(session, DATA_DIR)


def ingest_data_dir(event, context):
    with db.session_scope() as session:
        gesetze_im_internet.ingest_data_dir(session, DATA_DIR)
