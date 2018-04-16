import os
import pytest

import flask
from werkzeug.contrib.fixers import ProxyFix

from unittest import mock

from directorofme.flask_app import api, default_config
from directorofme.json import JSONEncoder
from directorofme.authorization.exceptions import MisconfiguredAuthError


# open is a PITA to mock
def open_side_effect(name):
    if name is None:
        raise TypeError()
    if open_mock.not_found == name:
        raise FileNotFoundError()

    file_mock = mock.MagicMock()
    file_mock.read.return_value = name
    file_mock.__enter__.return_value = file_mock

    return file_mock

open_mock = mock.mock_open()
open_mock.not_found = None
open_mock.side_effect = open_side_effect

@mock.patch("builtins.open", open_mock)
def test__api_basic(clear_env):
    app = api("app", { "app": { "JWT_PUBLIC_KEY_FILE": "public_key" }})

    assert isinstance(app, flask.Flask), "return a Flask app"
    assert isinstance(app.wsgi_app, ProxyFix), "proxy fix installed"
    assert app.json_encoder is JSONEncoder, "json encoder installed"
    assert app.config["RESTFUL_JSON"]["cls"] is JSONEncoder, "json encoder installed for flask-restful"
    assert app.name == "app", "name set"
    assert app.config["JWT_PUBLIC_KEY"] == "public_key", "public key read"
    assert app.config["PREFERRED_URL_SCHEME"] == "https", "empty app keys don't override defaults"


@mock.patch("builtins.open", open_mock)
def test__api_keys(clear_env):
    # no public key raises
    with pytest.raises(MisconfiguredAuthError):
        api("app", {})

    open_mock.assert_called_with(None)
    open_mock.reset_mock()

    open_mock.not_found = "public_key"
    with pytest.raises(MisconfiguredAuthError):
        api("app", { "app": { "JWT_PUBLIC_KEY_FILE": "public_key" } })

    open_mock.assert_called_with("public_key")
    open_mock.reset_mock()

    open_mock.not_found = None
    app = api("app", { "app": { "JWT_PUBLIC_KEY_FILE": "public_key" }})
    assert app.config["JWT_PUBLIC_KEY"] == "public_key", "public key set correctly for non-auth server"
    open_mock.reset_mock()

    with pytest.raises(MisconfiguredAuthError):
        api("app", { "app": { "JWT_PUBLIC_KEY_FILE": "public_key", "IS_AUTH_SERVER": True }})

    open_mock.assert_has_calls([mock.call("public_key"), mock.call(None)])
    open_mock.reset_mock()

    well_formed_config = {
        "app": {
            "JWT_PUBLIC_KEY_FILE": "public_key",
            "IS_AUTH_SERVER": True,
            "JWT_PRIVATE_KEY_FILE": "private_key"
        }
    }

    open_mock.not_found = "private_key"
    with pytest.raises(MisconfiguredAuthError):
        api("app", well_formed_config)

    # happy path
    open_mock.assert_has_calls([mock.call("public_key"), mock.call("private_key")])
    open_mock.reset_mock()
    open_mock.not_found = None

    app = api("app", well_formed_config)
    assert app.config["JWT_PUBLIC_KEY"] == "public_key", "public key set from read"
    assert app.config["JWT_PUBLIC_KEY"] == "public_key", "private key set from read"


def test__default_config(clear_env):
    # no name passed or in env raises an error
    with pytest.raises(ValueError):
        config = default_config()

    config = default_config("foo")
    assert config["name"] == "foo", "name set"
    assert config["api_name"] is None, "app.api_name defaults to None"

    app_config = config["app"]
    assert app_config["DEBUG"] is False, "app.DEBUG defaults to False"
    assert app_config["PREFERRED_URL_SCHEME"] == "https", "app.PREFERRED_URL_SCHEME defaults to https"
    assert app_config["SERVER_NAME"] is None, "app.SERVER_NAME defaults to None"

    assert app_config["SQLALCHEMY_DATABASE_URI"] is None, "app.SQLALCHEMY_DATABASE_URI defaults to None"
    assert app_config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False, \
       "app.SQLALCHEMY_TRACK_MODIFICATIONS defaults to None"

    assert app_config["IS_AUTH_SERVER"] is False, "app.IS_AUTH_SERVER defaults to False"
    assert app_config["JWT_PUBLIC_KEY_FILE"] is None, "app.PUBLIC_KEY_FILE defaults to None"
    assert app_config["JWT_PRIVATE_KEY_FILE"] is None, "app.PRIVATE_KEY_FILE defaults to None"

def test__default_config_env_overrides(clear_env):
    overridable_keys = {
        "APP_NAME": "name",
        "APP_DEBUG": "app.DEBUG",
        "APP_DB_ENGINE": "app.SQLALCHEMY_DATABASE_URI",
        "SERVER_NAME": "app.SERVER_NAME",
        "JWT_PUBLIC_KEY_FILE": "app.JWT_PUBLIC_KEY_FILE",
        "JWT_PRIVATE_KEY_FILE": "app.JWT_PRIVATE_KEY_FILE",
        "IS_AUTH_SERVER": "app.IS_AUTH_SERVER",
        "API_NAME": "api_name"
    }

    def load_var(config, path):
        working = config
        for name in path.split("."):
            working = working[name]

        return None if working is config else working

    os.environ.update({k:k for k in overridable_keys})
    config = default_config()
    for (key, path) in overridable_keys.items():
        assert key == load_var(config, path), "env var: {} overrides conf var: {}".format(key, path)
