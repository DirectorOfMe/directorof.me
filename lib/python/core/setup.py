from setuptools import setup, find_packages

setup(
    name="directorofme",
    version="0.1",
    packages=find_packages(),
    setup_requires=[
        "pytest-runner>=3.0",
        "sqlalchemy>=1.2",
    ],
    tests_require=[
        "pytest>=3.2.3",
    ]
)
