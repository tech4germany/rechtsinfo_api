import json
from glob import glob
from os.path import basename, dirname, join, splitext

import pytest

from rip_api.ingest.gesetze_im_internet import law_json_from_slug

tests_dir = join(dirname(__file__))
example_json_dir = join(tests_dir, '..', 'example_json')
xml_dir = join(tests_dir, 'fixtures', 'gii_xml')

examples = glob(join(example_json_dir, '*.json'))

@pytest.mark.parametrize('filename', examples)
def test_examples(filename):
    slug = splitext(basename(filename))[0]
    with open(filename) as f:
        parsed = json.loads(law_json_from_slug(xml_dir, slug))
        expected = json.load(f)
        assert parsed == expected
