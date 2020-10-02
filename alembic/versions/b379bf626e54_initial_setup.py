"""Initial setup

Revision ID: b379bf626e54
Revises:
Create Date: 2020-10-02 10:02:32.193510

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b379bf626e54'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('laws',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doknr', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('gii_slug', sa.String(), nullable=False),
        sa.Column('abbreviation', sa.String(), nullable=False),
        sa.Column('extra_abbreviations', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('first_published', sa.String(), nullable=False),
        sa.Column('source_timestamp', sa.String(), nullable=False),
        sa.Column('title_long', sa.String(), nullable=False),
        sa.Column('title_short', sa.String(), nullable=True),
        sa.Column('publication_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('notes_body', sa.String(), nullable=True),
        sa.Column('notes_footnotes', sa.String(), nullable=True),
        sa.Column('notes_documentary_footnotes', sa.String(), nullable=True),
        sa.Column('attachment_names', postgresql.ARRAY(sa.String()), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doknr')
    )
    op.create_index(op.f('ix_laws_gii_slug'), 'laws', ['gii_slug'], unique=False)
    op.create_index(op.f('ix_laws_slug'), 'laws', ['slug'], unique=False)
    op.create_table('content_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doknr', sa.String(), nullable=False),
        sa.Column('item_type', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('body', sa.String(), nullable=True),
        sa.Column('footnotes', sa.String(), nullable=True),
        sa.Column('documentary_footnotes', sa.String(), nullable=True),
        sa.Column('law_id', sa.Integer(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['law_id'], ['laws.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['content_items.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doknr')
    )
    op.create_index(op.f('ix_content_items_law_id'), 'content_items', ['law_id'], unique=False)


def downgrade():
    op.drop_table('content_items')
    op.drop_table('laws')
