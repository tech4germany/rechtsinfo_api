import json
import os
import sys
import tarfile
import tempfile

import boto3
import tqdm

from rip_api import api_schemas, db, models
from .parsing import parse_law
from .download import fetch_toc, has_update


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


def _loop_with_progress(slugs, desc):
    pbar = None
    if sys.stdout.isatty():
        pbar = tqdm.tqdm(total=len(slugs), desc=desc)
    else:
        print(desc, '-', len(slugs))

    for slug in slugs:
        yield slug
        if pbar:
            pbar.update()

    if pbar:
        pbar.close()


def _check_for_updates(slugs, check_fn):
    updated = set()

    for slug in _loop_with_progress(slugs, "Checking existing laws for updates"):
        if check_fn(slug):
            updated.add(slug)

    return updated


def _add_or_replace(slugs, add_fn):
    for slug in _loop_with_progress(slugs, "Adding new and updated laws"):
        add_fn(slug)


def _delete_removed(slugs, delete_fn):
    for slug in _loop_with_progress(slugs, "Deleting removed laws"):
        delete_fn(slug)


def download_laws(location):
    print("Fetching toc.xml")
    download_urls = fetch_toc()

    print("Loading timestamps")
    laws_on_disk = location.list_slugs_with_timestamps()
    existing, new, removed = _calculate_diff(laws_on_disk.keys(), download_urls.keys())

    updated = _check_for_updates(existing, lambda slug: has_update(download_urls[slug], laws_on_disk[slug]))
    new_or_updated = new.union(updated)

    _add_or_replace(new_or_updated, lambda slug: location.create_or_replace_law(slug, download_urls[slug]))

    _delete_removed(removed, lambda slug: location.remove_law(slug))


def ingest_data_from_location(session, location):
    print("Loading timestamps")
    laws_on_disk = location.list_slugs_with_timestamps()
    laws_in_db = {
        law.gii_slug: law.source_timestamp
        for law in db.all_laws_load_only_gii_slug_and_source_timestamp(session)
    }
    existing, new, removed = _calculate_diff(laws_in_db.keys(), laws_on_disk.keys())

    updated = _check_for_updates(existing, lambda slug: laws_on_disk[slug] > laws_in_db[slug])
    new_or_updated = new.union(updated)

    def add_fn(slug):
        ingest_law(session, location, slug)
        session.commit()

    _add_or_replace(new_or_updated, add_fn)

    print("Deleting removed laws")
    db.bulk_delete_laws_by_gii_slug(session, removed)
    session.commit()


def ingest_law(session, location, gii_slug):
    law_dict = parse_law(location.xml_file_for(gii_slug))
    law = models.Law.from_dict(law_dict, gii_slug)

    existing_law = db.find_law_by_doknr(session, law.doknr)
    if existing_law:
        session.delete(existing_law)
        session.flush()
    session.add(law)

    return law


def _write_json_file(filepath, content):
    with open(filepath, "w") as f:
        f.write(content + "\n")


def write_all_law_json_files(session, dir_path):
    laws_path = dir_path + "/laws"
    os.makedirs(laws_path, exist_ok=True)

    all_laws = []

    for law in db.all_laws(session):
        law_api_model = api_schemas.Law.from_law(law)
        single_law_response = api_schemas.LawResponse(data=law_api_model)
        _write_json_file(f"{laws_path}/{law.slug}.json", single_law_response.json(indent=2))

        all_laws.append(law_api_model.dict())

    _write_json_file(f"{dir_path}/all_laws.json", json.dumps({'data': all_laws}, indent=2))


def write_law_json_file(session, law, dir_path):
    filepath = f"{dir_path}/{law.slug}.json"
    _write_json_file(filepath, api_schemas.LawResponse.from_law(law).json(indent=2))


def upload_file_to_s3(local_path, s3_key):
    s3 = boto3.client("s3")
    s3.upload_file(local_path, ASSET_BUCKET, s3_key)


def generate_and_upload_bulk_law_files(session):
    with tempfile.TemporaryDirectory() as dir_path:
        print("Generating json files")
        write_all_law_json_files(session, dir_path)

        tarfilename = f"{dir_path}/all_laws.tar.gz"
        with tarfile.open(tarfilename, "w:gz") as tf:
            tf.add(dir_path + "/laws", arcname="laws")

        print("Uploading")
        jsonfilename = f"{dir_path}/all_laws.json"
        upload_file_to_s3(tarfilename, "all_laws.tar.gz")
        upload_file_to_s3(jsonfilename, "all_laws.json")
