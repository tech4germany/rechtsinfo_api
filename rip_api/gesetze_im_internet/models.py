import json
from typing import List, Optional, Dict

import humps
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Law(Base):
    __tablename__ = 'laws'

    id = Column(Integer, primary_key=True)
    doknr = Column(String, nullable=False)
    abbreviation = Column(String, nullable=False)
    extra_abbreviations = Column(postgresql.ARRAY(String), nullable=False)
    first_published = Column(String, nullable=False)
    source_timestamp = Column(String, nullable=False)
    heading_long = Column(String, nullable=False)
    heading_short = Column(String)
    publication_info = Column(postgresql.JSONB, nullable=False)
    status_info = Column(postgresql.JSONB, nullable=False)
    notes = Column(postgresql.JSONB)

    contents = relationship('ContentItem', back_populates='law', order_by='ContentItem.order',
                            cascade='all, delete, delete-orphan')


class ContentItem(Base):
    __tablename__ = 'content_items'

    id = Column(Integer, primary_key=True)
    doknr = Column(String, nullable=False)
    item_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    title = Column(String)
    body = Column(postgresql.JSONB)
    documentary_footnotes = Column(String)
    content_level = Column(Integer, nullable=False)
    law_id = Column(Integer, ForeignKey('laws.id'))
    parent_id = Column(Integer, ForeignKey('content_items.id'))
    order = Column(Integer, nullable=False)

    law = relationship('Law', back_populates='contents')
    parent = relationship('ContentItem', uselist=False)


def law_to_api_json(law, pretty=False):
    json_kwargs = {}
    if pretty:
        json_kwargs = {'indent': 2}

    law_dict = {
        'data': {
            'type': 'law',
            'id': law.doknr,
            'abbreviation': law.abbreviation,
            'extraAbbreviations': law.extra_abbreviations,
            'firstPublished': law.first_published,
            'sourceTimestamp': law.source_timestamp,
            'headingShort': law.heading_short,
            'headingLong': law.heading_long,
            'publicationInfo': law.publication_info,
            'statusInfo': law.status_info,
            'notes': humps.camelize(law.notes),
            'contents': []
        }
    }

    for item in law.contents:
        item_dict = {
            'id': item.doknr,
            'type': humps.camelize(item.item_type),
            'name': item.name,
            'title': item.title
        }

        if item.item_type in ('article', 'heading_article'):
            item_dict.update({
                'body': item.body,
                'documentaryFootnotes': item.documentary_footnotes
            })

        item_dict.update({
            'contentLevel': item.content_level,
            'parent': item.parent and { 'type': humps.camelize(item.parent.item_type), 'id': item.parent.doknr }
        })

        law_dict['data']['contents'].append(item_dict)

    return json.dumps(law_dict, **json_kwargs)
