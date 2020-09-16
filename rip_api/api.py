from fastapi import FastAPI

from . import db
from .api_schemas import LawResponse

app = FastAPI()


@app.get('/laws/{slug}', response_model=LawResponse)
async def read_law(slug: str):
    with db.session_scope() as session:
        law = db.find_law_by_slug(session, slug)
        response_model = LawResponse.from_law(law)
        return response_model
