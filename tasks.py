import os

from invoke import task

from rip_api.ingest import gesetze_im_internet


@task(
    help={
        'xml-dir': 'The path to the directory which holds the downloaded data from gesetze-im-internet.de',
        'law-slug': 'The abbreviation of the law you want to generate (as used in its directory name)'
    }
)
def generate_json_example(c, xml_dir, law_slug):
    """
    Generate JSON response for a single law and store it in the `example_json` directory.
    """
    json = gesetze_im_internet.law_json_from_slug(xml_dir, law_slug, pretty=True)
    with open(f'example_json/{law_slug}.json', 'w') as f:
        f.write(json + '\n')

@task(
    help={
        'xml-dir': 'The path to the directory which holds the downloaded data from gesetze-im-internet.de'
    }
)
def generate_json_examples(c, xml_dir):
    """
    Generate JSON response for a predefined set of laws and store them in the `example_json` directory.
    """
    for law_slug in ['alg', 'ifsg', 'jfdg', 'skaufg']:
        generate_json_example(c, xml_dir, law_slug)
