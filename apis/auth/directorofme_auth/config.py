import os
from directorofme.flask import default_config

def config():
    dflt = default_config(name=os.path.basename(os.path.dirname(__file__)))
    dflt["app"]["IS_AUTH_SERVER"] = True
    dflt.update({
        "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "GOOGLE_AUTH_URL": os.environ.get("GOOGLE_AUTH_URL"),
        "GOOGLE_TOKEN_URL": os.environ.get("GOOGLE_TOKEN_URL"),

        "SLACK_CLIENT_ID": os.environ.get("SLACK_CLIENT_ID"),
        "SLACK_CLIENT_SECRET": os.environ.get("SLACK_CLIENT_SECRET"),
        "SLACK_AUTH_URL": os.environ.get("SLACK_AUTH_URL"),
        "SLACK_TOKEN_URL": os.environ.get("SLACK_TOKEN_URL"),

        "MODELS_SCOPE_NAME": "auth"
    })

    return dflt
