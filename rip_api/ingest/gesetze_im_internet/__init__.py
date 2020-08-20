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


ContentsRoot = namedtuple('ContentsRoot', ['children'])


def _build_content_tree(norms):
    content = []

    contentsRoot = ContentsRoot(children=[])
    current = contentsRoot
    sections_by_code = {'': contentsRoot}

    for norm in norms:
        if isinstance(norm, ArticleNorm):
            parent = current

            if norm.section_info:
                code = norm.section_info['code']
                parent = _find_toc_parent(sections_by_code, code)

            parent.children.append(norm.to_content_item())

        elif isinstance(norm, SectionNorm):
            code = norm.section_info['code']

            content_item = norm.to_content_item()
            _find_toc_parent(sections_by_code, code).children.append(content_item)
            sections_by_code[code] = current = content_item

    _postprocess_tree(contentsRoot.children)

    return contentsRoot.children


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


def _postprocess_tree(contents):
    _add_levels(contents)
    _prune_heading_articles(contents)


def _add_levels(contents, current_level=0):
    """
    Add nesting level to aid formatting.
    """
    for item in contents:
        if type(item) == Article:
            continue
        item.heading_level = current_level
        _add_levels(item.children, current_level + 1)


def _prune_heading_articles(contents):
    for idx, item in enumerate(contents):
        if type(item) == Article:
            continue

        if type(item) == HeadingArticle and not item.children:
            props = item.dict()
            del props['children']
            del props['heading_level']
            contents[idx] = Article(**props)
            continue

        _prune_heading_articles(item.children)


class LawXmlParser:
    def __init__(self, xml_dir, slug):
        doc = _load_main_xml_doc(xml_dir, slug)
        norms = doc.xpath('/dokumente/norm')
        self.header_norm = HeaderNorm.from_xml(norms[0])
        self.body_norms = (body_norm_from_xml(norm) for norm in norms[1:])

    def parse(self):
        law_props = {
            k: getattr(self.header_norm, k)
            for k in ['id', 'juris_abbrs', 'official_abbr', 'first_published', 'source_timestamp',
                      'heading_long', 'heading_short', 'publication_info', 'status_info']
        }
        law_props['prelude'] = {
            'body': self.header_norm.body,
            'footnotes': self.header_norm.footnotes
        }
        law_props['content'] = _build_content_tree(self.body_norms)

        return Law(**law_props)


def law_json_from_slug(xml_dir, slug):
    law_parser = LawXmlParser(xml_dir, slug)
    law = law_parser.parse()
    return law.to_api_json()
