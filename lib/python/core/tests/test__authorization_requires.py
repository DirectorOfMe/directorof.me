import pytest
import flask

from unittest import mock

from directorofme.authorization import requires, groups, session
from directorofme.authorization.exceptions import PermissionDeniedError

class TestRequiresDecorator:
    def test__basic(self, request_context_with_session):
        flask.session.groups = [groups.everybody, groups.user, groups.admin]
        for g in flask.session.groups:
            decorator = requires.RequiresDecorator(g)
            with decorator:
                with requires.RequiresDecorator(decorator):
                    assert True, "RequiresDecorator works with a passed decorator as well as with a group"

        with pytest.raises(PermissionDeniedError):
            with requires.RequiresDecorator(groups.root):
                assert False, "should not be reached -- when group passed"

        with pytest.raises(PermissionDeniedError):
            with requires.RequiresDecorator(requires.RequiresDecorator(groups.root)):
                assert False, "should not be reached -- when decorator passed"


        with pytest.raises(ValueError):
            requires.RequiresDecorator(object())

    def test__passed_session(self, request_context_with_session):
        flask.session.groups = []
        real_session = session.Session(save=False, app=None, profile=None, groups=[groups.everybody],\
                                       environment={})

        with pytest.raises(PermissionDeniedError):
            with requires.RequiresDecorator(groups.everybody):
                assert False, "should fail with flask.session"

        with requires.RequiresDecorator(groups.everybody, session=real_session):
            assert True, "should succeed with this passed session"


    def test__as_a_decorator(self, request_context_with_session):
        ensure_call = mock.Mock()

        flask.session.groups = [groups.everybody]

        @requires.RequiresDecorator(groups.everybody)
        def test_decoration():
            ensure_call()

        test_decoration()
        assert ensure_call.called, "decorated method was called"

        ensure_call.reset_mock()

        @requires.RequiresDecorator(groups.root)
        def test_decoration_no():
            ensure_call()

        with pytest.raises(PermissionDeniedError):
            test_decoration_no()

        assert not ensure_call.called, "decorated method should not have been called"


    def test__test(self, request_context_with_session):
        flask.session.groups = [groups.everybody, groups.root]

        req_everybody = requires.RequiresDecorator(groups.everybody)
        req_root = requires.RequiresDecorator(groups.root)
        req_admin = requires.RequiresDecorator(groups.admin)

        assert req_everybody.test(), "everybody group works when present"
        assert requires.RequiresDecorator(req_everybody).test(), "everybody works when present as a requierement"
        assert requires.RequiresDecorator(req_everybody, and_=groups.root).test(), \
               "everybody and root works when both present"
        assert requires.RequiresDecorator(req_everybody, or_=req_root).test(), \
               "everybody and root works when both present"
        assert not requires.RequiresDecorator(req_everybody, and_=req_admin).test(), \
               "everybody and admin fails when one is not present"
        assert not requires.RequiresDecorator(req_admin, and_=groups.admin).test(), \
               "and fails when both sides not present"

        assert requires.RequiresDecorator(req_everybody, or_=req_admin).test(), \
               "or succeeds when left side is present"
        assert requires.RequiresDecorator(req_admin, or_=groups.everybody).test(), \
               "or succeeds when right side is present"
        assert not requires.RequiresDecorator(req_admin, or_=req_admin).test(), \
               "or fails when both sides are not present"

        assert requires.RequiresDecorator(req_everybody, or_=req_admin, and_=req_root).test(), \
               "and but not or present works"
        assert not requires.RequiresDecorator(req_everybody, and_=req_admin, or_=req_root).test(), \
               "or but not and present fails"

    def test__ands(self, request_context_with_session):
        flask.session.groups = [groups.everybody, groups.root]

        req_everybody = requires.RequiresDecorator(groups.everybody)
        req_root = requires.RequiresDecorator(groups.root)
        req_admin = requires.RequiresDecorator(groups.admin)

        for everybody_and_root in (req_everybody & req_root, req_everybody.and_(req_root)):
            assert isinstance(everybody_and_root, requires.RequiresDecorator), "and_ and & return decorator"
            assert everybody_and_root is not req_everybody, "new instance created by and_ and &"
            assert everybody_and_root is not req_root, "new instance created by and_ and &"
            assert everybody_and_root.test(), "test works for and_ and &"

        assert not req_root.and_(req_admin).test(), "when one side isn't in session it and_.test should fail"

    def test__ors(self, request_context_with_session):
        flask.session.groups = [groups.everybody]

        req_everybody = requires.RequiresDecorator(groups.everybody)
        req_root = requires.RequiresDecorator(groups.root)
        req_admin = requires.RequiresDecorator(groups.admin)

        for everybody_or_root in (req_everybody | req_root, req_everybody.or_(req_root)):
            assert isinstance(everybody_or_root, requires.RequiresDecorator), "or_ and | return decorator"
            assert everybody_or_root is not req_everybody, "new instance created by or_ and |"
            assert everybody_or_root is not req_root, "new instance created by or_ and |"
            assert everybody_or_root.test(), "test works for or_ and |"

        assert not req_root.or_(req_admin).test(), "when neither side is defined, or_.test returns false"

def test__group(request_context_with_session):
    mock_inner = mock.Mock()

    @requires.group(groups.root)
    def foo():
        mock_inner()

    flask.session.groups = [groups.root, groups.admin]
    foo()
    assert mock_inner.called, "foo was called"

    mock_inner.reset_mock()
    flask.session.groups = [groups.admin]
    with pytest.raises(PermissionDeniedError):
        foo()

    assert not mock_inner.called, "foo was not called"


def test__scope(request_context_with_session):
    test_scope = groups.Scope(name="test")
    flask.session.groups = [test_scope.read]

    with requires.scope("test", "read"):
        assert True, "test scope read permission enabled"

    with pytest.raises(PermissionDeniedError):
        with requires.scope("test", "read") & requires.scope("test", "write"):
            assert False, "should not be reached"

def test__feature(request_context_with_session):
    flask.session.groups = [groups.user]

    with requires.feature("user") | requires.group(groups.root):
        assert True, "test feature works with permission enabled"

    with pytest.raises(PermissionDeniedError):
        with requires.feature("pro") | requires.group(groups.root):
            assert False, "should not be reached"

def test__admin_user_staff_everybody_anybody(request_context_with_session):
    flask.session.groups = [groups.user]
    assert requires.user.test(), "user helper succeeds"
    flask.session.groups = [groups.admin]
    assert requires.admin.test(), "admin helper succeeds"
    flask.session.groups = [groups.staff]
    assert requires.staff.test(), "user helper succeeds"
    flask.session.groups = [groups.everybody]
    assert requires.everybody.test(), "everybody helper succeeds"
    assert requires.anybody.test(), "anybody helper succeeds"
