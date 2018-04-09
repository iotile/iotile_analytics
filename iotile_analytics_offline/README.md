# Introduction

`iotile-analytics-offline` adds support for caching and accessing data from
iotile.cloud while offline.  Data is stored locally on your computer using
pytables and HDF5 for high performance storage.

There is no difference in the way you interact with data online or offline. You
use the same classes and methods and typically do not need to do anything
differently.

## Prerequisites

`iotile-analytics-offline` requires that you have a working copy of the HDF5
file format engine installed.  This cannot be installed using `pip` but can
be downloaded from:

[https://support.hdfgroup.org/downloads/index.html](https://support.hdfgroup.org/downloads/index.html)

Once you install HDF5 using the appropriate installer for your platform,
`iotile-analytics-offline` should work.  Make sure you install the correct
32 or 64 bit version that matches the python version that you are using.

## Installation

The easiest way to install is by using PyPI:

```
pip install iotile-analytics-offline
```
