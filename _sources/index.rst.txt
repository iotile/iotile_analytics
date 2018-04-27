Introduction to IOTile Analytics
================================

IOTile Analytics is a python package that is designed for interacting with data
stored in IOTile.cloud using standard Data Science tools like numpy, pandas,
bokeh, matplotlib etc.

You can use it to quickly generate beautiful interactive data visualizations
that are just normal html files and can be shared with anyone and used offline.

For example, here's a complex visualization of the shocks and vibrations
experienced by a package during a trip:

.. image:: images/shipment_overview.png

.. important::

	Make sure to check out the `live interactive demo. <_static/shipment-details/index.html>`_

	Click around and see the graphs change.  Look for anomalies in the data.  Zoom
	in and out of the trip timeline.

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

.. command-output:: analytics-host --help

Next Steps
----------

Check out the :ref:`overview-label` to get a sense of the high level
organization of the package or just to the :ref:`quickstart-label` to see
working examples immediately.
