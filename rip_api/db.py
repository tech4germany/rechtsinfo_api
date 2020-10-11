from contextlib import contextmanager
import dataclasses
import math
import os
import re
import typing

from sqlalchemy import create_engine, func, literal, text
from sqlalchemy.orm import joinedload, load_only, sessionmaker

from .models import slugify, Base, Law, ContentItem

# There's big variety in how paragraph names are formatted. This rule captures 88% of them as of 2020-10-01.
ARTICLE_NUM_REGEX = re.compile(
    # Optional article identifier, optionally followed by a space,
    r'((§|art|artikel|nr) ?)?'
    # and:
    # 1) bare numbers ("13"),
    # 2) roman numerals below 50 ("XIV"),
    # 3) 1/2 may be followed by 1 or 2 letters ("224b", "13mb")
    # 4) 1/2/3 may be followed by a single dot ("3.", "IX.", "7c.")
    # 5) two groups of 1/2/3 may be joined by a single dot in the middle ("12.31", "4a.03")
    r'(?P<article_num>([\dIVX]+\w{0,2}\.?){1,2})',
    re.IGNORECASE
)

db_uri = os.environ.get("DB_URI") or "postgresql://localhost:5432/rip_api"
_engine = create_engine(db_uri)
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


class QueryItemProvider:
    def __init__(self, query):
        self.query = query

    @property
    def total(self):
        return self.query.count()

    def items(self, offset, limit):
        return self.query.offset(offset).limit(limit).all()


@dataclasses.dataclass
class Pagination:
    page: int
    per_page: int
    total: int
    prev_page: typing.Optional[int]
    next_page: typing.Optional[int]
    items: list


def paginate(item_provider, page, per_page, prepend_item=None):
    if page < 1:
        raise ValueError(f"page must be >= 1, got {page}")
    if per_page < 1:
        raise ValueError(f"per_page must be >= 1, got {per_page}")

    total = item_provider.total
    total_pages = math.ceil(total / per_page)

    prev_page = min(page - 1, total_pages)
    prev_page = None if prev_page == 0 else prev_page
    next_page = None if page + 1 > total_pages else page + 1

    offset = (page - 1) * per_page
    items = item_provider.items(offset, per_page)

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
    item_provider = QueryItemProvider(session.query(Law))
    return paginate(item_provider, page, per_page)


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


def _find_law_exact_match(session, query):
    return session.query(Law).filter(Law.slug == slugify(query)).first()


def _find_article_num_exact_match(session, query):
    law = None
    for token in query.split(" "):
        law = _find_law_exact_match(session, token)
        if law:
            break
    if not law:
        return None

    article_num_match = ARTICLE_NUM_REGEX.search(query)
    if article_num_match:
        article_num = article_num_match.groupdict()["article_num"]
        return _search_content_items_by_number(session, law.id, article_num)

    return None


def _search_content_items_by_number(session, law_id, article_num):
    return (
        session.query(ContentItem)
        .filter(ContentItem.law_id == law_id)
        .filter(ContentItem.item_type == 'article')
        .filter(ContentItem.name.endswith(' ' + article_num))  # Add space to avoid partial num matches.
        .first()
    )


def _full_text_search_query(session, model, tsquery):
    normalisation = 2  # TODO tweak
    rank = func.ts_rank_cd(model.search_tsv, tsquery, normalisation)
    fields = [
        literal(model.__table__.name[:-1]).label("type"),
        model.id.label("id"),
        rank.label("rank")
    ]
    return session.query(*fields).filter(model.search_tsv.op('@@')(tsquery))


def _find_exact_hit(session, query, filter_type):
    if filter_type == "laws":
        return _find_law_exact_match(session, query)
    elif filter_type == "articles":
        return _find_article_num_exact_match(session, query)
    else:
        return (
            _find_law_exact_match(session, query)
            or _find_article_num_exact_match(session, query)
        )


def _exact_hit_to_search_result_query(session, instance):
    fields = [
        literal(instance.__table__.name[:-1]).label("type"),
        literal(instance.id).label("id"),
        literal(10000).label("rank")
    ]
    return session.query(*fields)


def _map_search_results_to_models(session, items):
    # Collect ids.
    item_ids = {'law': [], 'content_item': []}
    for item_type, item_id, _ in items:
        item_ids[item_type].append(item_id)

    # Bulk load and map models.
    mapped = {'law': {}, 'content_item': {}}
    for law in session.query(Law).filter(Law.id.in_(item_ids['law'])):
        mapped['law'][law.id] = law
    for content_item in session.query(ContentItem).filter(ContentItem.id.in_(item_ids['content_item'])):
        mapped['content_item'][content_item.id] = content_item

    # Build list in original order.
    return [mapped[item_type][item_id] for item_type, item_id, _ in items]


def fulltext_search_laws_content_items(session, query, page, per_page, filter_type):
    exact_hit = _find_exact_hit(session, query, filter_type)

    tsquery = func.websearch_to_tsquery("german", query)

    law_query = _full_text_search_query(session, Law, tsquery)
    content_items_query = (
        _full_text_search_query(session, ContentItem, tsquery)
        .filter(ContentItem.item_type.in_(['article', 'heading_article']))
    )

    if filter_type == "laws":
        query = law_query
    elif filter_type == "articles":
        query = content_items_query
    else:
        query = law_query.union(content_items_query)

    if exact_hit:
        query = _exact_hit_to_search_result_query(session, exact_hit).union(query)

    query = query.order_by(text("rank desc"))

    pagination = paginate(QueryItemProvider(query), page, per_page)
    pagination.items = _map_search_results_to_models(session, pagination.items)

    return pagination
