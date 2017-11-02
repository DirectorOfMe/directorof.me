from directorofme.stubtools import Model

from . import Group

class App(Model):
    examples = {
        "dashboard": {
            "id": "dashboard",
            "name": "Application Dashboard",
            "url": "/dashboard",
            "callback_url": "/post_auth",
            "config_schema": {
                "title": "dashboard-config",
                "type": "object",
                "properties": {
                    "feed": {
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "format": "DOMQL"
                            },
                            "items_per_page": {
                                "type": "integer",
                                "default": 25
                            }
                        }
                    }
                }
            },
            "groups": [
                Group.query.get("app/dashboard")
            ]
        }
    }

class InstalledApp(Model):
    examples = {
        "dashboard/12345": {
            "app_id": "dashboard",
            "app": App.query.get("dashboard"),
            "config": {
                "feed": {
                    "filter": "type IN ('forecast', 'new issue')"
                }
            }
        }
    }
