"""empty message

Revision ID: edb1f4bba89e
Revises: 7705ff00b511
Create Date: 2018-01-30 21:57:11.153630

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'edb1f4bba89e'
down_revision = '7705ff00b511'
branch_labels = None
depends_on = None

from directorofme.authorization.groups import scope
from directorofme_auth.models import Group, GroupTypes, License, Profile,\
                                     App, InstalledApp

### GROUPS
# TODO: DEFAULT OWNERSHIP
def build_groups():
    everybody = Group(display_name="everybody", type=GroupTypes.system)
    user = Group(display_name="user", type=GroupTypes.feature, parent=everybody)

    groups = {
        ### 0-root and 0-admin members can selectively skip access controls
        # this group can never be added to a signed session
        "0-root": Group(display_name="root", type=GroupTypes.system),
        # group members of this group may temporarily add root to a session
        "0-admin": Group(display_name="admin", type=GroupTypes.system),

        # used to delete things, anybody can set to this group
        "0-nobody": Group(display_name="nobody", type=GroupTypes.system),

        # everybody, logged in or otherwise
        "0-everybody": everybody,

        # anyone with an account
        "f-user": user,

        # dom admins
        "f-dom-admin": Group(display_name="dom-admin", type=GroupTypes.feature,
                             parent=user)
    }

    for s in scope.known_scopes.values():
        for g in Group.create_scope_groups(s):
            groups[g.name] = g

    return groups

def build_main_app(groups):
    # TODO: requested access groups
    return App(
        name="Main",
        desc="DirectorOf.Me's main app. Everyone should have this installed.",
        url="/",
        requested_access_groups = [groups["s-profile-read"]]
    )


def build_profiles(groups, main_app):
    # founders
    profiles = []
    for (name, email) in (("Matt Story", "matt@directorof.me"),
                          ("Barb Blakley", "barb@directorof.me")):
        profiles.append(Profile.create_profile(
            name=name, email=email,
            additional_groups=[
                groups["f-user"],
                groups["0-admin"],
            ],
            install_apps=[main_app]))


    return profiles

def build_dom_license(groups, profiles):
    # dom-admin license
    return License(
        managing_group=groups["0-admin"],
        groups=[groups["f-dom-admin"]],
        seats=-1,
        profiles=profiles,
        valid_through=None,
        read=[groups["f-dom-admin"].name, groups["0-admin"].name],
        write=[groups["0-admin"].name],
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
