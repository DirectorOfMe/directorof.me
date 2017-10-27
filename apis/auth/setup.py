from setuptools import setup, find_packages

setup(
    name="dom-auth-api",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask==0.12.2",
        "flask-restful==0.3.5",
        "gunicorn==19.7",
    ]
)
