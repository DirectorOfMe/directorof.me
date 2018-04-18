"""empty message

Revision ID: 2ff0ef4fc4ef
Revises: 
Create Date: 2018-04-18 01:44:40.701239

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2ff0ef4fc4ef'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('directorofme_event_event_type',
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.Column('_permissions_read_0', sa.String(length=20), nullable=True),
    sa.Column('_permissions_read_1', sa.String(length=20), nullable=True),
    sa.Column('_permissions_write_0', sa.String(length=20), nullable=True),
    sa.Column('_permissions_write_1', sa.String(length=20), nullable=True),
    sa.Column('_permissions_delete_0', sa.String(length=20), nullable=True),
    sa.Column('_permissions_delete_1', sa.String(length=20), nullable=True),
    sa.Column('id', sa.dialects.postgresql.UUID(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('slug', sa.String(length=50), nullable=False),
    sa.Column('desc', sa.String(length=255), nullable=False),
    sa.Column('data_schema', sa.dialects.postgresql.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_directorofme_event_event_type__permissions_delete_0'), 'directorofme_event_event_type', ['_permissions_delete_0'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event_type__permissions_delete_1'), 'directorofme_event_event_type', ['_permissions_delete_1'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event_type__permissions_read_0'), 'directorofme_event_event_type', ['_permissions_read_0'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event_type__permissions_read_1'), 'directorofme_event_event_type', ['_permissions_read_1'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event_type__permissions_write_0'), 'directorofme_event_event_type', ['_permissions_write_0'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event_type__permissions_write_1'), 'directorofme_event_event_type', ['_permissions_write_1'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event_type_slug'), 'directorofme_event_event_type', ['slug'], unique=True)
    op.create_table('directorofme_event_event',
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.Column('_permissions_read_0', sa.String(length=20), nullable=True),
    sa.Column('_permissions_read_1', sa.String(length=20), nullable=True),
    sa.Column('_permissions_write_0', sa.String(length=20), nullable=True),
    sa.Column('_permissions_write_1', sa.String(length=20), nullable=True),
    sa.Column('_permissions_delete_0', sa.String(length=20), nullable=True),
    sa.Column('_permissions_delete_1', sa.String(length=20), nullable=True),
    sa.Column('id', sa.dialects.postgresql.UUID(), nullable=False),
    sa.Column('event_type_id', sa.dialects.postgresql.UUID(), nullable=False),
    sa.Column('event_time', sa.DateTime(), nullable=False),
    sa.Column('data', sa.dialects.postgresql.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['event_type_id'], ['directorofme_event_event_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_directorofme_event_event__permissions_delete_0'), 'directorofme_event_event', ['_permissions_delete_0'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event__permissions_delete_1'), 'directorofme_event_event', ['_permissions_delete_1'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event__permissions_read_0'), 'directorofme_event_event', ['_permissions_read_0'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event__permissions_read_1'), 'directorofme_event_event', ['_permissions_read_1'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event__permissions_write_0'), 'directorofme_event_event', ['_permissions_write_0'], unique=False)
    op.create_index(op.f('ix_directorofme_event_event__permissions_write_1'), 'directorofme_event_event', ['_permissions_write_1'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_directorofme_event_event__permissions_write_1'), table_name='directorofme_event_event')
    op.drop_index(op.f('ix_directorofme_event_event__permissions_write_0'), table_name='directorofme_event_event')
    op.drop_index(op.f('ix_directorofme_event_event__permissions_read_1'), table_name='directorofme_event_event')
    op.drop_index(op.f('ix_directorofme_event_event__permissions_read_0'), table_name='directorofme_event_event')
    op.drop_index(op.f('ix_directorofme_event_event__permissions_delete_1'), table_name='directorofme_event_event')
    op.drop_index(op.f('ix_directorofme_event_event__permissions_delete_0'), table_name='directorofme_event_event')
    op.drop_table('directorofme_event_event')
    op.drop_index(op.f('ix_directorofme_event_event_type_slug'), table_name='directorofme_event_event_type')
    op.drop_index(op.f('ix_directorofme_event_event_type__permissions_write_1'), table_name='directorofme_event_event_type')
    op.drop_index(op.f('ix_directorofme_event_event_type__permissions_write_0'), table_name='directorofme_event_event_type')
    op.drop_index(op.f('ix_directorofme_event_event_type__permissions_read_1'), table_name='directorofme_event_event_type')
    op.drop_index(op.f('ix_directorofme_event_event_type__permissions_read_0'), table_name='directorofme_event_event_type')
    op.drop_index(op.f('ix_directorofme_event_event_type__permissions_delete_1'), table_name='directorofme_event_event_type')
    op.drop_index(op.f('ix_directorofme_event_event_type__permissions_delete_0'), table_name='directorofme_event_event_type')
    op.drop_table('directorofme_event_event_type')
    # ### end Alembic commands ###
