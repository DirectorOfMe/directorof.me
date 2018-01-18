from setuptools import setup, find_packages

setup(
    name="dom-auth-api",
    version="0.1",
    packages=find_packages(),
    install_requires=[
		"directorofme",
        "directorofme_flask_restful",
        "flask==0.12.2",
        "flask-restful==0.3.5",
        "sqlalchemy>=1.2",
        "sqlalchemy-utils>=0.32",
        "python-slugify>=1.2.4",
        "gunicorn==19.7",
    ]
)
