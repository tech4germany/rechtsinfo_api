from unittest import mock

import pytest

from fastapi.testclient import TestClient

from rip_api import api
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
    included_fields = (
        "type", "id", "abbreviation", "firstPublished", "sourceTimestamp", "titleLong", "titleShort"
    )
    return {k: v for (k, v) in law_full_response_dict.items() if k in included_fields}


@pytest.fixture
def law_response_dict_with_contents():
    return load_example_json("skaufg")["data"]


class TestGetLaw:
    def test_law_happy_path(self, client, law, law_full_response_dict):
        with mock.patch("rip_api.db.find_law_by_slug", return_value=law):
            response = client.get("/laws/skaufg")

        assert response.status_code == 200
        assert response.json()["data"] == law_full_response_dict

    def test_law_include_contents(self, client, law, law_response_dict_with_contents):
        with mock.patch("rip_api.db.find_law_by_slug", return_value=law):
            response = client.get("/laws/skaufg?include=contents")

        assert response.status_code == 200
        assert response.json()["data"] == law_response_dict_with_contents

    def test_law_not_found(self, client):
        with mock.patch("rip_api.db.find_law_by_slug", return_value=None):
            response = client.get("/laws/unknown_slug")

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


class TestGetLaws:
    def test_happy_path(self, client, law, law_basic_response_dict):
        with mock.patch("rip_api.db.all_laws_paginated", return_value=make_pagination_mock(items=[law])):
            response = client.get("/laws")

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
            response = client.get("/laws?page=2&per_page=5")

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
        response = client.get("/laws?page=0")
        assert response.status_code == 422

    def test_pagination_per_page_should_be_greater_than_zero(self, client):
        response = client.get("/laws?page=2&per_page=0")
        assert response.status_code == 422

    def test_pagination_per_page_should_be_at_most_100(self, client):
        response = client.get("/laws?page=2&per_page=101")
        assert response.status_code == 422

    def test_include_all_fields(self, client, law, law_full_response_dict):
        with mock.patch("rip_api.db.all_laws_paginated", return_value=make_pagination_mock(items=[law])):
            response = client.get("/laws?include=all_fields")

        assert response.status_code == 200
        assert response.json()["data"][0] == law_full_response_dict


class TestBulkDownloads:
    def test_get_all_laws_json(self, client):
        response = client.get("/bulk_downloads/all_laws.json.gz", allow_redirects=False)

        assert response.status_code == 302
        location = response.headers["Location"]
        assert "s3" in location
        assert location.endswith("all_laws.json.gz")

    def test_get_all_laws_tarball(self, client):
        response = client.get("/bulk_downloads/all_laws.tar.gz", allow_redirects=False)

        assert response.status_code == 302
        location = response.headers["Location"]
        assert "s3" in location
        assert location.endswith("all_laws.tar.gz")


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
