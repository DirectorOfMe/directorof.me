import os
from directorofme.flask import default_config

def config():
	conf = default_config(name=os.path.basename(os.path.dirname(__file__)))
	conf.update({
        "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "GOOGLE_AUTH_URL": os.environ.get("GOOGLE_AUTH_URL"),
        "GOOGLE_TOKEN_URL": os.environ.get("GOOGLE_TOKEN_URL"),

        "SLACK_APP_ID": os.environ.get("SLACK_APP_ID"),

        "CALENDAR_PRIVATE_KEY_FILE": os.environ.get("CALENDAR_PRIVATE_KEY_FILE"),
        "CALENDAR_PUBLIC_KEY_FILE": os.environ.get("CALENDAR_PUBLIC_KEY_FILE"),
	})

	with open(conf.get("CALENDAR_PRIVATE_KEY_FILE"), "r") as pem_file:
		conf["CALENDAR_PRIVATE_KEY"] = pem_file.read()

	with open(conf.get("CALENDAR_PUBLIC_KEY_FILE"), "r") as pem_file:
		conf["CALENDAR_PUBLIC_KEY"] = pem_file.read()

	return conf

config = config()
