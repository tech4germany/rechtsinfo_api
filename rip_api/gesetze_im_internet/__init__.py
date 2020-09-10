import glob
import os

from .models import law_to_api_json, Law, ContentItem
from .parsing import parse_law_xml_to_dict


def parse_law_xml(xml_dir, slug):
    law_dir = os.path.join(xml_dir, slug)
    xml_files = glob.glob(f'{law_dir}/*.xml')
    assert len(xml_files) == 1, f'Expected 1 XML file in {law_dir}, got {len(xml_files)}'

    filename = xml_files[0]
    law_dict = parse_law_xml_to_dict(filename)
    content_item_dicts = law_dict.pop('contents')
    law = Law(**law_dict)

    content_items_by_doknr = {}
    for idx, content_item_dict in enumerate(content_item_dicts):
        parent_dict = content_item_dict.pop('parent')
        parent = parent_dict and content_items_by_doknr[parent_dict['doknr']]
        content_item = ContentItem(parent=parent, order=idx, **content_item_dict)
        law.contents.append(content_item)
        content_items_by_doknr[content_item.doknr] = content_item

    return law


def law_json_from_slug(xml_dir, slug, pretty=False):
    law = parse_law_xml(xml_dir, slug)
    return law_to_api_json(law, pretty=pretty)
