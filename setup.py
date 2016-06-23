"""
Setup script for the time keeper package
"""

import setuptools

with open("README.md") as readme:
    long_description = readme.read()

setuptools.setup(
                 entry_points={"console_scripts": ["worktime = timekeeper.tools.worktime:main",
                                                    "wt = timekeeper.tools.worktime:main",
                                                    "lockwatcher = timekeeper.tools.lockwatcher:main"]},
                 name="timekeeper",
                 version="1.0.1",
                 url="https://github.com/antonopa/timekeeper",
                 packages=["timekeeper", "timekeeper.tools"],
                 description="Command line script and DB class to log work time and overtime",
                 long_description=long_description,
                 license="MIT",
                 author="Alexandros Antonopoulos",
                 author_email="antonopa@gmail.com"
                )

