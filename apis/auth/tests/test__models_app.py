import uuid

from directorofme.authorization.groups import Scope, Group as AuthGroup
from directorofme.testing import commit_with_integrity_error, existing

from directorofme_auth.models import App, InstalledApp, Group, GroupTypes

def scopes_helper(cls, group_attr, scope_attr):
    obj = cls()
    assert getattr(obj, group_attr) == [], \
           "no {} returns an empty list".format(group_attr)

    one_scope_groups = [
        Group(name="s-test-1", scope_name="test", scope_permission="test_1"),
        Group(name="s-test-2", scope_name="test", scope_permission="test_2")
    ]

    setattr(obj, group_attr, one_scope_groups)
    scopes = getattr(obj, scope_attr)

    assert len(scopes) == 1, "There is one scope"
    assert isinstance(scopes[0], Scope), "the scope is a Scope"
    assert scopes[0].name == "test", "The one scope is right"
    assert scopes[0].perms["test_1"].name == one_scope_groups[0].name, \
           "permission 1 is correct"
    assert scopes[0].perms["test_2"].name == one_scope_groups[1].name, \
           "permission 2 is correct"


class TestApp:
    def test__mininum_well_formed(self, db, disable_permissions):
        app = App(name="test", desc="test app", url="https://directorof.me/")
        assert app.name == "test", "name set"
        assert app.slug == "test", "slug generated from name by __init__"
        assert app.desc == "test app", "description (desc) set"
        assert app.url == "https://directorof.me/"

        assert app.id is None, "id None until saved"
        assert existing(app, "name") is None, "no app pre-save"

        db.session.add(app)
        db.session.commit()

        assert isinstance(app.id, uuid.UUID), "id set after commit"

    def test__unique_name_and_slug(self, db, disable_permissions):
        app = App(name="foo", desc="r", url="https://directorof.me/")
        assert existing(app, "name") is None, "app not saved"

        db.session.add(app)
        db.session.commit()

        assert isinstance(existing(app, "name"), App), "app exists after saving"

        app_duplicate_name = App(name="foo", desc="r2", url="https://directorof.me/")
        app_duplicate_name.slug = "uniq"
        assert existing(app_duplicate_name, "slug") is None, "slug is unique"

        commit_with_integrity_error(db, app_duplicate_name)

        app_duplicate_slug = App(name="uniq", desc="r2", url="https://directorof.me/")
        app_duplicate_slug.slug = "foo"

        assert existing(app_duplicate_slug, "name") is None, "name is unique"
        commit_with_integrity_error(db, app_duplicate_slug)

    def test__required_fields(self, db, disable_permissions):
        #: TODO - factor this
        missing_name = App(slug="foo", desc="r", url="https://directorof.me/")
        assert existing(missing_name, "slug") is None, "slug is unique"
        commit_with_integrity_error(db, missing_name)

        missing_name.name = "foo"
        db.session.add(missing_name)
        db.session.commit()
        assert existing(missing_name, "name").name == "foo", "save works if name set"

        # slug
        missing_slug = App(name="bar", desc="r", url="https://directorof.me/")
        missing_slug.slug = None
        assert existing(missing_slug, "name") is None, "bar does not exist"
        commit_with_integrity_error(db, missing_slug)

        missing_slug.slug = "bar"
        db.session.add(missing_slug)
        db.session.commit()
        assert existing(missing_slug, "name").slug == "bar", "save works if slug set"

        # desc
        missing_desc = App(name="baz", url="https://directorof.me/")
        assert existing(missing_desc, "name") is None, "baz does not exist"
        commit_with_integrity_error(db, missing_desc)

        missing_desc.desc= "r3"
        db.session.add(missing_desc)
        db.session.commit()
        assert existing(missing_desc, "name").desc == "r3", "save works if desc set"

        # url
        missing_url = App(name="url", desc="r")
        assert existing(missing_url, "name") is None, "url does not exist"
        commit_with_integrity_error(db, missing_url)

        missing_url.url = "https://example.com/"
        db.session.add(missing_url)
        db.session.commit()
        assert existing(missing_url, "name").url == "https://example.com/", \
               "save works if url set"

    def test__requested_scopes(self, db, disable_permissions):
        scopes_helper(App, "requested_access_groups", "requested_scopes")


class TestInstalledApp:
    def test__minimum_well_formed(self, db, disable_permissions):
        app = App(name="test", desc="test app", url="https://directorof.me/")
        assert existing(app, "name") is None, "no app pre-save"

        installed_app = InstalledApp(app=app)
        assert installed_app.app == app, "app setup correctly"
        assert installed_app.app_id is None, "app_id None until saved"
        assert installed_app.id is None, "id None until saved"

        db.session.add(installed_app)
        db.session.commit()

        assert isinstance(installed_app.id, uuid.UUID), "id set after commit"
        assert isinstance(app.id, uuid.UUID), "id set after commit"

    def test__required_fields(self, db, disable_permissions):
        missing_app = InstalledApp()
        assert existing(missing_app, "app") is None, "app does not exist"
        commit_with_integrity_error(db, missing_app)

        missing_app.app = App(name="test", desc="r", url="https://directorof.me/")
        db.session.add(missing_app)
        db.session.commit()
        assert existing(missing_app, "app").app.name == "test", "works if app set"

    def test__scopes(self, db, disable_permissions):
        scopes_helper(InstalledApp, "access_groups", "scopes")

    def test__install_for_group(self, db, disable_permissions):
        # basic setup
        owner = Group(display_name="tester", type=GroupTypes.data)
        app = App(name="basic", desc="basic app", url="http://example.com")

        installed = InstalledApp.install_for_group(app, owner)
        assert isinstance(installed, InstalledApp), "factory returns correct class"
        assert installed.app == app, "app setup correctly"
        assert installed.read == (owner.name,), "permissions setup correctly"
        assert installed.id is None, "id not yet set"

        db.session.add(owner)
        db.session.add(installed)
        db.session.commit()

        assert isinstance(installed.id, uuid.UUID), "id set after successful save"

        # with auth group group
        owner = Group(display_name="tester2", type=GroupTypes.data)
        auth_owner = AuthGroup.from_conforming_type(owner)
        installed = InstalledApp.install_for_group(app, auth_owner)

        db.session.add(owner)
        db.session.add(installed)
        db.session.commit()
        assert installed.read == (owner.name,), "permissions setup correctly"

        # with group name
        owner = Group(display_name="tester3", type=GroupTypes.data)
        installed = InstalledApp.install_for_group(app, owner.name)

        db.session.add(owner)
        db.session.add(installed)
        db.session.commit()
        assert installed.read == (owner.name,), "permissions setup correctly"

        # with implicit access_groups
        access_groups = [ Group(display_name="access1", type=GroupTypes.scope,
                                scope_name="test", scope_permission="test") ]
        app.requested_access_groups = access_groups

        installed = InstalledApp.install_for_group(app, owner)
        assert len(installed.access_groups) == 1, "access group installed"
        assert installed.access_groups[0].name == access_groups[0].name, \
               "access group installed"
        assert len(installed.scopes) == 1, "scopes works"


        # with passed access_groups
        access_groups = [ Group(display_name="access2", type=GroupTypes.scope,
                                scope_name="test", scope_permission="test") ]

        installed = InstalledApp.install_for_group(
                        app, owner, access_groups=access_groups)
        assert len(installed.access_groups) == 1, "access group installed"
        assert installed.access_groups[0].name == access_groups[0].name, \
               "access group installed"
        assert len(installed.scopes) == 1, "scopes works"

        # config
        installed = InstalledApp.install_for_group(app, owner, config={})
        assert installed.config == {}, "config added"
