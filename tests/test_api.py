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


def test_happy_path(client, law):
    example_json = load_example_json('skaufg')

    with mock.patch('rip_api.db.find_law_by_slug', return_value=law):
        response = client.get('/laws/skaufg')

    assert response.status_code == 200
    assert response.json() == example_json
