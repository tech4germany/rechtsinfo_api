from unittest import mock

import pytest

from fastapi.testclient import TestClient

from rip_api import api, api_schemas
from .utils import load_example_json, load_law_from_fixture


@pytest.fixture
def client():
    return TestClient(api.app)


@pytest.fixture(scope="module")
def law():
    return load_law_from_fixture("skaufg")


@pytest.fixture
def law_full_response_dict(law_response_dict_with_contents):
    return {k: v for (k, v) in law_response_dict_with_contents.items() if k != "contents"}


@pytest.fixture
def law_basic_response_dict(law_full_response_dict):
    return {k: v for (k, v) in law_full_response_dict.items() if k in api_schemas.LawBasicFields.__fields__}


@pytest.fixture
def law_response_dict_with_contents():
    return load_example_json("skaufg")["data"]


class TestGetLaw:
    def test_law_happy_path(self, client, law, law_full_response_dict):
        with mock.patch("rip_api.db.find_law_by_slug", return_value=law):
            response = client.get("/v1/laws/skaufg")

        assert response.status_code == 200
        assert response.json()["data"] == law_full_response_dict

    def test_law_include_contents(self, client, law, law_response_dict_with_contents):
        with mock.patch("rip_api.db.find_law_by_slug", return_value=law):
            response = client.get("/v1/laws/skaufg", params={"include": "contents"})

        assert response.status_code == 200
        assert response.json()["data"] == law_response_dict_with_contents

    def test_unsupported_include_value(self, client):
        response = client.get("/v1/laws/skaufg", params={"include": "unsupported"})

        assert response.status_code == 422
        assert response.json() == {
            "errors": [
                {
                    "code": 422,
                    "title": "Unprocessable Entity",
                    "detail": [
                        {
                            "loc": ["query", "include"],
                            "msg": "value is not a valid enumeration member; permitted: 'contents'",
                            "type": "type_error.enum",
                            "ctx": {
                                "enum_values": ["contents"]
                            }
                        }
                    ]
                }
            ]
        }

    def test_law_not_found(self, client):
        with mock.patch("rip_api.db.find_law_by_slug", return_value=None):
            response = client.get("/v1/laws/unknown_slug")

        assert response.status_code == 404
        assert response.json() == {
            "errors": [
                {
                    "code": 404,
                    "title": "Resource not found",
                    "detail": "Could not find a law for this slug."
                }
            ]
        }


def make_pagination_mock(items, total=1, page=1, per_page=10, prev_page=None, next_page=None):
    return mock.Mock(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        prev_page=prev_page,
        next_page=next_page
    )


class TestListLaws:
    def test_happy_path(self, client, law, law_basic_response_dict):
        with mock.patch("rip_api.db.all_laws_paginated", return_value=make_pagination_mock(items=[law])):
            response = client.get("/v1/laws")

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["data"][0] == law_basic_response_dict

        pagination = response_json["pagination"]
        assert pagination["total"] == 1
        assert pagination["page"] == 1
        assert pagination["per_page"] == 10

        links = response_json["links"]
        assert links["prev"] is None
        assert links["next"] is None

    def test_pagination(self, client, law, law_basic_response_dict):
        mock_pagination = make_pagination_mock(
            items=[law] * 5,
            total=11,
            page=2,
            per_page=5,
            prev_page=1,
            next_page=3
        )

        with mock.patch("rip_api.db.all_laws_paginated", return_value=mock_pagination):
            response = client.get("/v1/laws", params={"page": 2, "per_page": "5"})

        assert response.status_code == 200
        response_json = response.json()

        assert len(response_json["data"]) == 5

        pagination = response_json["pagination"]
        assert pagination["total"] == 11
        assert pagination["page"] == 2
        assert pagination["per_page"] == 5

        links = response_json["links"]
        assert links["prev"].endswith("/laws?page=1&per_page=5")
        assert links["next"].endswith("/laws?page=3&per_page=5")

    def test_pagination_page_should_be_greater_than_zero(self, client):
        response = client.get("/v1/laws", params={"page": 0})
        assert response.status_code == 422

    def test_pagination_per_page_should_be_greater_than_zero(self, client):
        response = client.get("/v1/laws", params={"page": 2, "per_page": 0})
        assert response.status_code == 422

    def test_pagination_per_page_should_be_at_most_100(self, client):
        response = client.get("/v1/laws", params={"page": 2, "per_page": 101})
        assert response.status_code == 422

    def test_include_all_fields(self, client, law, law_full_response_dict):
        with mock.patch("rip_api.db.all_laws_paginated", return_value=make_pagination_mock(items=[law])):
            response = client.get("/v1/laws", params={"include": "all_fields"})

        assert response.status_code == 200
        assert response.json()["data"][0] == law_full_response_dict

    def test_unsupported_include_value(self, client):
        response = client.get("/v1/laws", params={"include": "unsupported"})

        assert response.status_code == 422
        assert response.json() == {
            "errors": [
                {
                    "code": 422,
                    "title": "Unprocessable Entity",
                    "detail": [
                        {
                            "loc": ["query", "include"],
                            "msg": "value is not a valid enumeration member; permitted: 'all_fields'",
                            "type": "type_error.enum",
                            "ctx": {
                                "enum_values": ["all_fields"]
                            }
                        }
                    ]
                }
            ]
        }


class TestGetArticle:
    def test_happy_path(self, client):
        content_item = mock.Mock()
        content_item.configure_mock(
            item_type="article",
            doknr="BJNR001950896BJNE000102377",
            name="§ 1",
            title="Beginn der Rechtsfähigkeit",
            parent=mock.Mock(
                item_type="heading",
                doknr="BJNR001950896BJNG000302377"
            ),
            body="<P>Die Rechtsfähigkeit des Menschen beginnt mit der Vollendung der Geburt.</P>",
            footnotes=None,
            documentary_footnotes=None,
            law=mock.Mock(
                slug='bgb'
            )
        )
        with mock.patch("rip_api.db.find_content_item_by_id_and_law_slug", return_value=content_item):
            response = client.get("/v1/laws/bgb/articles/BJNR001950896BJNE000102377")

        assert response.json() == {
            "data": {
                "type": "article",
                "id": "BJNR001950896BJNE000102377",
                "url": "https://api.rechtsinformationsportal.de/v1/laws/bgb/articles/BJNR001950896BJNE000102377",
                "name": "§ 1",
                "title": "Beginn der Rechtsfähigkeit",
                "parent": {
                    "type": "heading",
                    "id": "BJNR001950896BJNG000302377"
                },
                "body": "<P>Die Rechtsfähigkeit des Menschen beginnt mit der Vollendung der Geburt.</P>",
                "footnotes": None,
                "documentaryFootnotes": None
            }
        }

    def test_not_found(self, client):
        with mock.patch("rip_api.db.find_content_item_by_id_and_law_slug", return_value=None):
            response = client.get("/v1/laws/bgb/articles/asd")

        assert response.status_code == 404


class TestBulkDownloads:
    def test_get_all_laws_json(self, client):
        response = client.get("/v1/bulk_downloads/all_laws.json.gz", allow_redirects=False)

        assert response.status_code == 302
        location = response.headers["Location"]
        assert "s3" in location
        assert location.endswith("all_laws.json.gz")

    def test_get_all_laws_tarball(self, client):
        response = client.get("/v1/bulk_downloads/all_laws.tar.gz", allow_redirects=False)

        assert response.status_code == 302
        location = response.headers["Location"]
        assert "s3" in location
        assert location.endswith("all_laws.tar.gz")


class TestSearch:
    def test_full_text_search(self, client, law):
        search_result = make_pagination_mock(items=[law, law.contents[2], law.contents[4]])
        with mock.patch("rip_api.db.fulltext_search_laws_content_items", return_value=search_result):
            response = client.get("/v1/search", params={"q": "urlaub"})

        assert response.status_code == 200

        results = response.json()["data"]
        assert len(results) == 3

        law_response_dict = {
            "type": "law",
            "id": "BJNR055429995",
            "url": "https://api.rechtsinformationsportal.de/v1/laws/skaufg",
            "firstPublished": "1995-07-20",
            "sourceTimestamp": "20200909212501",
            "titleShort": "Streitkräfteaufenthaltsgesetz",
            "titleLong": (
                "Gesetz über die Rechtsstellung ausländischer Streitkräfte bei\nvorübergehenden Aufenthalten in der "
                "Bundesrepublik Deutschland"
            ),
            "abbreviation": "SkAufG",
            "slug": "skaufg"
        }
        assert results[0] == law_response_dict

        assert results[1] == {
            "type": "headingArticle",
            "id": "BJNR055429995BJNG000200305",
            "url": "https://api.rechtsinformationsportal.de/v1/laws/skaufg/articles/BJNR055429995BJNG000200305",
            "name": "Art 2",
            "title": None,
            "law": law_response_dict
        }

        assert results[2] == {
            "type": "article",
            "id": "BJNR055429995BJNE000801310",
            "url": "https://api.rechtsinformationsportal.de/v1/laws/skaufg/articles/BJNR055429995BJNE000801310",
            "name": "§ 2",
            "title": "Grenzübertritt, Einreise",
            "law": law_response_dict
        }

    def test_includes_pagination_envelope(self, client, law):
        search_result = make_pagination_mock(
            items=[law, law.contents[2], law.contents[4]],
            next_page=2,
            per_page=2,
            total=3
        )
        with mock.patch("rip_api.db.fulltext_search_laws_content_items", return_value=search_result):
            response = client.get("/v1/search", params={"q": "urlaub", "per_page": 2})

        assert response.status_code == 200

        assert response.json()["links"] == {
            "prev": None,
            "next": "https://api.rechtsinformationsportal.de/v1/search?q=urlaub&page=2&per_page=2"
        }

        assert response.json()["pagination"] == {
            "total": 3,
            "page": 1,
            "per_page": 2
        }


def test_generic_http_error(client):
    response = client.get("/foo")

    assert response.status_code == 404
    assert response.json() == {
        "errors": [
            {
                "code": 404,
                "title": "Not Found"
            }
        ]
    }
