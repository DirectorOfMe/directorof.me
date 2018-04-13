import pytest

from directorofme import specify
from directorofme.specify import Attribute, Spec

class Foo(Spec):
    attr = Attribute()
    typed_attr = Attribute(str)
    typed_and_defaulted = Attribute(str, default="hi")
    defaulted = Attribute(default="hi")


class FooIgnoredAttr(Foo):
    ignored = ("attr",)

class TestAttribute:
    def test__attr_contract(self):
        assert Foo.attr.type is None, "type defaults to None"
        assert Foo.typed_attr.type is str, "passed type works"
        assert Foo.typed_and_defaulted.type is str, "passed type with default works"
        assert Foo.typed_and_defaulted.default == "hi" , "default with type works"
        assert Foo.defaulted.default == "hi" , "default without type works"
        assert Foo.defaulted.type is None, "no type with default works"

        for attr in (Foo.attr, Foo.typed_attr):
            assert attr.default is specify.undefaulted, "undefaulted value = sentinel"

    def test__attr_descriptor(self):
        foo = Foo()

        for name in ("attr", "typed_attr"):
            with pytest.raises(ValueError):
                getattr(foo, name)

            setattr(foo, name, "hi")
            assert getattr(foo, name), "setting attribute on instance works"

        assert isinstance(Foo.attr, Attribute), "class var not overridden by set"


class Bar:
    pass

class TestSpec:
    attrs = ("attr", "typed_attr", "typed_and_defaulted", "defaulted")

    def test__init__takes_kwargs(self):
        foo = Foo(**{attr: attr for attr in self.attrs})

        for name in self.attrs:
            assert getattr(foo, name) == name, "init args work"

    def test__init__defaults_correctly(self):
        foo = Foo()

        # first make sure nothing was defautled that shouldn't have been
        for name in ("attr", "typed_attr"):
            with pytest.raises(ValueError):
                getattr(foo, name)

        # now test defaults
        for name in ("typed_and_defaulted", "defaulted"):
            assert getattr(foo, name) == "hi", "defaults work on instances"


    def test__json_encode__(self):
        kwargs = {name: name for name in self.attrs}
        assert kwargs == Foo(**kwargs).__json_encode__(), "encoder works"

    def test__ignored(self):
        kwargs = {name: name for name in self.attrs if name != "attr"}
        assert kwargs == FooIgnoredAttr(**kwargs).__json_encode__(), "ignores works"

    def test__from_conforming_type(self):
        bar = Bar()
        with pytest.raises(AttributeError):
            Foo.from_conforming_type(bar)

        for attr in self.attrs:
            setattr(bar, attr, "hi")

        from_bar = Foo.from_conforming_type(bar)
        assert isinstance(from_bar, Foo), "from_conforming_type is correct type"
        for name in self.attrs:
            assert getattr(from_bar, name) == "hi", "attributes set"
