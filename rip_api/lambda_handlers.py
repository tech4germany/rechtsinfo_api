from mangum import Mangum

from . import db, gesetze_im_internet
from .api import app

api = Mangum(app)

def update_data(event, context):
    data_dir = './downloads/gii'
    with db.session_scope() as session:
        gesetze_im_internet.update_all(session, data_dir)
