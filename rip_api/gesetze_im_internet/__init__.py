import glob
import os

import tqdm

from rip_api import api_schemas, db, models
from .parsing import parse_law
from .download import create_or_replace_law_dir, fetch_toc, has_update, remove_law_dir, read_law_dir_slugs_with_timestamps


ASSET_BUCKET = "fellows-2020-rechtsinfo-assets"


def _calculate_diff(previous_slugs, current_slugs):
    previous_slugs = set(previous_slugs)
    current_slugs = set(current_slugs)

    new = current_slugs - previous_slugs
    existing = previous_slugs.intersection(current_slugs)
    removed = previous_slugs - current_slugs

    # Avoid accidentally deleting all law data directories in case of errors
    if len(removed) > 250:
        raise Exception(f"Dubious number of laws to remove ({len(removed)}) - aborting")

    return existing, new, removed


def _check_for_updates(slugs, check_fn):
    updated = set()
    with tqdm.tqdm(total=len(slugs), desc="Checking which laws have been updated") as pbar:
        for slug in slugs:
            if check_fn(slug):
                updated.add(slug)
            pbar.update()
    return updated


def _add_or_replace(slugs, add_fn):
    with tqdm.tqdm(total=len(slugs), desc="Adding new and updated laws") as pbar:
        for slug in slugs:
            add_fn(slug)
            pbar.update()


def _delete_removed(slugs, delete_fn):
    with tqdm.tqdm(total=len(slugs), desc="Deleting removed laws") as pbar:
        for slug in slugs:
            delete_fn(slug)
            pbar.update()


def download_laws(session, data_dir):
    print("Fetching toc.xml")
    download_urls = fetch_toc()

    laws_on_disk = read_law_dir_slugs_with_timestamps(data_dir)
    existing, new, removed = _calculate_diff(laws_on_disk.keys(), download_urls.keys())

    updated = _check_for_updates(existing, lambda slug: has_update(download_urls[slug], laws_on_disk[slug]))
    new_or_updated = new.union(updated)

    _add_or_replace(new_or_updated, lambda slug: create_or_replace_law_dir(data_dir, slug, download_urls[slug]))

    _delete_removed(removed, lambda slug: remove_law_dir(data_dir, slug))


def ingest_data_dir(session, data_dir):
    laws_on_disk = read_law_dir_slugs_with_timestamps(data_dir)
    laws_in_db = {
        law.gii_slug: law.source_timestamp
        for law in db.all_laws_load_only_gii_slug_and_source_timestamp()
    }
    existing, new, removed = _calculate_diff(laws_in_db.keys(), laws_on_disk.keys())

    updated = _check_for_updates(existing, lambda slug: laws_on_disk[slug] > laws_in_db[slug])
    new_or_updated = new.union(updated)

    def add_fn(slug):
        ingest_law(session, data_dir, slug)
        session.commit()
    _add_or_replace(new_or_updated, add_fn)

    print("Deleting removed laws")
    db.bulk_delete_laws_by_gii_slug(removed)
    session.commit()


def ingest_law(session, data_dir, gii_slug):
    law_dir = os.path.join(data_dir, gii_slug)
    law_dict = parse_law(law_dir)
    law = models.Law.from_dict(law_dict, gii_slug)

    existing_law = db.find_law_by_doknr(session, law.doknr)
    if existing_law:
        session.delete(existing_law)
        session.flush()
    session.add(law)

    return law


def law_json_from_slug(session, slug, pretty=False):
    law = db.find_law_by_slug(session, slug)
    if not law:
        raise Exception(f'Could not find law by slug "{slug}". Has it been ingested yet?')

    json_kwargs = {}
    if pretty:
        json_kwargs = {"indent": 2}

    return api_schemas.LawResponse.from_law(law).json(**json_kwargs)
