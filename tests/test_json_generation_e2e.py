import json
import glob
import os.path

import pytest

from rip_api.ingest.gesetze_im_internet import law_json_from_slug

tests_dir = os.path.join(os.path.dirname(__file__))
example_json_dir = os.path.join(tests_dir, '..', 'example_json')
xml_fixtures_dir = os.path.join(tests_dir, 'fixtures', 'gii_xml')

example_law_slugs = [path.split('/')[-2] for path in glob.glob(os.path.join(xml_fixtures_dir, '*/*.xml'))]


@pytest.mark.parametrize('slug', example_law_slugs)
def test_examples(slug):
    with open(os.path.join(example_json_dir, slug + '.json')) as f:
        parsed = json.loads(law_json_from_slug(xml_fixtures_dir, slug))
        expected = json.load(f)
        assert parsed == expected
