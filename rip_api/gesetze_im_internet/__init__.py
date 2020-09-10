import glob
import os

from .models import law_to_api_json, Law, ContentItem
from .parsing import parse_law_xml_to_dict


def parse_law(law_dir):
    xml_files = glob.glob(f'{law_dir}/*.xml')
    assert len(xml_files) == 1, f'Expected 1 XML file in {law_dir}, got {len(xml_files)}'

    filepath = xml_files[0]
    return parse_law_xml_to_dict(filepath)


def ingest_law(session, law_dir):
    law_dict = parse_law(law_dir)
    law = Law.from_dict(law_dict)

    session.add(law)

    return law


def law_json_from_slug(session, slug, pretty=False):
    law = session.query(Law).filter_by(slug=slug).first()
    if not law:
        raise Exception(f'Could not find law by slug "{slug}". Has it been ingested yet?')

    return law_to_api_json(law, pretty=pretty)
