"""empty message

Revision ID: f3e106248c60
Revises: ca1ec74dc367
Create Date: 2018-05-04 09:01:38.555919

"""
from alembic import op
import sqlalchemy as sa
import os


import json
from unittest import mock
from jsonschema import Draft4Validator
from directorofme.authorization import groups
from directorofme_event.models import EventType

# revision identifiers, used by Alembic.
revision = 'f3e106248c60'
down_revision = 'ca1ec74dc367'
branch_labels = None
depends_on = None

def default_perms(*args):
    return tuple()

@mock.patch.object(EventType, "default_perms", default_perms)
def upgrade():
    schema = None
    with open(os.path.join(os.path.dirname(__file__), "../../json/schemas/daily-standup-report.json")) as f:
        schema = json.load(f)
    Draft4Validator.check_schema(schema)

    session = sa.orm.session.Session(bind=op.get_bind())
    with EventType.disable_permissions():
        session.add(EventType(
            name="Daily Stand-Up Report",
            desc="""Start your day off with all the information you need. The Daily Stand-Up report is
                    delivered to you each morning via E-Mail or Chat and has all the information you
                    need to have your best day every day.
                 """,
            data_schema=schema,
            read=(groups.everybody.name,),
            write=(groups.admin.name,),
        ))
        session.commit()

def downgrade():
    session = sa.orm.session.Session(bind=op.get_bind())
    with EventType.disable_permissions():
        session.delete(EventType.query.filter(EventType.slug == "daily-stand-up-report").first())
        session.commit()
