"""Add full text search

Revision ID: 6a36ec2b5509
Revises: b379bf626e54
Create Date: 2020-10-02 12:03:31.158624

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6a36ec2b5509'
down_revision = 'b379bf626e54'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('content_items', sa.Column('search_tsv', postgresql.TSVECTOR(), sa.Computed("""
        setweight(to_tsvector('german',
            coalesce(content_items.name, '') ||
            coalesce(content_items.title, '')),
        'A') ||
        setweight(to_tsvector('german',
            coalesce(content_items.body, '')),
        'B')
    """), nullable=True))
    op.add_column('laws', sa.Column('search_tsv', postgresql.TSVECTOR(), sa.Computed("""
        setweight(to_tsvector('german',
            coalesce(laws.title_long, '') ||
            coalesce(laws.title_short, '') ||
            coalesce(laws.abbreviation, '')),
        'A') ||
        setweight(to_tsvector('german',
            coalesce(laws.notes_body, '')),
        'B')
    """), nullable=True))
    op.create_index('ix_content_items_search_tsv', 'content_items', ['search_tsv'], unique=False, postgresql_using='gin')
    op.create_index('ix_laws_search_tsv', 'laws', ['search_tsv'], unique=False, postgresql_using='gin')


def downgrade():
    op.drop_index('ix_laws_search_tsv', table_name='laws')
    op.drop_column('laws', 'search_tsv')
    op.drop_index('ix_content_items_search_tsv', table_name='content_items')
    op.drop_column('content_items', 'search_tsv')
