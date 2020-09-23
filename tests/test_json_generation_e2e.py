import json

import pytest

from rip_api import gesetze_im_internet
from rip_api.db import session_scope
from rip_api.gesetze_im_internet.download import location_from_string
from .utils import load_example_json, xml_fixtures_dir

example_law_slugs = ["alg", "ifsg", "jfdg", "skaufg"]


@pytest.mark.parametrize("slug", example_law_slugs)
def test_examples(slug):
    with session_scope() as session:
        data_location = location_from_string(xml_fixtures_dir)
        gesetze_im_internet.ingest_law(session, data_location, slug)

    with session_scope() as session:
        parsed = json.loads(gesetze_im_internet.law_json_from_slug(session, slug))

    expected = load_example_json(slug)
    assert parsed == expected
