from enum import Enum
from typing import Optional

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import starlette

from . import PUBLIC_ASSET_ROOT, db, models, urls
from . import api_schemas

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


@app.exception_handler(fastapi.exceptions.RequestValidationError)
async def validation_error_handler(request: fastapi.Request, exc: fastapi.exceptions.RequestValidationError):
    detail = fastapi.encoders.jsonable_encoder(exc.errors())
    return build_error_response(status_code=422, title="Unprocessable Entity", detail=detail)


class GetLawIncludeOptions(Enum):
    contents = "contents"


@app.get("/laws/{slug}", response_model=api_schemas.LawResponse)
def get_law(
    slug: str,
    include: Optional[GetLawIncludeOptions] = None
):
    schema_class = api_schemas.LawAllFields
    if include == GetLawIncludeOptions.contents:
        schema_class = api_schemas.LawAllFieldsWithContents

    with db.session_scope() as session:
        law = db.find_law_by_slug(session, slug)
        if not law:
            raise ApiException(
                status_code=404, title="Resource not found", detail="Could not find a law for this slug."
            )

        return {"data": schema_class.from_orm_model(law)}


class ListLawsIncludeOptions(Enum):
    all_fields = "all_fields"


@app.get("/laws", response_model=api_schemas.LawsResponse)
def list_laws(
    page: int = fastapi.Query(1, gt=0),
    per_page: int = fastapi.Query(10, gt=0, le=100),
    include: Optional[ListLawsIncludeOptions] = None
):
    schema_class = api_schemas.LawBasicFields
    if include == ListLawsIncludeOptions.all_fields:
        schema_class = api_schemas.LawAllFields

    with db.session_scope() as session:
        pagination = db.all_laws_paginated(session, page, per_page)
        data = [schema_class.from_orm_model(law) for law in pagination.items]

    return {
        "data": data,
        "pagination": {
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page
        },
        "links": {
            "prev": urls.list_laws(pagination.prev_page, per_page, include),
            "next": urls.list_laws(pagination.next_page, per_page, include)
        }
    }


@app.get("/laws/{slug}/articles/{article_id}", response_model=api_schemas.ContentItemResponse)
def get_article(
    slug: str,
    article_id: str
):
    with db.session_scope() as session:
        content_item = db.find_content_item_by_id_and_law_slug(session, article_id, slug)
        if not content_item:
            raise ApiException(
                status_code=404, title="Resource not found", detail="Could not find article."
            )

    return {
        "data": api_schemas.ContentItemAllFields.from_orm_model(content_item)
    }


@app.get("/search", response_model=api_schemas.SearchResultsResponse)
def get_search_results(
    q: str,
    page: int = fastapi.Query(1, gt=0),
    per_page: int = fastapi.Query(10, gt=0, le=100),
):
    orm_type_to_schema = {
        models.Law: api_schemas.LawBasicFields,
        models.ContentItem: api_schemas.ContentItemBasicFields
    }
    with db.session_scope() as session:
        pagination = db.fulltext_search_laws_content_items(session, q, page, per_page)
        data = [orm_type_to_schema[type(item)].from_orm_model(item) for item in pagination.items]

    return {
        "data": data,
        "pagination": {
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page
        },
        "links": {
            "prev": urls.search(q, pagination.prev_page, per_page),
            "next": urls.search(q, pagination.next_page, per_page)
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
