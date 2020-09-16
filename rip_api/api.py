import fastapi

from . import db
from .api_schemas import LawResponse

app = fastapi.FastAPI()


class ApiException(Exception):
    def __init__(self, status_code, title, detail):
        self.status_code = status_code
        self.title = title
        self.detail = detail


@app.exception_handler(ApiException)
def exception_handler(request: fastapi.Request, exc: ApiException):
    return fastapi.responses.JSONResponse(
        status_code=exc.status_code,
        content={
            'errors': [{
                'code': exc.status_code,
                'title': exc.title,
                'detail': exc.detail
            }]
        }
    )


@app.get('/laws/{slug}', response_model=LawResponse)
def read_law(slug: str):
    with db.session_scope() as session:
        law = db.find_law_by_slug(session, slug)
        if not law:
            raise ApiException(status_code=404, title='Resource not found', detail='Could not find a law for this slug.')
        response_model = LawResponse.from_law(law)
        return response_model
