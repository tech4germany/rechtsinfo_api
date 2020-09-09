import json
from typing import List, Optional, Dict

import humps
import pydantic


class BaseModel(pydantic.BaseModel):
    @property
    def type_(self):
        return ''.join((self.__class__.__name__[0].lower(), self.__class__.__name__[1:]))


class ContentItem(BaseModel):
    id: str
    name: str
    title: Optional[str]
    content_level: Optional[int]  # not actually optional, but not known at object creation time
    parent: Optional['ContentItem']

    def to_api_dict(self):
        return {
            'type': self.type_,
            'parent': self.parent and { 'type': self.parent.type_, 'id': self.parent.id },
            **{ key: getattr(self, key) for key in self.dict() if key != 'parent'}
        }
ContentItem.update_forward_refs()

class Heading(ContentItem):
    pass


class Article(ContentItem):
    body: Optional[Dict]
    documentary_footnotes: Optional[str]


class HeadingArticle(Heading, Article):
    pass


class Law(BaseModel):
    id: str
    abbreviation: str
    extra_abbreviations: List[str]
    first_published: str
    source_timestamp: str
    heading_long: str
    heading_short: Optional[str]
    publication_info: Optional[List[Dict]]
    status_info: Optional[List[Dict]]
    notes: Dict
    contents: List[ContentItem]

    def to_api_dict(self):
        return {
            'type': self.type_,
            **{ key: getattr(self, key) for key in self.dict() if key != 'contents' },
            'contents': [content_item.to_api_dict() for content_item in self.contents]
        }


    def to_api_json(self):
        return json.dumps(humps.camelize({'data': self.to_api_dict()}))

