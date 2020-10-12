from typing import List, Optional, Union

import humps
import pydantic

from . import PUBLIC_ASSET_ROOT, urls


class ContentItemBasicFields(pydantic.BaseModel):
    type: str
    id: str
    url: str
    name: str
    title: Optional[str]

    @classmethod
    def _attrs_dict_from_item(cls, item):
        return {
            "id": item.doknr,
            "url": urls.get_article(item.law.slug, item.doknr),
            "name": item.name,
            "title": item.title,
        }

    @staticmethod
    def model_class_from_item_type(item_type):
        return {
            "article": ArticleBasicFields,
            "heading": HeadingBasicFields,
            "heading_article": HeadingArticleBasicFields,
        }[item_type]

    @classmethod
    def from_orm_model(cls, item):
        model_type = cls.model_class_from_item_type(item.item_type)
        attrs = cls._attrs_dict_from_item(item)
        return model_type(**attrs)


class ContentItemAllFields(ContentItemBasicFields):
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

    @staticmethod
    def model_class_from_item_type(item_type):
        return {
            "article": ArticleAllFields,
            "heading": HeadingAllFields,
            "heading_article": HeadingArticleAllFields,
        }[item_type]

    @classmethod
    def _attrs_dict_from_item(cls, item):
        attrs = super()._attrs_dict_from_item(item)
        attrs["parent"] = item.parent and {
            "type": humps.camelize(item.parent.item_type),
            "id": item.parent.doknr
        }

        if item.item_type in ('article', 'heading_article'):
            attrs["body"] = item.body

        attrs["footnotes"] = item.footnotes
        attrs["documentaryFootnotes"] = item.documentary_footnotes

        return attrs


class ContentItemWithBodyAndFootnotes(ContentItemAllFields):
    body: Optional[str] = ...
    footnotes: Optional[str] = ...
    documentaryFootnotes: Optional[str] = ...


class ContentItemWithFootnotes(ContentItemAllFields):
    footnotes: Optional[str] = ...
    documentaryFootnotes: Optional[str] = ...


class LawBasicFields(pydantic.BaseModel):
    type: str = "law"
    id: str
    url: str
    firstPublished: str
    sourceTimestamp: str
    titleShort: Optional[str]
    titleLong: str
    abbreviation: str
    slug: str

    @classmethod
    def _attrs_dict_from_law(cls, law):
        return dict(
            id=law.doknr,
            url=urls.get_law(law.slug),
            abbreviation=law.abbreviation,
            slug=law.slug,
            firstPublished=law.first_published,
            sourceTimestamp=law.source_timestamp,
            titleShort=law.title_short,
            titleLong=law.title_long
        )

    @classmethod
    def from_orm_model(cls, law):
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


class ContentItemBasicFieldsWithLaw(ContentItemBasicFields):
    law: LawBasicFields

    @staticmethod
    def model_class_from_item_type(item_type):
        return {
            "article": ArticleBasicFieldsWithLaw,
            "heading": HeadingBasicFieldsWithLaw,
            "heading_article": HeadingArticleBasicFieldsWithLaw,
        }[item_type]

    @classmethod
    def _attrs_dict_from_item(cls, item):
        return {
            **super()._attrs_dict_from_item(item),
            "law": LawBasicFields.from_orm_model(item.law)
        }


class HeadingBasicFields(ContentItemBasicFields):
    type: str = "heading"


class HeadingBasicFieldsWithLaw(ContentItemBasicFieldsWithLaw):
    type: str = "heading"


class HeadingAllFields(ContentItemWithFootnotes):
    type: str = "heading"


class ArticleBasicFields(ContentItemBasicFields):
    type: str = "article"


class ArticleBasicFieldsWithLaw(ContentItemBasicFieldsWithLaw):
    type: str = "article"


class ArticleAllFields(ContentItemWithBodyAndFootnotes):
    type: str = "article"


class HeadingArticleBasicFields(ContentItemBasicFields):
    type: str = "headingArticle"


class HeadingArticleBasicFieldsWithLaw(ContentItemBasicFieldsWithLaw):
    type: str = "headingArticle"


class HeadingArticleAllFields(ContentItemWithBodyAndFootnotes):
    type: str = "headingArticle"


class LawAllFieldsWithContents(LawAllFields):
    # Ordering in the Union matters, cf. LawResponse.
    contents: List[Union[ArticleAllFields, HeadingAllFields, HeadingArticleAllFields]]

    @classmethod
    def _attrs_dict_from_law(cls, law):
        attrs = super()._attrs_dict_from_law(law)
        attrs["contents"] = [ContentItemAllFields.from_orm_model(ci) for ci in law.contents]
        return attrs


class LawResponse(pydantic.BaseModel):
    # LawWithContents must come first in the Union: FastAPI tries them in order and only skips
    # types if there's a validation error.
    data: Union[LawAllFieldsWithContents, LawAllFields]

    @classmethod
    def from_orm_model(cls, law):
        return cls(data=LawAllFields.from_orm_model(law))


class PaginationLinks(pydantic.BaseModel):
    prev: Optional[str]
    next: Optional[str]


class Pagination(pydantic.BaseModel):
    total: int
    page: int
    per_page: int


class LawsResponse(pydantic.BaseModel):
    data: list
    links: PaginationLinks
    pagination: Pagination


class ContentItemResponse(pydantic.BaseModel):
    data: Union[LawAllFields, ArticleAllFields, HeadingArticleAllFields]


class SearchResultsResponse(pydantic.BaseModel):
    data: List[Union[
        LawBasicFields,
        ArticleBasicFieldsWithLaw, ArticleBasicFields,
        HeadingArticleBasicFieldsWithLaw, HeadingArticleBasicFields
    ]]
    links: PaginationLinks
    pagination: Pagination
