from setuptools import setup, find_packages

setup(
    name = "exp",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = [
        "rdflib",
        "owlready2",
        "sparqlwrapper",
        "networkx",
        "pyswip",
        "coloredlogs",
        ],

    scripts = [],
    entry_points = {
        'console_scripts': [
        ]
    }
)
