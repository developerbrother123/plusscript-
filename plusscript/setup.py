from setuptools import setup
setup(
    name="plusscript",
    version="1.0",
    scripts=["plusscript.py"],
    entry_points={"console_scripts": ["plusscript = plusscript:main"]},
)