import uuid

from flask import Flask
from flask.sessions import SessionInterface as FlaskSessionInterface
import flask_jwt_extended as jwt
from . import session, exceptions

### We are using this basically just to hook up JWT to the request context
class SessionInterface(FlaskSessionInterface):
    def open_session(self, app, request):
        jwt_claims = jwt.get_jwt_claims()
        return session.Session(
            id = uuid.UUID(jwt.get_jti()),
            profile=session.SessionProfile(**jwt.get_jwt_identity()),
            groups=[session.SessionGroup(**g) for g in jwt_claims.get("groups", [])],
            app=session.SessionApp(jwt_claims.get("app", {})),
            environment=jwt_claims.get("environment", {}))

    ###: TODO: this isn't setup
    def null_session(self, *args, **kwargs):
        return session.Session.anonymous()

    def save_session(self, *args, **kwargs):
        '''No-Op. Session is stateless'''
        pass

class JWTManager(jwt.JWTManager):
    '''Our implementation of JWT overrides some things'''
    def init_app(self, app: Flask):
        self.configure_app(app)
        super().init_app(app)

    def configure_app(self, app: Flask):
        app.config['JWT_TOKEN_LOCATION'] = ['cookies']
        app.config['JWT_COOKIE_CSRF_PROTECT'] = True

        # change the default to EC512
        app.config.setdefault('JWT_ALGORITHM', 'EC512')

        # these force asymetric crypto, which is desirable
        if not app.config.get('JWT_PUBLIC_KEY'):
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
        app.session_interface = SessionInterface()
