"""empty message

Revision ID: edb1f4bba89e
Revises: 7705ff00b511
Create Date: 2018-01-30 21:57:11.153630

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'edb1f4bba89e'
down_revision = '29b7f139356a'
branch_labels = None
depends_on = None

from slugify import slugify

from directorofme.authorization import orm
from directorofme.authorization.groups import base_groups, admin, staff
from directorofme_auth.models import Group, GroupTypes, License, Profile, App, InstalledApp

### GROUPS
# TODO: DEFAULT OWNERSHIP
def build_groups():
    groups = {g.name: Group(display_name=g.display_name, type=g.type) for g in base_groups}
    for g in Group.create_scope_groups(orm.Model.__scope__):
        groups[g.name] = g

    return groups

def build_main_app(groups):
    # TODO: requested access groups
    return App(
        name="Main",
        desc="DirectorOf.Me's main app. Everyone should have this installed.",
        url="/",
        requested_access_groups = [groups["s-{}-read".format(slugify(orm.Model.__scope__.display_name))]]
    )


def build_profiles(groups, main_app):
    # founders
    profiles = []
    for (name, email) in (("Matt Story", "matt@directorof.me"),
                          ("Barb Blakley", "barb@directorof.me")):
        profile = Profile.create_profile(name=name, email=email)
        profile.licenses[0].groups.extend([ groups["f-user"], groups["0-admin"] ])
        InstalledApp.install_for_group(main_app, profile.group_of_one)
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

def upgrade():
    session = get_session()
    groups = build_groups()
    session.add_all(groups.values())

    main_app = build_main_app(groups)
    session.add(main_app)

    profiles = build_profiles(groups, main_app)
    session.add_all(profiles)

    session.add(build_dom_license(groups, profiles))
    session.commit()

def downgrade():
    # TODO:
    session = get_session()
    session.commit()
