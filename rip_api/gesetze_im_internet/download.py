import glob
from io import BytesIO
import os
import shutil
import zipfile

from lxml import etree
import requests

TOC_URL = 'http://www.gesetze-im-internet.de/gii-toc.xml'


def fetch_toc():
    response = requests.get(TOC_URL)
    response.raise_for_status()

    toc = {}

    doc = etree.fromstring(response.content)
    for item in doc.xpath('/items/item'):
        url = item.find('link').text
        slug = url.split('/')[-2]
        toc[slug] = url

    return toc


def purge_missing(data_dir, slugs):
    # Avoid deleting the whole data directory in case of a truncated toc.xml
    if len(slugs) < 2000:
        raise Exception(f'Dubious number of laws ({len(slugs)}) - aborting')

    slugs = set(slugs)
    for dir_path in glob.glob(f'{data_dir}/*/'):
        existing_slug = dir_path.split('/')[-2]
        if existing_slug not in slugs:
            shutil.rmtree(dir_path)


def replace_law_data(data_dir, gii_slug, download_url):
    dir_path = os.path.join(data_dir, gii_slug)

    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

    os.makedirs(dir_path, exist_ok=True)

    response = requests.get(download_url)
    response.raise_for_status()

    zip_archive = zipfile.ZipFile(BytesIO(response.content))
    for filename in zip_archive.namelist():
        zip_archive.extract(filename, dir_path)

