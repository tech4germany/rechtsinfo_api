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


class TestGetLaw:
    def test_law_happy_path(self, client, law):
        example_json = load_example_json("skaufg")

        with mock.patch("rip_api.db.find_law_by_slug", return_value=law):
            response = client.get("/laws/skaufg")

        assert response.status_code == 200
        assert response.json() == example_json

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
