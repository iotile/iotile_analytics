# Introduction

`iotile-analytics-offline` adds support for caching and accessing data from
iotile.cloud while offline.  Data is stored locally on your computer using
pytables and HDF5 for high performance storage.

There is no difference in the way you interact with data online or offline. You
use the same classes and methods and typically do not need to do anything
differently.

## Prerequisites

`iotile-analytics-offline` requires that you have a working copy of the HDF5
file format engine installed.  This is installed automatically be `pip` but can
be downloaded from here if you really want to:

[https://support.hdfgroup.org/downloads/index.html](https://support.hdfgroup.org/downloads/index.html)

## Installation

The easiest way to install is by using PyPI:

```
pip install iotile-analytics-offline
```
