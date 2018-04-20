Introduction to IOTile Analytics
================================

IOTile Analytics is a python package that is designed for interacting with data
stored in IOTile.cloud using standard Data Science tools like numpy, pandas,
bokeh, matplotlib etc.

This section serves as a basic introduction to the fundamental concepts and
classes of IOTile Analytics as well as some example usage.

If you are looking for the quickest way to get something working and don't want
any other details, try the :ref:`quickstart-label`.

.. toctree::
  :hidden:

  overview
  quickstart
  api


Prerequisites
-------------

You need to have either Python 2.7 or Python 3.5+ installed.  

Everything else will be downloaded and installed automatically from ``pip``.
Although you don't need to explicitly install anything, the following packages
are used heavily in ``iotile_analytics`` so you may want to check them out:

===========================================================  ======================================================
Package                                                      Description                                           
===========================================================  ======================================================
`Bokeh <https://bokeh.pydata.org/en/latest/>`_               Interactive data visualization using html documents.  
`Pandas <https://pandas.pydata.org/pandas-docs/stable/>`_    Timeseries analysis tools                             
`Numpy <https://docs.scipy.org/doc/>`_                       Numerical data analysis in Python.                    
===========================================================  ======================================================

Installation
------------

A basic installation just needs three packages pip installed into your
environment.

.. code-block:: bash

	pip install -U iotile-analytics-core iotile-analytics-interactive iotile-analytics-offline

To check that everything is working, make sure you can access the ``analytics-host``
application.

.. code-block:: bash

	$ analytics-host --help
	usage: analytics-host [-h] [-v] [-u USER] [-n] [-p PASSWORD] [-o OUTPUT]
	                      [-t REPORT] [-l] [-b] [-d DOMAIN]
	                      [analysis_group]

	Generate a LiveReport from data stored locally or in iotile.cloud.

	positional arguments:
	  analysis_group        The slug or path of the object you want to generate a
	                        report on

	optional arguments:
	  -h, --help            show this help message and exit
	  -v, --verbose         Increase logging level (goes error, warn, info, debug)
	  -u USER, --user USER  Your iotile.cloud user name.
	  -n, --no-verify       Do not verify the SSL certificate of iotile.cloud
	  -p PASSWORD, --password PASSWORD
	                        Your iotile.cloud password. If not specified it will
	                        be prompted when needed.
	  -o OUTPUT, --output OUTPUT
	                        The output path that you wish to save the report at.
	  -t REPORT, --report REPORT
	                        The name of the report to generate
	  -l, --list            List all known report types without running one
	  -b, --bundle          Bundle the rendered output into a zip file
	  -d DOMAIN, --domain DOMAIN
	                        Domain to use for remote queries, defaults to
	                        https://iotile.cloud


Next Steps
----------

Check out the :ref:`overview-label` to get a sense of the high level
organization of the package or just to the :ref:`quickstart-label` to see
working examples immediately.
