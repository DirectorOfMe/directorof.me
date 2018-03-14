import os

###: TODO: move this to core and factor it
def config():
    return {
        "name": os.environ.get(
            "APP_CONFIG_NAME",
            os.path.basename(os.path.dirname(__file__))
        ),
        "app": {
            "DEBUG": os.environ.get("APP_DEBUG", False),
            "SQLALCHEMY_DATABASE_URI": os.environ.get("APP_DB_ENGINE", None),
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "PREFERRED_URL_SCHEME": "https",
            "SERVER_NAME": os.environ.get("SERVER_NAME"),
            "JWT_PUBLIC_KEY_FILE": os.environ.get("JWT_PUBLIC_KEY_FILE"),
            "JWT_PRIVATE_KEY_FILE": os.environ.get("JWT_PRIVATE_KEY_FILE"),
            "IS_AUTH_SERVER": True
        },

        "API_NAME": os.environ.get("API_NAME"),

        "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "GOOGLE_AUTH_URL": os.environ.get("GOOGLE_AUTH_URL"),
        "GOOGLE_TOKEN_URL": os.environ.get("GOOGLE_TOKEN_URL"),
    }
