import pytest
from directorofme.registry import RegisterByName

def test__make_registrymetaclass():
    type_ = RegisterByName.make_registrymetaclass()
    assert type_.registry == {}, "registry is empty"

    class A(metaclass=type_):
        name = "A"
    assert type_.registry == { "A": A }, "A is registered"

    with pytest.raises(TypeError):
        class AAgain(metaclass=type_):
            name = "A"

    assert RegisterByName.make_registrymetaclass().registry == {}, "new metaclass has new registry"


def test__by_name():
    class WithRegistry(RegisterByName, metaclass=RegisterByName.make_registrymetaclass()):
        pass

    assert WithRegistry.by_name("sub") is None, "no sub if not created yet"

    class Sub(WithRegistry):
        name = "sub"
    assert WithRegistry.by_name("sub") is Sub, "Sub registered properly"
