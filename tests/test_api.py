from unittest import mock

import pytest

from fastapi.testclient import TestClient

from rip_api import api, models
from .utils import load_example_json, load_law_from_xml_fixture


@pytest.fixture
def client():
    return TestClient(api.app)


@pytest.fixture(scope='module')
def law():
    return load_law_from_xml_fixture('skaufg')


def test_law_happy_path(client, law):
    example_json = load_example_json('skaufg')

    with mock.patch('rip_api.db.find_law_by_slug', return_value=law):
        response = client.get('/laws/skaufg')

    assert response.status_code == 200
    assert response.json() == example_json


def test_law_not_found(client):
    with mock.patch('rip_api.db.find_law_by_slug', return_value=None):
        response = client.get('/laws/unknown_slug')

    assert response.status_code == 404
    assert response.json() == {
        'errors': [
            {
                "code": 404,
                "title":  "Resource not found",
                "detail": "Could not find a law for this slug."
            }
        ]
    }

def test_generic_http_error(client):
    response = client.get('/foo')

    assert response.status_code == 404
    assert response.json() == {
        'errors': [
            {
                "code": 404,
                "title":  "Not Found",
            }
        ]
    }
