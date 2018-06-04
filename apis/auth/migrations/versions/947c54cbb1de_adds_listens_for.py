"""empty message

Revision ID: 947c54cbb1de
Revises: e145c5343ca4
Create Date: 2018-06-04 04:02:57.778637

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '947c54cbb1de'
down_revision = 'e145c5343ca4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('directorofme_auth_app', sa.Column('listens_for', sa.ARRAY(sa.String()), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('directorofme_auth_app', 'listens_for')
    # ### end Alembic commands ###