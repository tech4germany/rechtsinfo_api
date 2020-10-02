from contextlib import contextmanager
import dataclasses
import math
import os
import typing

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import joinedload, load_only, sessionmaker

from .models import Base, Law, ContentItem

_engine = create_engine(
    os.environ.get("DB_URI") or "postgresql://localhost:5432/rip_api"
)
Session = sessionmaker(bind=_engine)


def init_db():
    Base.metadata.create_all(_engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:  # noqa
        session.rollback()
        raise
    finally:
        session.close()


@dataclasses.dataclass
class Pagination:
    page: int
    per_page: int
    total: int
    prev_page: typing.Optional[int]
    next_page: typing.Optional[int]
    items: list


def paginate(query, page, per_page):
    if page < 1:
        raise ValueError(f"page must be >= 1, got {page}")
    if per_page < 1:
        raise ValueError(f"per_page must be >= 1, got {per_page}")

    total = query.count()
    total_pages = math.ceil(total / per_page)

    prev_page = min(page - 1, total_pages)
    prev_page = None if prev_page == 0 else prev_page
    next_page = None if page + 1 > total_pages else page + 1

    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    return Pagination(
        page=page,
        per_page=per_page,
        total=total,
        prev_page=prev_page,
        next_page=next_page,
        items=items
    )


def all_laws(session):
    return session.query(Law).all()


def all_laws_paginated(session, page, per_page):
    return paginate(session.query(Law), page, per_page)


def all_gii_slugs(session):
    return session.query(Law.gii_slug).all()


def all_laws_load_only_gii_slug_and_source_timestamp(session):
    return session.query(Law).options(load_only("gii_slug", "source_timestamp")).all()


def find_law_by_doknr(session, doknr):
    return session.query(Law).filter_by(doknr=doknr).first()


def find_law_by_slug(session, slug):
    return session.query(Law).filter_by(slug=slug).first()


def find_content_item_by_id_and_law_slug(session, content_item_id, law_slug):
    return (
        session.query(ContentItem)
        .options(joinedload(ContentItem.law), joinedload(ContentItem.parent).load_only("doknr", "item_type"))
        .filter(ContentItem.doknr == content_item_id, Law.slug == law_slug)
        .first()
    )


def bulk_delete_laws_by_gii_slug(session, gii_slugs):
    Law.__table__.delete().where(Law.gii_slug.in_(gii_slugs))


def _full_text_search_query(session, model, tsquery):
    rank = func.ts_rank_cd(model.search_tsv, tsquery).label("rank")
    return (
        session.query(model, rank)
        .filter(model.search_tsv.op('@@')(tsquery))
        .order_by(text("rank desc"))
    )


def fulltext_search_laws_content_items(session, query, offset=0, limit=10):
    tsquery = func.websearch_to_tsquery("german", query)
    laws = _full_text_search_query(session, Law, tsquery).limit(limit).all()
    content_items = _full_text_search_query(session, ContentItem, tsquery).limit(limit).all()
    combined = laws + content_items
    combined.sort(key=lambda it: it[1], reverse=True)

    return combined[:limit]
