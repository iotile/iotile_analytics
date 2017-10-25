"""Setup file for iotile_analytics."""



from setuptools import setup, find_packages
from version import version

setup(
    name="iotile_analytics",
    packages=find_packages(exclude=("test",)),
    version=version,
    license="LGPLv3",
    install_requires=[
        "future>=0.16.0"
    ],
    description="A data science bridge for iotile.cloud",
    author="Arch",
    author_email="info@arch-iot.com",
    url="https://github.com/iotile/typedargs",
    keywords=[""],
    classifiers=[
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
    long_description="""\
IOTile Analytics
----------------

IOTile Analytics provides classes for pulling data from iotile.cloud into
a standard data science environment.  In particular it natively maps data into
numpy and pandas as appropriate and provides functions to select data.  It
works well with a Jupyter Notebook based analysis environment, through the
functionality can be used in any python environment.

Installation:

```
pip install iotile_analytics
```
"""
)
