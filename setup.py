from setuptools import setup, find_packages

setup(
    name = "draid",

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
        "lark-parser",
        "pygraphviz",
        "pyyaml",
        "pandas",
        "notebook",
        ],

    scripts = [],
    entry_points = {
        'console_scripts': [
            'draid=draid.__main__:console_entry',
        ]
    }
)
