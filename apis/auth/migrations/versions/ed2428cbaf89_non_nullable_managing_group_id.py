"""empty message

Revision ID: ed2428cbaf89
Revises: 879e94e29655
Create Date: 2018-02-06 22:22:54.529120

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed2428cbaf89'
down_revision = '879e94e29655'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('license', 'managing_group_id',
               existing_type=sa.dialects.postgresql.UUID(),
               nullable=False)


def downgrade():
    op.alter_column('license', 'managing_group_id',
               existing_type=sa.dialects.postgresql.UUID(),
               nullable=True)
