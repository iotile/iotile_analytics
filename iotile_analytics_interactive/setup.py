"""Setup file for iotile-analytics-interactive."""


from setuptools import setup, find_packages
from version import version


setup(
    name="iotile-analytics-interactive",
    packages=find_packages(exclude=("test",)),
    version=version,
    license="LGPLv3",
    install_requires=[
        "iotile-analytics-core >= 0.1.0",
        "bokeh >= 0.12.15"
    ],
    entry_points={
        'console_scripts': ['analytics-host = iotile_analytics.interactive.scripts.analytics_host:cmdline_main'],
        'iotile_analytics.live_report': ['basic_info = iotile_analytics.interactive.reports.info_report:SourceInfoReport',
                                         'stream_overview = iotile_analytics.interactive.reports.stream_report:StreamOverviewReport']
    },
    include_package_data=True,
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
IOTile Analytics Interactive
----------------------------

This package provides interactive IPython widgets for viewing, plotting and
interacting with iotile.cloud data.  It builds on the core functionality in
iotile-analytics-core.

```
pip install iotile-analytics-interactive
```
"""
)
