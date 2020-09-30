from typing import List, Optional, Union

import humps
import pydantic

from . import PUBLIC_ASSET_ROOT, urls


class ContentItem(pydantic.BaseModel):
    type: str
    id: str
    name: str
    title: Optional[str]
    parent: Optional[pydantic.create_model(
        'ContentItemReference',  # noqa
        type=(str, ...),
        id=(str, ...)
    )]

    @pydantic.validator("type", allow_reuse=True, check_fields=False)
    def type_string_must_match_model_type(cls, v):
        if v != cls.__fields__["type"].default:
            raise ValueError("type string must match model type")
        return v


class ContentItemWithTextContent(ContentItem):
    body: Optional[str] = ...
    footnotes: Optional[str] = ...
    documentaryFootnotes: Optional[str] = ...


class Heading(ContentItem):
    type: str = "heading"


class Article(ContentItemWithTextContent):
    type: str = "article"


class HeadingArticle(ContentItemWithTextContent):
    type: str = "headingArticle"


def content_item_from_db_model(item):
    model_type = ITEM_TYPE_TO_MODEL_TYPE[item.item_type]

    attrs = {
        "id": item.doknr,
        "name": item.name,
        "title": item.title,
        "parent": item.parent and {
            "type": humps.camelize(item.parent.item_type),
            "id": item.parent.doknr
        }
    }

    if model_type in (Article, HeadingArticle):
        attrs["body"] = item.body
        attrs["footnotes"] = item.footnotes
        attrs["documentaryFootnotes"] = item.documentary_footnotes

    return model_type(**attrs)


class LawBasicFields(pydantic.BaseModel):
    type: str = "law"
    id: str
    url: str
    firstPublished: str
    sourceTimestamp: str
    titleShort: Optional[str]
    titleLong: str
    abbreviation: str

    @classmethod
    def _attrs_dict_from_law(cls, law):
        return dict(
            id=law.doknr,
            url=urls.get_law(law.slug),
            abbreviation=law.abbreviation,
            firstPublished=law.first_published,
            sourceTimestamp=law.source_timestamp,
            titleShort=law.title_short,
            titleLong=law.title_long
        )

    @classmethod
    def from_law(cls, law):
        return cls(**cls._attrs_dict_from_law(law))


class LawAllFields(LawBasicFields):
    extraAbbreviations: List[str]
    publicationInfo: List[pydantic.create_model(
        'PublicationInfoItem',  # noqa
        reference=(str, ...),
        periodical=(str, ...)
    )]
    statusInfo: List[pydantic.create_model(
        'StatusInfoItem',  # noqa
        comment=(str, ...),
        category=(str, ...)
    )]
    notes: pydantic.create_model(
        'TextContent',  # noqa
        body=(Optional[str], ...),
        footnotes=(Optional[str], ...),
        documentaryFootnotes=(Optional[str], ...)
    )
    attachments: dict

    @classmethod
    def _attrs_dict_from_law(cls, law):
        attrs = super()._attrs_dict_from_law(law)

        attrs["extraAbbreviations"] = law.extra_abbreviations
        attrs["publicationInfo"] = law.publication_info
        attrs["statusInfo"] = law.status_info

        attrs["notes"] = {
            "body": law.notes_body,
            "footnotes": law.notes_footnotes,
            "documentaryFootnotes": law.notes_documentary_footnotes
        }

        attrs["attachments"] = {
            name: f"{PUBLIC_ASSET_ROOT}/gesetze_im_internet/{law.gii_slug}/{name}"
            for name in law.attachment_names
        }

        return attrs


class LawAllFieldsWithContents(LawAllFields):
    # Ordering in the Union matters, cf. LawResponse.
    contents: List[Union[Article, Heading, HeadingArticle]]

    @classmethod
    def _attrs_dict_from_law(cls, law):
        attrs = super()._attrs_dict_from_law(law)
        attrs["contents"] = [content_item_from_db_model(ci) for ci in law.contents]
        return attrs


class LawResponse(pydantic.BaseModel):
    # LawWithContents must come first in the Union: FastAPI tries them in order and only skips
    # types if there's a validation error.
    data: Union[LawAllFieldsWithContents, LawAllFields]

    @classmethod
    def from_law(cls, law):
        return cls(data=LawAllFields.from_law(law))


class LawsResponse(pydantic.BaseModel):
    data: list
    links: pydantic.create_model(
        'PaginationLinks',  # noqa
        prev=(str, None),
        next=(str, None)
    )
    pagination: pydantic.create_model(
        'Pagination',  # noqa
        total=(int, ...),
        page=(int, ...),
        per_page=(int, ...)
    )


class ContentItemResponse(pydantic.BaseModel):
    # Ordering in the Union matters, cf. LawResponse.
    data: Union[Article, Heading, HeadingArticle]


ITEM_TYPE_TO_MODEL_TYPE = {
    "article": Article,
    "heading": Heading,
    "heading_article": HeadingArticle,
}
