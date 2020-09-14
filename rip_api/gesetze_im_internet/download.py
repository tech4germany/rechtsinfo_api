from email.utils import parsedate_to_datetime
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


def has_update(download_url, timestamp_string):
    response = requests.head(download_url)
    response.raise_for_status()

    last_modified_header = response.headers['Last-Modified']
    last_modified_string = parsedate_to_datetime(last_modified_header).strftime('%Y%m%d')

    return last_modified_string > timestamp_string


def remove_law_dir(data_dir, gii_slug):
    shutil.rmtree(os.path.join(data_dir, gii_slug), ignore_errors=True)


def create_or_replace_law_dir(data_dir, gii_slug, download_url):
    dir_path = os.path.join(data_dir, gii_slug)

    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

    os.makedirs(dir_path, exist_ok=True)

    response = requests.get(download_url)
    response.raise_for_status()

    zip_archive = zipfile.ZipFile(BytesIO(response.content))
    for filename in zip_archive.namelist():
        zip_archive.extract(filename, dir_path)

