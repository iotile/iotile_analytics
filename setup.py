"""Setup file for iotile-analytics.

This is a meta package that just makes sure subpackages are installed with a specific version"""



from setuptools import setup, find_packages

VERSION = "0.1.0"

setup(
    name="iotile-analytics",
    version=VERSION,
    license="LGPLv3",
    install_requires=[
        "iotile-analytics-core == 0.2.0"
    ],
    description="A data science bridge for iotile.cloud",
    author="Arch",
    author_email="info@arch-iot.com",
    url="https://github.com/iotile/iotile_analytics ",
    keywords=[""],
    classifiers=[
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        "Development Status :: 3 - Alpha",
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

This metapackage contains all of the individual packages that make up iotile-analytics
including those that depend on Jupyter, IPython and ipywidgets.  If you want to do an
installation on a background server that does not have interactive capabilities, you
should install the relevant iotile-analytics-* packages directly.

Installation:

```
pip install iotile-analytics
```
"""
)
