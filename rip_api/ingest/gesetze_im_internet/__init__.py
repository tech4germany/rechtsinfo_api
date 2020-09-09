import os
from collections import namedtuple
from glob import glob

from lxml import etree

from .models import Article, Heading, HeadingArticle, Law
from .parsing import ArticleNorm, HeaderNorm, SectionNorm, body_norm_from_xml
from .utils import chunk_string


def _load_main_xml_doc(xml_dir, slug):
    law_dir = os.path.join(xml_dir, slug)
    xml_files = glob(f'{law_dir}/*.xml')
    assert len(xml_files) == 1, f'Expected 1 XML file in {law_dir}, got {len(xml_files)}'

    filename = xml_files[0]
    with open(filename) as f:
        return etree.parse(f)


def _build_content_items(norms):
    content_items = []

    current_parent = None
    sections_by_code = {'': None}
    items_with_children = set()

    for norm in norms:
        if isinstance(norm, ArticleNorm):
            if norm.section_info:
                code = norm.section_info['code']
                parent = _find_toc_parent(sections_by_code, code)
            else:
                parent = current_parent

            item = norm.to_content_item(parent)
            items_with_children.add(parent and parent.id)
            content_items.append(item)

        elif isinstance(norm, SectionNorm):
            code = norm.section_info['code']
            parent = _find_toc_parent(sections_by_code, code)

            item = norm.to_content_item(parent)
            items_with_children.add(parent and parent.id)
            content_items.append(item)
            sections_by_code[code] = current_parent = item

    # Convert empty heading articles -> articles
    for idx, item in enumerate(content_items):
        if type(item) == HeadingArticle and item.id not in items_with_children:
            content_items[idx] = Article(**item.dict())

    return content_items


def _find_toc_parent(sections_by_code, code):
    """
    Iterative search by successively removing 3 digits from the end of the code to find a
    match among already-added sections. Assumes an entry for ''.
    """
    chunks = chunk_string(code, 3)
    for i in reversed(range(len(chunks) + 1)):
        substring = ''.join(chunks[:i])
        if sections_by_code.get(substring):
            return sections_by_code[substring]
    return None


class LawXmlParser:
    def __init__(self, xml_dir, slug):
        doc = _load_main_xml_doc(xml_dir, slug)
        norms = doc.xpath('/dokumente/norm')
        self.header_norm = HeaderNorm.from_xml(norms[0])
        self.body_norms = (body_norm_from_xml(norm) for norm in norms[1:])

    def parse(self):
        law_props = {
            k: getattr(self.header_norm, k)
            for k in ['id', 'abbreviation', 'extra_abbreviations', 'first_published', 'source_timestamp',
                      'heading_long', 'heading_short', 'publication_info', 'status_info']
        }
        law_props['notes'] = {
            'body': self.header_norm.body,
            'documentary_footnotes': self.header_norm.documentary_footnotes
        }
        law_props['contents'] = _build_content_items(self.body_norms)

        return Law(**law_props)


def law_json_from_slug(xml_dir, slug, pretty=False):
    law_parser = LawXmlParser(xml_dir, slug)
    law = law_parser.parse()
    return law.to_api_json(pretty=pretty)
