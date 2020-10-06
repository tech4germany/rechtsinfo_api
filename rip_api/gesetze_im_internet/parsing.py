import itertools

from lxml import etree

from .utils import chunk_string


def _text(elements, multi=False):
    def _element_text_with_tags(element):
        """Preserve XML tags in the returned text string."""
        return "".join(
            itertools.chain([element.text or ""], (etree.tostring(child, encoding="unicode") for child in element))
        ).strip()

    if elements is None or len(elements) == 0:
        return None

    values = [_element_text_with_tags(el) for el in elements]

    if multi:
        return values

    assert len(values) == 1, f"Multiple values found but not requested: {values}"
    return values[0].strip() or None


def _parse_abbrs(norm):
    abbrs = (_text(norm.xpath("metadaten/amtabk"), multi=True) or []) + _text(norm.xpath("metadaten/jurabk"), multi=True)
    abbrs_unique = list(dict.fromkeys(abbrs))
    primary, *rest = abbrs_unique

    return {"abbreviation": primary, "extra_abbreviations": rest}


def _parse_publication_info(norm):
    elements = norm.xpath("metadaten/fundstelle")
    if not elements:
        return []
    return [
        {
            "periodical": _text(el.xpath("periodikum")),
            "reference": _text(el.xpath("zitstelle"))
        } for el in elements
    ]


def _parse_status_info(norm):
    elements = norm.xpath("metadaten/standangabe")
    if not elements:
        return []
    return [
        {
            "category": _text(el.xpath("standtyp")),
            "comment": _text(el.xpath("standkommentar"))
        } for el in elements
    ]


def _parse_section_info(norm):
    if not norm.xpath("metadaten/gliederungseinheit"):
        return None

    return {
        "code": _text(norm.xpath("metadaten/gliederungseinheit/gliederungskennzahl")),
        "name": _text(norm.xpath("metadaten/gliederungseinheit/gliederungsbez")),
        "title": _text(norm.xpath("metadaten/gliederungseinheit/gliederungstitel"))
    }


def _parse_text(norm):
    elements = norm.xpath("textdaten/text")

    if not elements:
        return {}

    assert len(elements) == 1, 'Found multiple elements matching "textdaten/text"'
    text = elements[0]

    text_format = text.get("format")
    if text_format == "decorated":
        assert _text(text) is None, "Found text[@format=decorated] with unexpected text content."
        return {}

    assert text_format == "XML", f'Unknown text format {text["format"]}'

    content = _parse_text_content(text.xpath("Content"))
    toc = _text(text.xpath("TOC"))
    assert not (content and toc), "Found norm with both TOC and Content."

    data = {"body": content or toc, "footnotes": _text(text.xpath("Footnotes"))}

    return data


def _parse_text_content(content):
    text_content = _text(content)
    if not text_content or any(text_content.strip() == p for p in EMPTY_CONTENT_PATTERNS):
        return None
    return text_content


EMPTY_CONTENT_PATTERNS = ["<P/>", "<P>-</P>"]


def _parse_documentary_footnotes(norm):
    return _parse_text_content(norm.xpath("textdaten/fussnoten/Content"))


def load_norms_from_file(file_or_filepath):
    if hasattr(file_or_filepath, "read"):
        doc = etree.parse(file_or_filepath)
    else:
        with open(file_or_filepath) as f:
            doc = etree.parse(f)

    return doc.xpath("/dokumente/norm")


def extract_law_attrs(header_norm):
    abbrs = _parse_abbrs(header_norm)
    notes_text = _parse_text(header_norm)
    return {
        "doknr": header_norm.get("doknr"),
        **abbrs,
        "first_published": _text(header_norm.xpath("metadaten/ausfertigung-datum")),
        "source_timestamp": header_norm.get("builddate"),
        "title_long": _text(header_norm.xpath("metadaten/langue")),
        "title_short": _text(header_norm.xpath("metadaten/kurzue")),
        "publication_info": _parse_publication_info(header_norm),
        "status_info": _parse_status_info(header_norm),
        "notes_body": notes_text.get("body"),
        "notes_footnotes": notes_text.get("footnotes"),
        "notes_documentary_footnotes": _parse_documentary_footnotes(header_norm)
    }


def extract_contents(body_norms):
    def _extract_common_attrs(norm):
        text = _parse_text(norm)
        return {
            "doknr": norm.get("doknr"),
            "body": text.get("body"),
            "footnotes": text.get("footnotes"),
            "documentary_footnotes": _parse_documentary_footnotes(norm)
        }

    def _set_item_type(item, norm):
        if "NE" in item["doknr"]:
            item["item_type"] = "article"
        elif "NG" in item["doknr"]:
            if item["body"]:
                item["item_type"] = "heading_article"
            else:
                item["item_type"] = "heading"
        else:
            raise Exception(f"Unknown norm structure encountered: {etree.tostring(norm)}")

    def _set_name_and_title(item, norm):
        section_info = _parse_section_info(norm)

        if "NE" in item["doknr"]:
            item.update({
                "name": _text(norm.xpath("metadaten/enbez")),
                "title": _text(norm.xpath("metadaten/titel"))
            })
        elif "NG" in item["doknr"]:
            item.update({
                "name": section_info["name"],
                "title": section_info["title"]
            })
        else:
            raise Exception(f"Unknown norm structure encountered: {etree.tostring(norm)}")

    def _find_parent(sections_by_code, code):
        """
        Search by iteratively removing 3 digits from the end of the code to find a
        match among already-added sections.
        """
        chunks = chunk_string(code, 3)
        for i in reversed(range(len(chunks) + 1)):
            substring = "".join(chunks[:i])
            if sections_by_code.get(substring):
                return sections_by_code[substring]
        return None

    def _set_parent(item, norm, parser_state):
        section_info = _parse_section_info(norm)
        code = section_info and section_info["code"]

        if "NE" in item["doknr"]:
            if code:
                item["parent"] = _find_parent(parser_state["sections_by_code"], code)
            else:
                item["parent"] = parser_state["current_parent"]

        elif "NG" in item["doknr"]:
            item["parent"] = _find_parent(parser_state["sections_by_code"], code)
            parser_state["sections_by_code"][code] = parser_state["current_parent"] = item

        if item["parent"]:
            parser_state["items_with_children"].add(item["parent"]["doknr"])

    content_items = []

    parser_state = {
        "current_parent": None,
        "sections_by_code": {"": None},
        "items_with_children": set(),
    }

    for norm in body_norms:
        item = _extract_common_attrs(norm)
        _set_item_type(item, norm)
        _set_name_and_title(item, norm)
        _set_parent(item, norm, parser_state)
        content_items.append(item)

    # Convert empty heading articles to articles
    for item in content_items:
        if item["item_type"] == "heading_article" and item["doknr"] not in parser_state["items_with_children"]:
            item["item_type"] = "article"

    return content_items


def parse_law(file_or_filepath):
    header_norm, *body_norms = load_norms_from_file(file_or_filepath)

    law_attrs = extract_law_attrs(header_norm)
    law_attrs["contents"] = extract_contents(body_norms)

    return law_attrs
