from contextlib import contextmanager
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import load_only, sessionmaker

from .models import Base, Law

_engine = create_engine(os.environ.get("DB_URI") or "postgresql://localhost:5432/rip_api")
Session = sessionmaker(bind=_engine)
Base.metadata.create_all(_engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def all_gii_slugs(session):
    return session.query(Law.gii_slug).all()


def all_laws_load_only_gii_slug_and_source_timestamp(session):
    return session.query(Law).options(load_only("gii_slug", "source_timestamp")).all()


def find_law_by_doknr(session, doknr):
    return session.query(Law).filter_by(doknr=doknr).first()


def find_law_by_slug(session, slug):
    return session.query(Law).filter_by(slug=slug).first()
