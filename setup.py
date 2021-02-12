#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

requirements = [
    "parse",
    "pint",
    "numpy",
]

setup(
    author="Henrik Finsberg",
    author_email="henriknf@simula.no",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    description="Tool for parsing information from filenames",
    entry_points={"console_scripts": ["mps_data_parser=mps_data_parser.scripts:main"]},
    install_requires=requirements,
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="mps_data_parser",
    name="mps_data_parser",
    packages=find_packages(include=["mps_data_parser", "mps_data_parser.*"]),
    test_suite="tests",
    url="https://github.com/finsberg/mps_data_parser",
    version="0.1.0",
    project_urls={
        "Documentation": "https://mps-data-parser.readthedocs.io.",
        "Source": "https://github.com/finsberg/mps_data_parser",
    },
    zip_safe=False,
)
