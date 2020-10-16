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

description_api = """\
This API provides access to legal information for Germany.

For detailed information on this project (in German), see:
- [tech4germany/rechtsinfo_api](https://github.com/tech4germany/rechtsinfo_api) on Github and
- [the Tech4Germany website](https://tech.4germany.org/project/rechtsinformationsportal/).

### Note on text contents
Text contents (mainly body and footnote text, but occasionally also text in law titles and item headings) are formatted in a custom XML format, which includes some HTML-like elements, but also many custom constructs. Absent any descriptive documentation, we have only been able to guess the format's semantics. We have included our guesses here, in the hope that they will be of use to consumers of this data.

<details>
  <summary><small>Click to read more</small></summary>

Elements which exist in HTML with equivalent meaning include: `<P>`, `<pre>`, `<BR>`, `<SUB>`, `<SUP>`, `<B>`, `<I>`, `<U>`, `<small>`, `<IMG>`

Elements which exist in HTML but work differently:
- `<DL>/<DT>/<DD> and <LA>` - Definitions lists are used for enumerating paragraphs inside articles. `<DL>` attribute `Type` indicates the enumeration style (arabic/alpha/roman/etc), `Font` the text styles (normal/bold/italic/etc); `<DT>` holds the enumeration; `<DD>` holds the text content inside `<LA>` custom tags. (<a href="https://api.rechtsinformationsportal.de/v1/laws/amg/articles/BJNR024480976BJNE025900116">example</a>)
- `<table> etc` - The table format used in the data has some similarities to HTML but differs in many ways. It also bears some resemblance to the [CALS table model](https://www.oasis-open.org/specs/tablemodels.php) ([see also Wikipedia](https://en.wikipedia.org/wiki/CALS_Table_Model)). It uses `<row>` for table rows and `<entry>` for cell data. Other tags in use are: `<tgroup>`, `<thead>`, `<tfoot>`, `<tbody>`, `<colspec>`, `<spanspec>`.

Custom elements (with our buest guess at their meaning):

- `<F>` - Mathematical formulae (<a href="https://api.rechtsinformationsportal.de/v1/laws/zkg/articles/BJNR072010016BJNE005500000">example</a>)
- `<SP>` - Text with increased letter spacing (<a href="https://api.rechtsinformationsportal.de/v1/laws/fwistatv/articles/BJNR003610986BJNE000500326">example</a>)
- `<NB>` - No-wrap text (<a href="https://api.rechtsinformationsportal.de/v1/laws/eu_fahrgrbusv/articles/BJNR409800013BJNE000300000">example</a>)
- `<FnR>` - In-text reference to a footnote (<a href="https://api.rechtsinformationsportal.de/v1/laws/gwgmeldv_immobilien/articles/BJNR196500020BJNE000400000">example</a>)
- `<Footnote>` - Footnote text (<a href="https://api.rechtsinformationsportal.de/v1/laws/gwgmeldv_immobilien/articles/BJNR196500020BJNE000400000">example</a>)
- `<FnArea>` - Area for footnotes _inside_ body text (<a href="https://api.rechtsinformationsportal.de/v1/laws/euwo/articles/BJNR014530988BJNE012504377">example</a>)
- `<QuoteL>` - Opening quote marks (<a href="https://api.rechtsinformationsportal.de/v1/laws/medbvsv/articles/BJNR614700020BJNE000500000">example</a>)
- `<QuoteR>` - Closing quote marks (<a href="https://api.rechtsinformationsportal.de/v1/laws/medbvsv/articles/BJNR614700020BJNE000500000">example</a>)
- `<Title>` - Centered heading-styled text (<a href="https://api.rechtsinformationsportal.de/v1/laws/schbesv/articles/BJNR257500013BJNE001301305">example</a>)
- `<Subtitle>` - Centered subheading-styled text (<a href="https://api.rechtsinformationsportal.de/v1/laws/betrpraemdurchfg/articles/BJNR176310004BJNE001004377">example</a>)
- `<FILE>` - Links to file attachments, see also the "Note on attachments" below (<a href="https://api.rechtsinformationsportal.de/v1/laws/pstv/articles/BJNR226300008BJNE009100000">example</a>)
- `<Accolade>` - Used to indicate vertical lines in tables (<a href="https://api.rechtsinformationsportal.de/v1/laws/tabakerzv/articles/BJNR098010016BJNE003800000">example</a>)
- `<noindex>` - Unclear, possibly search-related? (<a href="https://api.rechtsinformationsportal.de/v1/laws/hhg/articles/BJNR004980955BJNE003402310">example</a>)
- `<Citation>` - Unclear, possibly like `<cite>` in HTML (<a href="https://api.rechtsinformationsportal.de/v1/laws/abfaev/articles/BJNR404310013BJNE000901116">example</a>)
- `<Split>` - Unclear, possibly a special line break (<a href="https://api.rechtsinformationsportal.de/v1/laws/ausbeignv_2009/articles/BJNR008800009BJNE001200000">example</a>)
- `<Ident>` - Unclear, used in tables of contents (<a href="https://api.rechtsinformationsportal.de/v1/laws/schausrv/articles/BJNR191310008BJNE000100000">example</a>)
- `<Revision>` - Unclear (<a href="https://api.rechtsinformationsportal.de/v1/laws/intguervg/articles/BJNR257310018BJNE001000000">example</a>)
- `<kommentar>` - Unclear (<a href="https://api.rechtsinformationsportal.de/v1/laws/binschuo/articles/BJNR139810018BJNE004800000">example</a>)
- `<ABWFORMAT>` - Unclear (<a href="https://api.rechtsinformationsportal.de/v1/laws/uelv_2_besvng/articles/BJNR026080975BJNE000501306">example</a>)
</details>

The complete format is specified (but not documented) at https://www.gesetze-im-internet.de/dtd/1.01/gii-norm.dtd.

For an example how this content can be processed and styled on a web page, see https://github.com/tech4germany/rechtsinfo-fe.

### Note on attachments
Some laws reference attachments such as images or PDF documents by file name in their text contents. Laws returned by the API include an `attachments` field which maps the referenced file names to locations where these files are hosted publicly.

### Note on hierarchical sections in laws
While some laws are simply collections of articles (_Paragrafen_ or _Artikel_), represented as content items with `type` "article", others are structured into sections with possibly several levels of subsections. To represent this, laws also include content items with `type` "heading" and articles have a `parent` field which points to the nearest heading they appear under. In some rare cases, section headings also include text content, which is represented by `type` "headingArticle".

To construct a hierarchical tree of sections, sub-sections, and articles, you can use this sample code:

<details>
  <summary><small>Click to read more</small></summary>

##### Javascript
```javascript
// JSON response for a law including contents, e.g. https://api.rechtsinformationsportal.de/v1/laws/beeg?include=contents
const lawJson = ...;
const contentById = {};
const hierarchicalContents = [];
for (const item of lawJson.data.contents) {
    contentById[item.id] = item;
    item.children = [];

    if (item.parent === null) {
        hierarchicalContents.push(item);
    } else {
        parent = contentById[item.parent.id];
        parent.children.push(item);
    }
}
```

##### Python
```python
// JSON response for a law including contents, e.g. https://api.rechtsinformationsportal.de/v1/laws/beeg?include=contents
law_json = ...
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
</details>
"""

description_page = "Result page number"
description_per_page = "Number of items per page"

v1 = fastapi.FastAPI(
    title="Rechtsinformationen API",
    description=description_api,
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
    page: int = Query(1, gt=0, description=description_page),
    per_page: int = Query(10, gt=0, le=100, description=description_per_page),
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
