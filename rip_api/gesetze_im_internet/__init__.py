import glob
import os

import tqdm

from .models import law_to_api_json, Law, ContentItem
from .parsing import parse_law_xml_to_dict
from .download import fetch_toc, purge_missing, replace_law_data


def download_all(data_dir, print_progress=False):
    law_urls = fetch_toc()
    purge_missing(data_dir, law_urls.keys())

    laws_iter = law_urls.items()
    if print_progress:
        laws_iter = tqdm.tqdm(laws_iter)

    for gii_slug, download_url in laws_iter:
        replace_law_data(data_dir, gii_slug, download_url)


def parse_law(law_dir):
    xml_files = glob.glob(f'{law_dir}/*.xml')
    assert len(xml_files) == 1, f'Expected 1 XML file in {law_dir}, got {len(xml_files)}'

    filepath = xml_files[0]
    return parse_law_xml_to_dict(filepath)


def ingest_law(session, law_dir, gii_slug):
    law_dict = parse_law(law_dir)
    law = Law.from_dict(law_dict, gii_slug)

    session.add(law)

    return law


def law_json_from_slug(session, slug, pretty=False):
    law = session.query(Law).filter_by(slug=slug).first()
    if not law:
        raise Exception(f'Could not find law by slug "{slug}". Has it been ingested yet?')

    return law_to_api_json(law, pretty=pretty)
