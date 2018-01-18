import os

import flask
import flask_restful
import sqlalchemy

config = {
    "config_file": os.environ.get("APP_CONFIG_FILE"),
    "name": os.environ.get(
        "APP_CONFIG_NAME",
        os.path.basename(os.path.dirname(__file__))
    ),
    "app": {
        "DEBUG": os.environ.get("APP_DEBUG", False),
    },
    "db": {
        "engine": os.environ.get("APP_DB_ENGINE", None),
    }
}

app = flask.Flask(config["name"])
app.config.update(config["app"])
api = flask_restful.Api(app)
db = sqlalchemy.create_engine(config["db"]["engine"])
