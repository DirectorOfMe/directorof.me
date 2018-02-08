from setuptools import setup, find_packages

# THIS FILE IS GENERATED, DO NOT EDIT

{% set deps = PKG_DEPS.split(',') %}
setup(
    name="{{ PKG_NAME|trim }}",
    version="{{ PKG_VERSION|trim }}",
    packages=find_packages(),
    install_requires=[
        "pytest>=3.2.3",
        "pytest-runner>=3.0",
        {% for dep in deps %}{% if dep|trim %}"{{ dep|trim }}",{% endif %}
        {% endfor %}
    ],
    tests_require=[
        "pytest>=3.2.3",
        "pytest-cov>=2.5",
    ]
)
