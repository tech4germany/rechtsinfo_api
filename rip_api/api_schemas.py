from typing import List, Optional, Union

import humps
import pydantic

from . import PUBLIC_ASSET_ROOT


class TextContent(pydantic.BaseModel):
    body: Optional[str] = ...
    footnotes: Optional[str] = ...
    documentaryFootnotes: Optional[str] = ...


class ContentItemReference(pydantic.BaseModel):
    type: str
    id: str


class ContentItem(pydantic.BaseModel):
    type: str
    id: str
    name: str
    title: Optional[str]
    parent: Optional[ContentItemReference]

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
        "parent": item.parent and ContentItemReference(type=humps.camelize(item.parent.item_type), id=item.parent.doknr),
    }

    if model_type in (Article, HeadingArticle):
        attrs["body"] = item.body
        attrs["footnotes"] = item.footnotes
        attrs["documentaryFootnotes"] = item.documentary_footnotes

    return model_type(**attrs)


class PublicationInfoItem(pydantic.BaseModel):
    reference: str
    periodical: str


class StatusInfoItem(pydantic.BaseModel):
    comment: str
    category: str


class Law(pydantic.BaseModel):
    type: str = "law"
    id: str
    abbreviation: str
    extraAbbreviations: List[str]
    firstPublished: str
    sourceTimestamp: str
    titleShort: Optional[str]
    titleLong: str
    publicationInfo: List[PublicationInfoItem]
    statusInfo: List[StatusInfoItem]
    notes: TextContent
    attachments: dict
    contents: List[Union[Article, Heading, HeadingArticle]]

    @classmethod
    def from_law(cls, law):
        attachments = {
            name: f"{PUBLIC_ASSET_ROOT}/gesetze_im_internet/{law.gii_slug}/{name}"
            for name in law.attachment_names
        }

        notes = {
            "body": law.notes_body,
            "footnotes": law.notes_footnotes,
            "documentaryFootnotes": law.notes_documentary_footnotes
        }

        return cls(
            id=law.doknr,
            abbreviation=law.abbreviation,
            extraAbbreviations=law.extra_abbreviations,
            firstPublished=law.first_published,
            sourceTimestamp=law.source_timestamp,
            titleShort=law.title_short,
            titleLong=law.title_long,
            publicationInfo=pydantic.parse_obj_as(List[PublicationInfoItem], law.publication_info),
            statusInfo=pydantic.parse_obj_as(List[StatusInfoItem], law.status_info),
            notes=notes,
            attachments=attachments,
            contents=[content_item_from_db_model(ci) for ci in law.contents],
        )


class LawResponse(pydantic.BaseModel):
    data: Law

    @classmethod
    def from_law(cls, law):
        return cls(data=Law.from_law(law))


ITEM_TYPE_TO_MODEL_TYPE = {
    "article": Article,
    "heading": Heading,
    "heading_article": HeadingArticle,
}
