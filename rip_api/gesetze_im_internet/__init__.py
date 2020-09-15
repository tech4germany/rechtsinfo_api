import glob
import os

import tqdm

import rip_api.db
from rip_api.models import law_to_api_json, Law
from .parsing import parse_law_xml_to_dict
from .download import create_or_replace_law_dir, fetch_toc, has_update, remove_law_dir


def find_models_for_laws(session, slugs):
    slugs = set(slugs)

    new_slugs = set()
    existing = set()
    existing_slugs = set()
    removed = set()
    removed_slugs = set()

    laws = rip_api.db.all_laws_load_only_gii_slug_and_source_timestamp(session)

    for law in laws:
        if law.gii_slug in slugs:
            existing.add(law)
            existing_slugs.add(law.gii_slug)
        else:
            removed.add(law)
            removed_slugs.add(law.gii_slug)

    new_slugs = slugs - existing_slugs - removed_slugs

    return existing, removed, new_slugs


def _verify_db_and_data_dir_sync(session, data_dir):
    db_slugs = { res[0] for res in rip_api.db.all_gii_slugs(session) }
    data_dir_slugs = { path.split('/')[-2] for path in glob.glob(f'{data_dir}/*/') }

    difference = data_dir_slugs - db_slugs
    assert len(difference) == 0, f'Found left-over directories in data dir: {difference}'


def update_all(session, data_dir):
    print('Fetching toc.xml')
    download_urls = fetch_toc()

    existing, removed, new_slugs = find_models_for_laws(session, download_urls.keys())

    # Avoid accidentally deleting all law data directories in case of errors
    if len(removed) > 250:
        raise Exception(f'Dubious number of laws to remove ({len(removed)}) - aborting')

    updated_slugs = set()
    with tqdm.tqdm(total=len(existing), desc='Checking which laws have been updated') as pbar:
        for law in existing:
            if has_update(download_urls[law.gii_slug], law.source_timestamp):
                updated_slugs.add(law.gii_slug)
            pbar.update()

    slugs_to_update = updated_slugs | new_slugs
    with tqdm.tqdm(total=len(slugs_to_update), desc='Updating laws') as pbar:
        for slug in slugs_to_update:
            create_or_replace_law_dir(data_dir, slug, download_urls[slug])
            ingest_law(session, data_dir, slug)
            session.commit()
            pbar.update()

    with tqdm.tqdm(total=len(removed), desc='Deleting removed laws') as pbar:
        for law in removed:
            remove_law_dir(data_dir, law.gii_slug)
            session.delete(law)
            session.commit()
            pbar.update()

    _verify_db_and_data_dir_sync(session, data_dir)


def parse_law(law_dir):
    xml_files = glob.glob(f'{law_dir}/*.xml')
    assert len(xml_files) == 1, f'Expected 1 XML file in {law_dir}, got {len(xml_files)}'

    filepath = xml_files[0]
    return parse_law_xml_to_dict(filepath)


def ingest_law(session, data_dir, gii_slug):
    law_dir = os.path.join(data_dir, gii_slug)
    law_dict = parse_law(law_dir)
    law = Law.from_dict(law_dict, gii_slug)

    existing_law = rip_api.db.find_law_by_doknr(session, law.doknr)
    if existing_law:
        session.delete(existing_law)
        session.flush()
    session.add(law)

    return law


def law_json_from_slug(session, slug, pretty=False):
    law = rip_api.db.find_law_by_slug(session, slug)
    if not law:
        raise Exception(f'Could not find law by slug "{slug}". Has it been ingested yet?')

    return law_to_api_json(law, pretty=pretty)
