import os
from directorofme.flask_app import default_config

def config():
    dflt = default_config()
    dflt.update({
        "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "GOOGLE_AUTH_URL": os.environ.get("GOOGLE_AUTH_URL"),
        "GOOGLE_TOKEN_URL": os.environ.get("GOOGLE_TOKEN_URL"),
    })

    return dflt
