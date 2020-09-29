import json

import pytest

from rip_api import api_schemas, db, gesetze_im_internet
from rip_api.gesetze_im_internet.download import location_from_string
from .utils import load_example_json, xml_fixtures_dir

example_law_slugs = ["alg", "ifsg", "jfdg", "skaufg", "estg"]


@pytest.fixture(autouse=True, scope="module")
def init_db():
    db.init_db()


@pytest.mark.parametrize("slug", example_law_slugs)
def test_examples(slug):
    with db.session_scope() as session:
        data_location = location_from_string(xml_fixtures_dir)
        gesetze_im_internet.ingest_law(session, data_location, slug)

    with db.session_scope() as session:
        law = db.find_law_by_slug(session, slug)
        parsed = json.loads(api_schemas.LawWithContents.from_law(law).json(indent=2))

    expected = load_example_json(slug)["data"]
    assert parsed == expected
