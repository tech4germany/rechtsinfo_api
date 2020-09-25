import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import starlette

from . import db
from .api_schemas import LawResponse

app = fastapi.FastAPI()
app.add_middleware(GZipMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ApiException(Exception):
    def __init__(self, status_code, title, detail):
        self.status_code = status_code
        self.title = title
        self.detail = detail


def build_error_response(status_code, title, detail=None):
    error = {"code": status_code, "title": title}
    if detail:
        error["detail"] = detail

    return fastapi.responses.JSONResponse(status_code=status_code, content={"errors": [error]})


@app.exception_handler(ApiException)
async def api_exception_handler(request: fastapi.Request, exc: ApiException):
    return build_error_response(exc.status_code, exc.title, exc.detail)


@app.exception_handler(Exception)
async def generic_exception_handler(request: fastapi.Request, exc: Exception):
    return build_error_response(
        status_code=500, title="Internal Server Error", detail="Something went wrong while processing your request."
    )


@app.exception_handler(starlette.exceptions.HTTPException)
async def http_exception_handler(request: fastapi.Request, exc: starlette.exceptions.HTTPException):
    response = build_error_response(status_code=exc.status_code, title=exc.detail)
    headers = getattr(exc, "headers", None)
    if headers:
        response.init_headers(headers)

    return response


@app.get("/laws/{slug}", response_model=LawResponse)
def read_law(slug: str):
    with db.session_scope() as session:
        law = db.find_law_by_slug(session, slug)
        if not law:
            raise ApiException(
                status_code=404, title="Resource not found", detail="Could not find a law for this slug."
            )
        response_model = LawResponse.from_law(law)
        return response_model


@app.get("/bulk_downloads/all_laws.json")
async def bulk_download_laws_json():
    return fastapi.responses.RedirectResponse(
        url="https://fellows-2020-rechtsinfo-assets.s3.eu-central-1.amazonaws.com/public/all_laws.json",
        status_code=302)


@app.get("/bulk_downloads/all_laws.tar.gz")
async def bulk_download_laws_json():
    return fastapi.responses.RedirectResponse(
        url="https://fellows-2020-rechtsinfo-assets.s3.eu-central-1.amazonaws.com/public/all_laws.tar.gz",
        status_code=302)
