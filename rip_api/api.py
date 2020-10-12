from enum import Enum
from typing import Optional

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import starlette

from . import PUBLIC_ASSET_ROOT, db, models, urls
from . import api_schemas

app = fastapi.FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

v1 = fastapi.FastAPI(
    docs_url=None,
    redoc_url=None
)
app.mount("/v1", v1)


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


async def api_exception_handler(request: fastapi.Request, exc: ApiException):
    return build_error_response(exc.status_code, exc.title, exc.detail)

app.exception_handler(ApiException)(api_exception_handler)
v1.exception_handler(ApiException)(api_exception_handler)


async def generic_exception_handler(request: fastapi.Request, exc: Exception):
    return build_error_response(
        status_code=500, title="Internal Server Error", detail="Something went wrong while processing your request."
    )

app.exception_handler(Exception)(generic_exception_handler)
v1.exception_handler(Exception)(generic_exception_handler)


async def http_exception_handler(request: fastapi.Request, exc: starlette.exceptions.HTTPException):
    response = build_error_response(status_code=exc.status_code, title=exc.detail)
    headers = getattr(exc, "headers", None)
    if headers:
        response.init_headers(headers)

    return response

app.exception_handler(starlette.exceptions.HTTPException)(http_exception_handler)
v1.exception_handler(starlette.exceptions.HTTPException)(http_exception_handler)


@v1.exception_handler(fastapi.exceptions.RequestValidationError)
async def validation_error_handler(request: fastapi.Request, exc: fastapi.exceptions.RequestValidationError):
    detail = fastapi.encoders.jsonable_encoder(exc.errors())
    return build_error_response(status_code=422, title="Unprocessable Entity", detail=detail)


class GetLawIncludeOptions(Enum):
    contents = "contents"


@v1.get("/laws/{slug}", response_model=api_schemas.LawResponse)
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


@v1.get("/laws", response_model=api_schemas.LawsResponse)
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


@v1.get("/laws/{slug}/articles/{article_id}", response_model=api_schemas.ContentItemResponse)
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


class SearchTypeOptions(Enum):
    laws = "laws"
    articles = "articles"


@v1.get("/search", response_model=api_schemas.SearchResultsResponse)
def get_search_results(
    q: str,
    page: int = fastapi.Query(1, gt=0),
    per_page: int = fastapi.Query(10, gt=0, le=100),
    type_filter: Optional[SearchTypeOptions] = fastapi.Query(None, alias="type")
):
    orm_type_to_schema = {
        models.Law: api_schemas.LawBasicFields,
        models.ContentItem: api_schemas.ContentItemBasicFields
    }
    with db.session_scope() as session:
        type_filter_value = type_filter and type_filter.value
        pagination = db.fulltext_search_laws_content_items(session, q, page, per_page, type_filter_value)
        data = [orm_type_to_schema[type(item)].from_orm_model(item) for item in pagination.items]

    return {
        "data": data,
        "pagination": {
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page
        },
        "links": {
            "prev": urls.search(q, pagination.prev_page, per_page, type_filter),
            "next": urls.search(q, pagination.next_page, per_page, type_filter)
        }
    }


@v1.get("/bulk_downloads/all_laws.json.gz")
async def bulk_download_laws_json():
    return fastapi.responses.RedirectResponse(
        url=f"{PUBLIC_ASSET_ROOT}/all_laws.json.gz",
        status_code=302)


@v1.get("/bulk_downloads/all_laws.tar.gz")
async def bulk_download_laws_tarball():
    return fastapi.responses.RedirectResponse(
        url=f"{PUBLIC_ASSET_ROOT}/all_laws.tar.gz",
        status_code=302)


@v1.get("/docs", response_class=fastapi.responses.HTMLResponse, include_in_schema=False)
async def rapidoc():
    return f"""
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
            </head>
            <body><rapi-doc spec-url="/v1{v1.openapi_url}"></rapi-doc></body>
        </html>
    """


@v1.get("/", include_in_schema=False)
async def redirect_root():
    return fastapi.responses.RedirectResponse(url="/docs", status_code=302)


@app.get("/", include_in_schema=False)
async def redirect_app_root():
    return fastapi.responses.RedirectResponse(url="/v1/docs", status_code=302)


@app.get("/docs", include_in_schema=False)
async def redirect_app_docs():
    return fastapi.responses.RedirectResponse(url="/v1/docs", status_code=302)
