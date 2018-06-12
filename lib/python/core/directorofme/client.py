from requests import Session
from furl import furl

from json.decoder import JSONDecodeError

import flask_jwt_extended as flask_jwt

__all__ = [ "Unauthorized", "PermissionDenied", "BadRequest", "NotFound", "ServerError", "ClientError", "DOM" ]

class ClientError(Exception):
    pass

class Unauthorized(ClientError):
    pass

class PermissionDenied(ClientError):
    pass

class BadRequest(ClientError):
    pass

class NotFound(ClientError):
    pass

class Conflict(ClientError):
    pass

class ServerError(ClientError):
    pass

class DOM(Session):
    def __init__(self, domain, version="-", access_token=None, access_csrf_token=None,
                 refresh_token=None, refresh_csrf_token=None):
        self.__url = furl("https://")
        self.__url.host = domain
        self.__url.path.segments = [ "api", version ]
        super().__init__()

        if access_csrf_token is not None:
            self.headers["X-CSRF-TOKEN"] = access_csrf_token
        if refresh_csrf_token is not None:
            self.headers["X-CSRF-REFRESH-TOKEN"] = refresh_csrf_token

        if access_token is not None:
            self.cookies["access_token_cookie"] = access_token
        if refresh_token is not None:
            self.cookies["refresh_token_cookie"] = refresh_token

    def url(self, url):
        url_ = self.__url.copy()
        url_.path.segments.extend(url.split("/"))
        return url_.url

    def check(self, response):
        if response.status_code in (200, 201, 301, 302):
            return response.json()
        elif response.status_code in (204, 304):
            return None

        errors = {
            400: BadRequest,
            401: Unauthorized,
            403: PermissionDenied,
            404: NotFound,
            409: Conflict,
        }

        try:
            raise errors[response.status_code](response.json().get("message"))
        except JSONDecodeError:
            raise errors[response.status_code](response.text)
        except KeyError:
            raise ServerError(response.text)

    def get(self, url, *args, **kwargs):
        return self.check(super().get(url=self.url(url), *args, **kwargs))

    def post(self, url, data=None, *args, **kwargs):
        return self.check(super().post(url=self.url(url), json=data, *args, **kwargs))

    def put(self, url, data=None, *args, **kwargs):
        return self.check(super().put(url=self.url(url), json=data, *args, **kwargs))

    def delete(self, url, data=None, *args, **kwargs):
        return self.check(super().delete(url=self.url(url), json=data, *args, **kwargs))

    def patch(self, url, data=None, *args, **kwargs):
        return self.check(super().patch(url=self.url(url), json=data, *args, **kwargs))

    def refresh(self):
        resp = self.put("auth/session")
        if self.cookies.get("csrf_access_token") is not None:
            self.headers["X-CSRF-TOKEN"] = self.cookies["csrf_access_token"]
        if self.cookies.get("csrf_refresh_token") is not None:
            self.headers["X-CSRF-REFRESH-TOKEN"] = self.cookies["csrf_refresh_token"]

        return resp

    @classmethod
    def from_request(cls, request, app=None):
        access_token = request.cookies.get("access_token_cookie")
        csrf_token = request.headers.get("X-CSRF-TOKEN")

        refresh_token = request.cookies.get("refresh_token_cookie")
        refresh_csrf_token = request.headers.get("X-CSRF-REFRESH-TOKEN")

        if app is not None:
            if csrf_token is None and access_token:
                with app.app_context():
                    csrf_token = flask_jwt.get_csrf_token(access_token.encode("utf-8"))

            if refresh_csrf_token is None and refresh_token:
                with app.app_context():
                    refresh_csrf_token = flask_jwt.get_csrf_token(refresh_token.encode("utf-8"))

        return cls(
            request.host,
            access_token=access_token,
            access_csrf_token=csrf_token,
            refresh_token=refresh_token,
            refresh_csrf_token=refresh_csrf_token
        )

    @classmethod
    def from_installed_app(cls, domain, cipher, installed_app):
        try:
            dom_integration = installed_app["config"]["integrations"]["directorofme"]
        except KeyError:
            raise ValueError("InstalledApp must have `directorofme` integration in config")

        try:
            refresh_token = cipher.decrypt(dom_integration["refresh_token"]["value"])
            refresh_csrf_token = cipher.decrypt(dom_integration["refresh_csrf_token"]["value"])
        except KeyError as e:
            raise ValueError("Missing token: {}".format(e))

        client = DOM(domain, refresh_token=refresh_token, refresh_csrf_token=refresh_csrf_token)
        client.refresh()

        return client
