import os
from directorofme.flask import default_config

def config():
	conf = default_config(name=os.path.basename(os.path.dirname(__file__)))
	conf.update({
        "URL_PREFIX": os.environ.get("URL_PREFIX"),

        "SLACK_APP_ID": os.environ.get("SLACK_APP_ID"),
        "SLACK_CLIENT_ID": os.environ.get("SLACK_CLIENT_ID"),
        "SLACK_APP_ID": os.environ.get("SLACK_APP_ID"),
        "SLACK_CLIENT_SECRET": os.environ.get("SLACK_CLIENT_SECRET"),
        "SLACK_VERIFICATION_TOKEN": os.environ.get("SLACK_VERIFICATION_TOKEN"),

        "SLACK_PRIVATE_KEY_FILE": os.environ.get("SLACK_PRIVATE_KEY_FILE"),
        "SLACK_PUBLIC_KEY_FILE": os.environ.get("SLACK_PUBLIC_KEY_FILE"),
	})

	with open(conf.get("SLACK_PRIVATE_KEY_FILE"), "r") as pem_file:
		conf["SLACK_PRIVATE_KEY"] = pem_file.read()

	with open(conf.get("SLACK_PUBLIC_KEY_FILE"), "r") as pem_file:
		conf["SLACK_PUBLIC_KEY"] = pem_file.read()

	return conf

config = config()
