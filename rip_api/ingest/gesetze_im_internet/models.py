import json
from typing import List, Optional, Dict

import humps
from pydantic import BaseModel


class Law(BaseModel):
    id: str
    juris_abbrs: List[str]
    official_abbr: Optional[str]
    first_published: str
    source_timestamp: str
    heading_long: str
    heading_short: Optional[str]
    publication_info: Optional[List[Dict]]
    status_info: Optional[List[Dict]]
    prelude: Dict
    content: List

    def to_api_dict(self):
        attributes = {
            key: getattr(self, key) for key in self.dict()
            if key not in ('type', 'id', 'content')
        }

        return {
            'type': 'law',
            'id': self.id,
            'attributes': attributes,
            'content': [content_item.to_api_dict() for content_item in self.content]
        }


    def to_api_json(self):
        return json.dumps(humps.camelize(self.to_api_dict()))


class ContentItem(BaseModel):
    id: str
    name: str
    title: Optional[str]

    def to_api_dict(self):
        data = {
            'type': ''.join([self.__class__.__name__[0].lower(), self.__class__.__name__[1:]]),
            'id': self.id,
            'attributes': {
                key: getattr(self, key) for key in self.dict()
                if key not in ('type', 'id', 'children')
            }
        }

        if hasattr(self, 'children'):
            data['children'] = [child.to_api_dict() for child in self.children]
        return data


class Heading(ContentItem):
    heading_level: Optional[int]  # not actually optional, but not known at object creation time
    children: List[ContentItem]


class Article(ContentItem):
    body: Optional[Dict]
    footnotes: Optional[str]


class HeadingArticle(Heading, Article):
    pass
