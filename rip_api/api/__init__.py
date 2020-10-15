from enum import Enum
from typing import Optional

import fastapi
from fastapi import Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import starlette

from rip_api import PUBLIC_ASSET_ROOT, api_schemas, db, models, urls
from .errors import (
    ApiException,
    api_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_error_handler,
)

app = fastapi.FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

tags_metadata = [
    {
        "name": "Laws",
        "description": "Federal legislation (Gesetze & Verordnungen)."
    },
    {
        "name": "Search",
        "description": "Full-text search in laws and articles."
    },
    {
        "name": "Bulk Downloads",
        "description": (
            "For easier integration into batch processing, we also provide regularly-updated bulk downloads containing "
            "all data available in this API."
        )
    }
]

api_description = """\
This API provides access to legal information for Germany.

For detailed information on this project (in German), see:
- [tech4germany/rechtsinfo_api](https://github.com/tech4germany/rechtsinfo_api) on Github and
- [the Tech4Germany website](https://tech.4germany.org/project/rechtsinformationsportal/).

"""

v1 = fastapi.FastAPI(
    title="Rechtsinformationen API",
    description=api_description,
    version="v1",
    openapi_tags=tags_metadata,
    docs_url=None,
    redoc_url=None,
)
app.mount("/v1", v1)


app.exception_handler(ApiException)(api_exception_handler)
app.exception_handler(Exception)(generic_exception_handler)
app.exception_handler(starlette.exceptions.HTTPException)(http_exception_handler)

v1.exception_handler(ApiException)(api_exception_handler)
v1.exception_handler(Exception)(generic_exception_handler)
v1.exception_handler(starlette.exceptions.HTTPException)(http_exception_handler)
v1.exception_handler(fastapi.exceptions.RequestValidationError)(validation_error_handler)


class ListLawsIncludeOptions(Enum):
    all_fields = "all_fields"


@v1.get(
    "/laws",
    tags=["Laws"],
    summary="List all laws",
    response_model=api_schemas.LawsResponse,
    response_model_exclude_unset=True,
)
def list_laws(
    include: Optional[ListLawsIncludeOptions] = None,
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0, le=100),
):
    """
    Lists all available laws. Use the optional query parameter `include=all_fields` to include all law metadata.
    """
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


class GetLawIncludeOptions(Enum):
    contents = "contents"


@v1.get(
    "/laws/{slug}",
    tags=["Laws"],
    summary="Get a single law",
    response_model=api_schemas.LawResponse,
    response_model_exclude_unset=True,
)
def get_law(
    slug: str = Path(..., description="URL-safe lowercased abbreviation of the law."),
    include: GetLawIncludeOptions = Query(None, description="Whether to include the laws articles & section headings.")
):
    """
    Get detailed metadata on a single law. Use the optional query parameter `include=contents` to also include the full text
    and metadata of all articles and section headings that comprise the law.

    Some laws are structured into hierarchical sections: individual items in `contents` may have a `parent` property pointing
    to to a containing section `heading` (or `heading_article` for those few section headings that also have body content).
    If a hierarchical representation of the sections is desired, it can easily be constructed:

    ```javascript
    // JavaScript
    const contentById = {}
    const hierarchicalContents = []
    for (const item of lawJson.data.contents) {
        contentById[item.id] = item
        item.children = []

        if (item.parent === null) {
            hierarchicalContents.push(item)
        } else {
            parent = contentById[item.parent.id]
            parent.children.push(item)
        }
    }
    ```

    ```python
    # Python
    content_by_id = {}
    hierarchical_contents = []
    for item in law_json['data']['contents']:
        content_by_id[item['id']] = item
        item['children'] = []

        if item['parent'] is None:
            hierarchical_contents.append(item)
        else:
            parent = content_by_id[item['parent']['id']]
            parent['children'].append(item)
    ```
    """
    with db.session_scope() as session:
        law = db.find_law_by_slug(session, slug)
        if not law:
            raise ApiException(
                status_code=404, title="Resource not found", detail="Could not find a law for this slug."
            )

        law_data = api_schemas.LawAllFields.from_orm_model(
            law,
            include_contents=(include == GetLawIncludeOptions.contents)
        )
        return api_schemas.LawResponse(data=law_data)


@v1.get(
    "/laws/{slug}/articles/{article_id}",
    tags=["Laws"],
    summary="Get an article",
    response_model=api_schemas.ContentItemResponse,
)
def get_article(
    slug: str = Path(..., description="URL-safe lowercased abbreviation of the law."),
    article_id: str = Path(..., description="The article's ID.")
):
    """
    Get data for an individual article within a law.
    """
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


@v1.get(
    "/search",
    tags=["Search"],
    summary="Search",
    response_model=api_schemas.SearchResultsResponse,
)
def get_search_results(
    q: str = Query(..., description="Œuery to search for."),
    type_filter: Optional[SearchTypeOptions] = Query(None, alias="type", description="Only return results of specified type."),
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0, le=100),
):
    """
    Returns laws and articles matching a search query.
    """
    orm_type_to_schema = {
        models.Law: api_schemas.LawBasicFields,
        models.ContentItem: api_schemas.ContentItemBasicFieldsWithLaw
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


@v1.get(
    "/bulk_downloads/all_laws.json.gz",
    tags=["Bulk Downloads"],
    summary="Single JSON object",
    status_code=302,
)
async def bulk_download_laws_json():
    """
    Returns the location of a file containing a single JSON object with information on all laws (including their
    articles and section headings).
    """
    return fastapi.responses.RedirectResponse(
        url=f"{PUBLIC_ASSET_ROOT}/all_laws.json.gz",
        status_code=302)


@v1.get(
    "/bulk_downloads/all_laws.tar.gz",
    tags=["Bulk Downloads"],
    summary="One JSON file per law",
    status_code=302,
)
async def bulk_download_laws_tarball():
    """
    Returns the location of a .tar archive containing a one JSON file per law (including its articles and section headings).
    """
    return fastapi.responses.RedirectResponse(
        url=f"{PUBLIC_ASSET_ROOT}/all_laws.tar.gz",
        status_code=302)


@v1.get(
    "/docs",
    response_class=fastapi.responses.HTMLResponse,
    include_in_schema=False,
)
async def rapidoc():
    return f"""
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
            </head>
            <body>
                <rapi-doc spec-url="/v1{v1.openapi_url}" show-header="false"
                          allow-authentication="false" allow-server-selection="false">
                </rapi-doc>
            </body>
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