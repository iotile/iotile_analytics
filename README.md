# IOTile Analytics

[![Build Status](https://travis-ci.org/iotile/iotile_analytics.svg?branch=master)](https://travis-ci.org/iotile/iotile_analytics)

- Core Package: [![PyPI](https://img.shields.io/pypi/v/iotile_analytics.svg?style=plastic)](https://pypi.python.org/pypi/iotile-analytics-core) [![PyPI](https://img.shields.io/pypi/pyversions/iotile_analytics.svg?style=plastic)](https://github.com/iotile/iotile_analytics)
- Interactive Widgets: [![PyPI](https://img.shields.io/pypi/v/iotile_analytics.svg?style=plastic)](https://pypi.python.org/pypi/iotile-analytics-interactive) [![PyPI](https://img.shields.io/pypi/pyversions/iotile_analytics.svg?style=plastic)](https://github.com/iotile/iotile_analytics)

An open-source data science package for interacting with data stored on
iotile.cloud.  

<!-- MarkdownTOC autolink="true" bracket="round"-->

- [Requirements](#requirements)
- [Installation](#installation)
    - [\(optional\) Jupyter Setup](#optional-jupyter-setup)
    - [\(optional\) Interactive Widgets](#optional-interactive-widgets)
    - [\(optional\) Windows Python Installation](#optional-windows-python-installation)
- [Basic Usage](#basic-usage)
- [Documentation](#documentation)

<!-- /MarkdownTOC -->


## Requirements

- Python 2.7+ or Python 3.5+
- Any platform supported by python with all of the required dependencies
- Ideally a working Jupyter installation for analysis though that is not
  required.

This package requires the following standard python data analysis packages:

- numpy
- pandas
- matplotlib

They are installed automatically when you install `iotile_anlytics` but if you
are running on Windows, you may want to download a prebuilt python distribution
since that's easier to install than trying to compile everything.

## Installation

```shell
pip install iotile_analytics
```

### (optional) Jupyter Setup

If you're not familiar with the Jupyter Interactive Computing program, you can
read more about it at [https://jupyter.org](https://jupyter.org/) or you can
install it quickly using:

```
pip install jupyter
```

Running is as simple as:

```
jupyter notebook
```

There is also [Quickstart Guide](https://jupyter.readthedocs.io/en/latest/content-quickstart.html)

### (optional) Interactive Widgets

Some operations can take awhile to complete depending on how much data you have
to fetch from iotile.cloud.  To support showing progress bars in Jupyter
Notebook you need to install [IPyWidgets](https://ipywidgets.readthedocs.io/en/latest/):

```shell
pip install ipywidgets
jupyter nbextension enable --py --sys-prefix widgetsnbextension
```

### (optional) Windows Python Installation

If you are on Windows and don't have a good python interpreter, one potentially
good option would be [Anaconda](https://www.anaconda.com/download/).  It has
prebuilt versions of all of the standard packages.  

## Basic Usage

This package is best used in combination with a Jupyter Notebook for
interactive data analysis using data pulled from iotile.cloud.  

TODO: Add example usage here

## Documentation

TODO: Add link to readthedocs
