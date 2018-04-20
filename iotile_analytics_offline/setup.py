"""Setup file for iotile-analytics-offline."""



from setuptools import setup, find_packages
from version import version

setup(
    name="iotile-analytics-offline",
    packages=find_packages(exclude=("test",)),
    version=version,
    license="LGPLv3",
    install_requires=[
        "iotile-analytics-core >= 0.2.0",
        "tables >= 3.4.2"
    ],
    entry_points={
        'iotile_analytics.save_format': ['hdf5 = iotile_analytics.offline.integration:hdf5_save_factory'],
        'iotile_analytics.load_format': ['hdf5 = iotile_analytics.offline.integration:hdf5_load_factory'],
        'iotile_analytics.live_report': ['save_hdf5 = iotile_analytics.offline.report:SaveOfflineReport']
    },
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
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
    long_description="""\
IOTile Analytics Core
----------------------

IOTile Analytics Core provides classes for pulling data from iotile.cloud into
a standard data science environment.  In particular it natively maps data into
numpy and pandas as appropriate and provides functions to select data.  It
works well with a Jupyter Notebook based analysis environment, through the
functionality can be used in any python environment.

The IOTile Analytics package is broken into multiple parts of which
iotile-analytics-core is one.  You should install the additional parts that you need for
your use cases.

Installation:

```
pip install iotile_analytics
```
"""
)
