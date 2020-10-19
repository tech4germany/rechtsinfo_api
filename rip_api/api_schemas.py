from typing import List, Union

import humps
from pydantic import BaseModel, Field, validator

from . import PUBLIC_ASSET_ROOT, urls


class ContentItemBasicFields(BaseModel):
    type: str
    id: str = Field(..., description="Unique ID")
    url: str = Field(..., description="Resource link")
    name: str = Field(..., description="Item name, e.g. paragraph number or section")
    title: str = Field(None, description="Section or article title")

    @classmethod
    def _attrs_dict_from_item(cls, item):
        return {
            "id": item.doknr,
            "type": humps.camelize(item.item_type),
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


class ContentItemReference(BaseModel):
    type: str = Field(..., description="Type of containing heading (\"heading\" or \"headingArticle\")")
    id: str = Field(..., description="ID of containing heading")


class ContentItemAllFields(ContentItemBasicFields):
    parent: ContentItemReference = Field(None, description="Containing heading (see Note on hierarchical sections)")

    @validator("type", allow_reuse=True, check_fields=False)
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


class HasBody(BaseModel):
    body: str = Field(None, description="Body text (see Note on text contents)")


class HasFootnotes(BaseModel):
    footnotes: str = Field(None, description="Official footnotes (see Note on text contents)")
    documentaryFootnotes: str = Field(None, description="Editorial footnotes")


class TextContent(HasFootnotes, HasBody):
    pass


class ContentItemWithBodyAndFootnotes(TextContent, ContentItemAllFields):
    pass


class ContentItemWithFootnotes(HasFootnotes, ContentItemAllFields):
    pass


class LawBasicFields(BaseModel):
    """
    **Law** (basic fields)
    """

    type: str = "law"
    id: str = Field(..., description="Unique ID")
    url: str = Field(..., description="Resource link")
    firstPublished: str = Field(..., description="Initial publication date")
    sourceTimestamp: str = Field(..., description="Modification time on gesetze-im-internet.de")
    titleShort: str = Field(None, description="Title of the law (shortened)")
    titleLong: str = Field(..., description="Title of the law")
    abbreviation: str = Field(..., description="Abbreviated title")
    slug: str = Field(..., description="URL-safe lowercased abbreviation")

    @classmethod
    def _attrs_dict_from_law(cls, law):
        return dict(
            id=law.doknr,
            type="law",
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


class ContentItemBasicFieldsWithLaw(ContentItemBasicFields):
    law: LawBasicFields = Field(..., description="Law (basic fields)")

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
    """
    **Heading** (basic fields)
    """
    type: str = "heading"


class HeadingBasicFieldsWithLaw(ContentItemBasicFieldsWithLaw):
    """
    **Heading** (basic fields and law)
    """
    type: str = "heading"


class HeadingAllFields(ContentItemWithFootnotes):
    """
    **Heading** (all fields)
    """
    type: str = "heading"


class ArticleBasicFields(ContentItemBasicFields):
    """
    **Article** (basic fields)
    """
    type: str = "article"


class ArticleBasicFieldsWithLaw(ContentItemBasicFieldsWithLaw):
    """
    **Article** (basic fields and law)
    """
    type: str = "article"


class ArticleAllFields(ContentItemWithBodyAndFootnotes):
    """
    **Article** (all fields)
    """
    type: str = "article"


class HeadingArticleBasicFields(ContentItemBasicFields):
    """
    **HeadingArticle** (basic fields)
    """
    type: str = "headingArticle"


class HeadingArticleBasicFieldsWithLaw(ContentItemBasicFieldsWithLaw):
    """
    **HeadingArticle** (basic fields and law)
    """
    type: str = "headingArticle"


class HeadingArticleAllFields(ContentItemWithBodyAndFootnotes):
    """
    **HeadingArticle** (all fields)
    """
    type: str = "headingArticle"


class PublicationInfoItem(BaseModel):
    reference: str = Field(..., description="e.g. year, issue no., page")
    periodical: str = Field(..., description="Name of publication")


class StatusInfoItem(BaseModel):
    comment: str = Field(..., description="Free-text status information")
    category: str = Field(..., description='Any of "Aufh", "Stand", "Hinweis", "Neuf", "Sonst"')


class LawAllFields(LawBasicFields):
    """
    **Law** (all fields)
    """
    extraAbbreviations: List[str] = Field(..., description="Additional abbreviations")
    publicationInfo: List[PublicationInfoItem] = Field(..., description="Publication information")
    statusInfo: List[StatusInfoItem] = Field(..., description="Status information")
    notes: TextContent
    attachments: dict = Field(..., description="See Note on attachments")
    # Order in the Union matters: FastAPI tries one after the other and only skips types if there's a validation error.
    contents: List[Union[
        ArticleAllFields, HeadingAllFields, HeadingArticleAllFields
    ]] = Field(None, description="Contents of the law (articles, section headings)")

    @classmethod
    def _attrs_dict_from_law(cls, law, include_contents=False):
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

        if include_contents:
            attrs["contents"] = [ContentItemAllFields.from_orm_model(ci) for ci in law.contents]

        return attrs

    @classmethod
    def from_orm_model(cls, law, include_contents=False):
        return cls(**cls._attrs_dict_from_law(law, include_contents=include_contents))


class LawResponse(BaseModel):
    data: LawAllFields = Field(..., description="The requested data")

    @classmethod
    def from_orm_model(cls, law):
        return cls(data=LawAllFields.from_orm_model(law))


class PaginationLinks(BaseModel):
    """
    Pagination links
    """
    prev: str = Field(None, description="Link to previous result page")
    next: str = Field(None, description="Link to following result page")


class Pagination(BaseModel):
    """
    Pagination information
    """
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Result page number")
    per_page: int = Field(..., description="Number of items per page")


class LawsResponse(BaseModel):
    data: List[Union[LawAllFields, LawBasicFields]] = Field(..., description="The requested data")
    links: PaginationLinks
    pagination: Pagination


class ContentItemResponse(BaseModel):
    # Order in the Union matters: FastAPI tries one after the other and only skips types if there's a validation error.
    data: Union[ArticleAllFields, HeadingArticleAllFields, HeadingAllFields] = Field(..., description="The requested data")


class SearchResultsResponse(BaseModel):
    # Order in the Union matters: FastAPI tries one after the other and only skips types if there's a validation error.
    data: List[Union[
        LawBasicFields,
        ArticleBasicFieldsWithLaw, ArticleBasicFields,
        HeadingArticleBasicFieldsWithLaw, HeadingArticleBasicFields
    ]] = Field(..., description="The requested data")
    links: PaginationLinks
    pagination: Pagination
