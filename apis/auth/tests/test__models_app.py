import uuid

import pytest

from directorofme.authorization.groups import Scope
from directorofme.testing import commit_with_integrity_error, existing

from directorofme_auth.models import App, InstalledApp, Group

class TestApp:
    def test__mininum_well_formed(self, db):
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

    def test__slug_autogenerates_when_name_set(self, db):
        app = App()

        assert app.name is None, "slug none if name not set"
        assert app.slug is None, "slug none if name not set"

        app.name = "test_Foo"
        assert app.slug == "test-foo", "slugified name set to slug"
        assert app.name == "test_Foo", "un-sluggified name set to name"

        app.name = "test_Bar"
        assert app.slug == "test-bar", "slugified name set on update to attr"

        app = App(name="test_Baz")
        assert app.name == "test_Baz", "__init__ sets up name"
        assert app.slug == "test-baz", "__init__ sets up slug when not passed"

        app = App(name="test_Foo_again", slug="slug")
        assert app.slug == "test-foo-again", \
               "passed slug is overridden by slugified name"

    def test__unique_name_and_slug(self, db):
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

    def test__required_fields(self, db):
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

    def test__requested_scopes(self, db):
        assert App().requested_access_groups == [], \
               "no requested access groups and property returns an empty list"

        one_scope_groups = [
            Group(name="s-test-1", scope_name="test", scope_permission="test_1"),
            Group(name="s-test-2", scope_name="test", scope_permission="test_2")
        ]
        one_scope_app = App(requested_access_groups=one_scope_groups)

        assert one_scope_app.requested_access_groups == one_scope_groups, \
               "__init__ sets up requested_access_groups"

        requested_scopes = one_scope_app.requested_scopes
        assert len(requested_scopes) == 1, "There is one scope"
        assert isinstance(requested_scopes[0], Scope), "the scope is a Scope"
        assert requested_scopes[0].name == "test", "The one scope is right"
        assert requested_scopes[0].perms["test_1"].name == one_scope_groups[0].name, \
               "permission 1 is correct"
        assert requested_scopes[0].perms["test_2"].name == one_scope_groups[1].name, \
               "permission 2 is correct"

class TestInstalledApp:
    def test__minimum_well_formed(self, db):
        pass

    def test__required_fields(self, db):
        pass

    def test__scopes(self, db):
        pass

    def test__install_for_group(self, db):
        pass
