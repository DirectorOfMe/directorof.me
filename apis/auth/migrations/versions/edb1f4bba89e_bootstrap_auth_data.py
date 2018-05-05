"""empty message

Revision ID: edb1f4bba89e
Revises: 7705ff00b511
Create Date: 2018-01-30 21:57:11.153630

"""
from alembic import op
import sqlalchemy as sa

import os
import json
import jsonschema

# revision identifiers, used by Alembic.
revision = 'edb1f4bba89e'
down_revision = '8c0968acb34f'
branch_labels = None
depends_on = None

from slugify import slugify

from directorofme.authorization.groups import base_groups, admin, staff, everybody, Scope, user
from unittest import mock
from directorofme_auth.models import Group, GroupTypes, License, Profile, App, InstalledApp
from directorofme_auth import db

### GROUPS
# TODO: DEFAULT OWNERSHIP
def build_groups():
    groups_groups = { "read": (everybody.name,), "write": (admin.name,) }
    groups = {g.name: Group(display_name=g.display_name, type=g.type, **groups_groups) for g in base_groups}

    for scope in [
        db.Model.__scope__,
        Scope(display_name="directorofme_event")
    ]:
        for g in Group.create_scope_groups(scope):
            g.read = groups_groups["read"]
            g.write = groups_groups["write"]
            groups[g.name] = g

    return groups

def build_apps(groups):
    apps = [
        App(
            name="Main",
            desc="DirectorOf.Me's main app. Everyone should have this installed.",
            url="/",
            requested_access_groups = [groups["s-{}-read".format(slugify(db.Model.__scope__.display_name))]],
            read=(everybody.name,),
            write=(admin.name,),
        )
    ]

    schema = None
    with open(os.path.join(os.path.dirname(__file__), "../../json/schemas/daily-standup-app-config.json")) as f:
        schema = json.load(f)
    jsonschema.Draft4Validator.check_schema(schema)

    slugged_event = slugify("directorofme_event")
    return  apps + [
        App(url="/daily-stand-up",
            name="Daily Stand-Up Report",
            config_schema = schema,
            desc="""Start your day off with all the information you need. The Daily Stand-Up report is
                    delivered to you each morning via E-Mail or Chat and has all the information you
                     need to have your best day every day.""",
            requested_access_groups = [
                groups["s-{}-read".format(slugged_event)],
                groups["s-{}-write".format(slugged_event)]
            ],
            read=(user.name,),
            write=(admin.name,),
        )
    ]


def build_profiles(groups, apps):
    # founders
    config = None
    with open(os.path.join(os.path.dirname(__file__), "../../json/examples/daily-standup-app-config.json")) as f:
        config = json.load(f)

    profiles = []
    for (name, email) in (("Matt Story", "matt@directorof.me"),):
        profile = Profile.create_profile(name=name, email=email, add_user_group=False,
                                         additional_groups=[ groups["f-user"], groups["0-admin"] ])
        for app in apps:
            kwargs = {}
            if app.slug == "daily-stand-up-reort":
                jsonschema.validate(config, app.config_schema)
                kwargs = { "config": config }

            InstalledApp.install_for_group(app, profile.group_of_one, **kwargs)

        profiles.append(profile)

    return profiles

def build_dom_license(groups, profiles):
    # dom-admin license
    return License(
        managing_group=groups[admin.name],
        groups=[groups[staff.name]],
        seats=-1,
        profiles=profiles,
        valid_through=None,
        read=[staff.name, admin.name],
        write=[admin.name],
        notes="License for site-admins."
    )

def get_session():
    return sa.orm.session.Session(bind=op.get_bind())

def default_perms(*args):
    return tuple()

@mock.patch.object(db.Model, "default_perms", default_perms)
def upgrade():
    session = get_session()
    groups = build_groups()
    session.add_all(groups.values())

    apps = build_apps(groups)
    session.add_all(apps)

    profiles = build_profiles(groups, apps)
    session.add_all(profiles)

    session.add(build_dom_license(groups, profiles))
    session.commit()

def downgrade():
    # TODO:
    session = get_session()
    session.commit()
