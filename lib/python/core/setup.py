from setuptools import setup, find_packages

setup(
    name="directorofme",
    version="0.1",
    packages=find_packages(),
    setup_requires=[
        "pytest-runner>=3.0",
        "sqlalchemy>=1.2",
        "sqlalchemy-utils>=0.32",
        "flask-sqlalchemy>=2.3.2",
		"flask-jwt-extended[asymmetric_crypto]>=3.6",
    ],
    tests_require=[
        "pytest>=3.2.3",
    ]
)
