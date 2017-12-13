from setuptools import setup, find_packages

setup(
    name="directorofme_flask_restful",
    version="0.1",
    packages=find_packages(),
    install_requires=[
		"directorofme",
        "flask==0.12.2",
        "flask-restful==0.3.5",
    ]
)
