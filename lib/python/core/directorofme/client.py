from requests import Session
from furl import furl

__all__ = [ "Unauthorized", "PermissionDenied", "BadRequest", "NotFound", "ServerError", "DOM" ]

class Unauthorized(Exception):
    pass

class PermissionDenied(Exception):
    pass

class BadRequest(Exception):
    pass

class NotFound(Exception):
    pass

class ServerError(Exception):
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
        if response.status_code in (204, 304):
            return None
        elif response.status_code < 400:
            return response.json()

        errors = {
            400: BadRequest,
            401: Unauthorized,
            403: PermissionDenied,
            404: NotFound
        }

        if response.status_code in errors:
            raise errors[response.status_code](response.json().get("message"))
        raise ServerError(response.text)

    def get(self, url, *args, **kwargs):
        return self.check(super().get(url=self.url(url), *args, **kwargs))

    def post(self, url, *args, **kwargs):
        return self.check(super().post(url=self.url(url), *args, **kwargs))

    def put(self, url, *args, **kwargs):
        return self.check(super().put(url=self.url(url), *args, **kwargs))

    def delete(self, url, *args, **kwargs):
        return self.check(super().delete(url=self.url(url), *args, **kwargs))

    def patch(self, url, *args, **kwargs):
        return self.check(super().patch(url=self.url(url), *args, **kwargs))

    def refresh(self):
        return self.put("auth/refresh")