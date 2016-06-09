"""
Setup script for the time keeper package
"""

import setuptools

with open("README.md") as readme:
    long_description = readme.read()

setuptools.setup(
                 entry_points={"console_scripts": ["worktime = worktime:main",
                                                    "wt = worktime:main",
                                                    "lockwatcher = lockwatcher:main"]},
                 name="timekeeper",
                 version="1.0",
                 url="https://github.com/antonopa/timekeeper",
                 packages=["timekeeper"],
                 package_data={"timekeeper":["./README.md"]},
                 py_modules=['worktime', 'lockwatcher'],
                 description="Command line script and DB class to log work time and overtime",
                 long_description=long_description,
                 license="MIT",
                 author="Alexandros Antonopoulos",
                 author_email="antonopa@gmail.com"
                )

