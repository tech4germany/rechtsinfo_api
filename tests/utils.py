import glob
import json
import os

from rip_api import models
from rip_api.gesetze_im_internet import parsing

example_json_dir = os.path.join(os.path.dirname(__file__), "..", "example_json")
xml_fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "gii_xml")


def load_example_json(slug):
    with open(os.path.join(example_json_dir, slug + ".json")) as f:
        return json.load(f)


def load_law_from_xml_fixture(slug):
    xml_filename = glob.glob(os.path.join(xml_fixtures_dir, slug, "*.xml"))[0]
    law_dict = parsing.parse_law(xml_filename)
    law = models.Law.from_dict(law_dict, slug)
    return law
