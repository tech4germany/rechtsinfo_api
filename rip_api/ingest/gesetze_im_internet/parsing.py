import itertools
from typing import Dict, List, Optional

from lxml import etree
import pydantic

from .models import Article, Heading, HeadingArticle


def _text(elements, multi=False):
    def _element_text_with_tags(element):
        """Preserve XML tags in the returned text string."""
        return ''.join(itertools.chain([element.text or ''], (etree.tostring(child, encoding='unicode') for child in element))).strip()

    if elements is None or len(elements) == 0:
        return None

    values = [_element_text_with_tags(el) for el in elements]

    if multi:
        return values

    assert len(values) == 1, f'Multiple values found but not requested: {values}'
    return values[0]


def _parse_abbrs(norm):
    abbrs = filter(None, _text(norm.xpath('metadaten/amtabk'), multi=True) + _text(norm.xpath('metadaten/jurabk'), multi=True))
    abbrs_unique = list(dict.fromkeys(abbrs))
    primary, *rest = abbrs_unique

    return { 'abbreviation': primary, 'extra_abbreviations': rest }


def _parse_publication_info(norm):
    elements = norm.xpath('metadaten/fundstelle')
    if not elements:
        return None
    return [
        {
            'periodical': _text(el.xpath('periodikum')),
            'reference': _text(el.xpath('zitstelle'))
        }
        for el in elements
    ]


def _parse_status_info(norm):
    elements = norm.xpath('metadaten/standangabe')
    if not elements:
        return None
    return [
        {
            'category': _text(el.xpath('standtyp')),
            'comment': _text(el.xpath('standkommentar'))
        }
        for el in elements
    ]


def _parse_section_info(norm):
    if not norm.xpath('metadaten/gliederungseinheit'):
        return None

    return {
        'code': _text(norm.xpath('metadaten/gliederungseinheit/gliederungskennzahl')),
        'label': _text(norm.xpath('metadaten/gliederungseinheit/gliederungsbez')),
        'title': _text(norm.xpath('metadaten/gliederungseinheit/gliederungstitel'))
    }


def _parse_text(norm):
    elements = norm.xpath('textdaten/text')

    if not elements:
        return None

    assert len(elements) == 1, 'Found multiple elements matching "textdaten/text"'
    text = elements[0]

    text_format = text.get('format')
    if text_format == 'decorated':
        assert _text(text) is None, 'Found text[@format=decorated] with unexpected text content.'
        return None

    assert text_format == 'XML', f'Unknown text format {text["format"]}'

    content = _parse_text_content(text.xpath('Content'))
    toc = _text(text.xpath('TOC'))
    assert not (content and toc), 'Found norm with both TOC and Content.'

    data = {
        'content': content or toc,
        'footnotes': _text(text.xpath('Footnotes'))
    }

    if not any(data.values()):
        return None

    return data


EMPTY_CONTENT_PATTERNS = [
     '<P/>', '<P>-</P>'
]


def _parse_text_content(content):
    text_content = _text(content)
    if not text_content or any(text_content.strip() == p for p in EMPTY_CONTENT_PATTERNS):
        return None
    return text_content


def _parse_footnotes(norm):
    return _parse_text_content(norm.xpath('textdaten/fussnoten/Content'))


class BaseModel(pydantic.BaseModel):
    def to_content_item(self, parent):
        if not parent:
            content_level = 0
        else:
            content_level = parent.content_level + 1

        return self.content_item_class()(parent=parent, content_level=content_level, **self.dict())


class HeaderNorm(BaseModel):
    id: str
    abbreviation: str
    extra_abbreviations: List[str]
    first_published: str
    source_timestamp: str
    heading_long: str
    heading_short: Optional[str]
    publication_info: Optional[List[Dict]]
    status_info: Optional[List[Dict]]
    body: Optional[Dict]
    documentary_footnotes: Optional[str]

    @classmethod
    def from_xml(cls, norm):
        header_props = {
            'id': norm.get('doknr'),
            **_parse_abbrs(norm),
            'first_published': _text(norm.xpath('metadaten/ausfertigung-datum')),
            'source_timestamp': norm.get('builddate'),
            'heading_long': _text(norm.xpath('metadaten/langue')),
            'heading_short': _text(norm.xpath('metadaten/kurzue')),
            'publication_info': _parse_publication_info(norm),
            'status_info': _parse_status_info(norm),
            'body': _parse_text(norm),
            'documentary_footnotes': _parse_footnotes(norm)
        }
        return cls(**header_props)


def body_norm_from_xml(norm):
    doknr = norm.get('doknr')
    if 'NE' in doknr:
        return ArticleNorm.from_xml(norm)
    elif 'NG' in doknr:
        return SectionNorm.from_xml(norm)
    else:
        raise Exception(f'Unknown norm structure encountered: {etree.tostring(norm)}')


class ArticleNorm(BaseModel):
    id: str
    name: str
    title: Optional[str]
    section_info: Optional[Dict]
    body: Optional[Dict]
    documentary_footnotes: Optional[str]

    @classmethod
    def from_xml(cls, norm):
        common_props = _parse_common_body_props(norm)
        props = {
            **common_props,
            'name': _text(norm.xpath('metadaten/enbez')),
            'title': _text(norm.xpath('metadaten/titel')),
        }
        return cls(**props)

    def content_item_class(self):
        return Article


class SectionNorm(BaseModel):
    id: str
    name: str
    title: Optional[str]
    section_info: Dict
    body: Optional[Dict]
    documentary_footnotes: Optional[str]

    @classmethod
    def from_xml(cls, norm):
        common_props = _parse_common_body_props(norm)
        props = {
            **common_props,
            'name': common_props['section_info']['label'],
            'title': common_props['section_info']['title'],
            'children': []
        }
        return cls(**props)

    def content_item_class(self):
        if self.body or self.documentary_footnotes:
            return HeadingArticle
        else:
            return Heading


def _parse_common_body_props(norm):
    return {
        'id': norm.get('doknr'),
        'section_info': _parse_section_info(norm),
        'body': _parse_text(norm),
        'documentary_footnotes': _parse_footnotes(norm)
    }