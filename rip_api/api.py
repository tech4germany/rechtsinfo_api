from enum import Enum
from typing import Optional

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import starlette

from . import PUBLIC_ASSET_ROOT, db
from . import api_schemas

app = fastapi.FastAPI()
app.add_middleware(GZipMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


API_BASE_URL = "https://api.rechtsinformationsportal.de"


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


class LawIncludeOptions(Enum):
    contents = "contents"


@app.get("/laws/{slug}", response_model=api_schemas.LawResponse)
def get_law(
    slug: str,
    include: Optional[LawIncludeOptions] = None
):
    schema_class = api_schemas.LawAllFields
    if include == LawIncludeOptions.contents:
        schema_class = api_schemas.LawAllFieldsWithContents

    with db.session_scope() as session:
        law = db.find_law_by_slug(session, slug)
        if not law:
            raise ApiException(
                status_code=404, title="Resource not found", detail="Could not find a law for this slug."
            )

        return {"data": schema_class.from_law(law)}


class LawsIncludeOptions(Enum):
    all_fields = "all_fields"


@app.get("/laws", response_model=api_schemas.LawsResponse)
def get_laws(
    page: int = fastapi.Query(1, gt=0),
    per_page: int = fastapi.Query(10, gt=0, le=100),
    include: Optional[LawsIncludeOptions] = None
):
    def _generate_pagination_url(page=page):
        if not page:
            return None
        url = f"{API_BASE_URL}/laws?page={page}&per_page={per_page}"
        if include:
            url += f"&include={include.value}"
        return url

    schema_class = api_schemas.LawBasicFields
    if include == LawsIncludeOptions.all_fields:
        schema_class = api_schemas.LawAllFields

    with db.session_scope() as session:
        pagination = db.all_laws_paginated(session, page, per_page)
        data = [schema_class.from_law(law) for law in pagination.items]

    return {
        "data": data,
        "pagination": {
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page
        },
        "links": {
            "prev": _generate_pagination_url(pagination.prev_page),
            "next": _generate_pagination_url(pagination.next_page)
        }
    }


@app.get("/bulk_downloads/all_laws.json.gz")
async def bulk_download_laws_json():
    return fastapi.responses.RedirectResponse(
        url=f"{PUBLIC_ASSET_ROOT}/all_laws.json.gz",
        status_code=302)


@app.get("/bulk_downloads/all_laws.tar.gz")
async def bulk_download_laws_tarball():
    return fastapi.responses.RedirectResponse(
        url=f"{PUBLIC_ASSET_ROOT}/all_laws.tar.gz",
        status_code=302)
