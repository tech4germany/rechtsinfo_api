import urllib.parse

API_BASE_URL = "https://api.rechtsinformationsportal.de/v1"


def _build_url(path, params=None):
    if not params:
        return API_BASE_URL + path
    else:
        return API_BASE_URL + path + '?' + urllib.parse.urlencode(params)


def get_law(slug, include=None):
    if not slug:
        return None

    params = {}
    if include:
        params['include'] = include.value

    return _build_url(f"/laws/{slug}", params)


def list_laws(page, per_page, include=None):
    if not (page and per_page):
        return None

    params = {
        "page": page,
        "per_page": per_page
    }
    if include:
        params['include'] = include.value

    return _build_url("/laws", params)


def get_article(law_slug, item_id):
    if not (law_slug and item_id):
        return None

    return _build_url(f"/laws/{law_slug}/articles/{item_id}")


def search(query, page, per_page, type_filter):
    if not (query and page and per_page):
        return None

    params = {
        "q": query,
        "page": page,
        "per_page": per_page
    }
    if type_filter:
        params['filter'] = type_filter.value

    return _build_url("/search", params)
