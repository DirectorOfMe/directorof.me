import functools

import flask
import jwt.exceptions
import flask_jwt_extended as flask_jwt

from flask.sessions import SessionInterface as FlaskSessionInterface

from . import session, groups, exceptions
from . import orm


__all__ = [ "JWTSessionInterface", "JWTManager", "Model" ]

class Model(orm.Model):
    __abstract__ = True

    @classmethod
    def default_perms(cls, perm_name):
        return flask.session.default_object_perms.get(perm_name, tuple())

    @classmethod
    def load_groups(cls):
        return flask.session.groups

### Utility
def empty_if_expired(fn):
    '''Wrapper to suppress InvalidTokenErrors, preferring to reset to an empty session'''
    dummy = flask_jwt.jwt_optional(lambda: True)

    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            dummy()
        except jwt.exceptions.InvalidTokenError:
            pass

        return fn(*args, **kwargs)

    return inner

### We are using this basically just to hook up JWT to the request context
class JWTSessionInterface(FlaskSessionInterface):
    '''Hooks up our JWT tokens to the session interface so we can use flask
       the way it was intended but also get the benefit of JWTs. Sessions in
       this system are immutable, and may only be written by an application server'''
    @empty_if_expired
    def open_session(self, app, request):
        '''Populate the session from the JWT cookies at the start of a request'''
        ### TODO: MAYBE RAISE IF KEY IS EXPIRED
        ### TODO: default_objectt_perms
        ### TODO: default_object_perms are strings, but groups are objects ...
        identity = flask_jwt.get_jwt_identity() or {}
        try:
            ###: TODO: app is required, but not yet implemented, re-factor
            app = identity.get("app")
            return session.Session(
                save=False,
                profile=session.SessionProfile(**identity["profile"]),
                groups=[groups.Group(**g) for g in (identity["groups"] or [])],
                app=(app if app is None else session.SessionApp(**app)),
                default_object_perms=identity.get("default_object_perms", {}),
                environment=identity.get("environment", {}))
        except (TypeError, KeyError):
            return session.Session(save=False, app=None, profile=None,groups=[groups.everybody],
                                   environment={}, default_object_perms={ "read": (groups.everybody.name,) })

    def save_session(self, app, session_obj, response):
        '''Save the session at the end of a request if it's new and we are the auth server'''
        if app.config.get("IS_AUTH_SERVER") and session_obj.save:
            flask_jwt.set_access_cookies(response, flask_jwt.create_access_token(session_obj))
            flask_jwt.set_refresh_cookies(response, flask_jwt.create_refresh_token(session_obj))


class JWTManager(flask_jwt.JWTManager):
    '''Our implementation of JWT overrides some things'''
    def init_app(self, app: flask.Flask):
        '''Extension of the JWTManager to configure all servers correctly to
           work together'''
        self.configure_app(app)
        super().init_app(app)

    def configure_app(self, app: flask.Flask):
        app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
        app.config["JWT_COOKIE_CSRF_PROTECT"] = True

        # change the default to ES512
        app.config.setdefault("JWT_ALGORITHM", "ES512")

        # these force asymetric crypto, which is desirable
        if not app.config.get("JWT_PUBLIC_KEY"):
            raise exceptions.MisconfiguredAuthError("JWT_PUBLIC_KEY must be set")

        if app.config.get("JWT_PRIVATE_KEY") and not app.config.get("IS_AUTH_SERVER"):
            raise exceptions.MisconfiguredAuthError(
                "JWT_PRIVATE_KEY may only be specified by the auth server"
            )

        if app.config.get("IS_AUTH_SERVER") and not app.config.get("JWT_PRIVATE_KEY"):
            raise exceptions.MisconfiguredAuthError(
                "JWT_PRIVATE_KEY must be specified by the auth server"
            )

        # hook up the JWT session
        app.session_interface = JWTSessionInterface()
