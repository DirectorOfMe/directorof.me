import pytest

from unittest import mock
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String

from directorofme import orm

def test__slugify_on_change():
    init_mock = mock.Mock()

    @orm.slugify_on_change("name", "slug")
    class Slugify(declarative_base()):
        __tablename__ = "slugify_test"

        name = Column(String, primary_key=True)
        slug = Column(String)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            init_mock()

    @orm.slugify_on_change("name2", "slug2")
    class SlugifyNoInit(Slugify):
        name2 = Column(String)
        slug2 = Column(String)


    slugified = Slugify()
    assert init_mock.called, "Slugify.__init__ was called"

    assert slugified.name is None, "slug none if name not set"
    assert slugified.slug is None, "slug none if name not set"

    slugified.name = "test_Foo"
    assert slugified.slug == "test-foo", "slugified name set to slug"
    assert slugified.name == "test_Foo", "un-sluggified name set to name"

    slugified.name = "test_Bar"
    assert slugified.slug == "test-bar", "slugified name set on update to attr"

    slugified = Slugify(name="test_Baz")
    assert slugified.name == "test_Baz", "__init__ sets up name"
    assert slugified.slug == "test-baz", "__init__ sets up slug when not passed"

    slugified = Slugify(name="test_Foo_again", slug="slug")
    assert slugified.slug == "test-foo-again", "passed slug is overridden by slugified name"

    init_mock.reset_mock()
    no_init = SlugifyNoInit(name="test_Name", name2="test_Name 2")
    assert init_mock.called, "super().__init__ called by decorated sub-class"
    assert no_init.slug2 == "test-name-2", "sub-class slugger works"

    no_init.name2 = "test_Name2 again"
    assert no_init.slug2 == "test-name2-again", "update works on superclass"

    with pytest.raises(ValueError):
        orm.slugify_on_change("name", "slugged")(declarative_base())
