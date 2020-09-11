import json
import glob
import os.path

import pytest

from rip_api import gesetze_im_internet
from rip_api.gesetze_im_internet.db import session_scope
from rip_api.gesetze_im_internet.models import Law

tests_dir = os.path.join(os.path.dirname(__file__))
example_json_dir = os.path.join(tests_dir, '..', 'example_json')
xml_fixtures_dir = os.path.join(tests_dir, 'fixtures', 'gii_xml')

example_law_slugs = [
    'alg', 'ifsg', 'jfdg', 'skaufg'
]


@pytest.mark.parametrize('slug', example_law_slugs)
def test_examples(slug):
    # TODO: use test DB which cleans up after itself, making this block unnecessary
    with session_scope() as session:
        law = session.query(Law).filter_by(slug=slug).first()
        if law:
            session.delete(law)

    with session_scope() as session:
        law_dir = os.path.join(xml_fixtures_dir, slug)
        gesetze_im_internet.ingest_law(session, law_dir, slug)

    with open(os.path.join(example_json_dir, slug + '.json')) as f:
        with session_scope() as session:
            parsed = json.loads(gesetze_im_internet.law_json_from_slug(session, slug))
        expected = json.load(f)
        assert parsed == expected
