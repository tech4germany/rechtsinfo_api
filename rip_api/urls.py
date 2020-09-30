API_BASE_URL = "https://api.rechtsinformationsportal.de"


def get_law(slug, include=None):
    if not slug:
        return None
    url = f"{API_BASE_URL}/laws/{slug}"
    if include:
        url += f"?include={include.value}"
    return url


def list_laws(page, per_page, include=None):
    if not page:
        return None
    url = f"{API_BASE_URL}/laws?page={page}&per_page={per_page}"
    if include:
        url += f"&include={include.value}"
    return url
