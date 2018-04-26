.. _quickstart-label:

5-Minute Quickstart Guide
=========================

Make sure you have everything installed and up to date before running any of the
examples below:

.. code-block:: bash
	
	pip install -U iotile-analytics-core iotile-analytics-interactive iotile-analytics-offline


..  note::

	In the following examples, all of the data referenced will be local to your
	computer.  You will be prompted to download some data files before each
	example so that you can quickly get up to speed with no external
	dependencies.

``iotile-analytics`` works on Python 2.7+ and Python 3.5+.  There is no usage difference
on Python 2 or Python 3.


Generating Live Reports
-----------------------

Live Reports are a key part of IOTile Analytics.  They are static HTML documents
that either embed data and plots or reference local data files that can be
accessed without needing a web server.

.. important::

	Download :download:`thermo_device.hdf5 <data/thermo_device.hdf5>` to use
	as source data and place it in your current working directory.

The quickest way to generate a live report is to use the ``analytics-host`` command
line program that comes with ``iotile-analytics-interactive``.  You can use the 
program to generate reports from datasets that are either stored locally on your
computer or downloaded on the fly from iotile.cloud.

Almost always, the output of ``analytics-host`` is an interactive html+javascript
document embedding graphs, data tables and other widgets to let you scroll through
your data.  Sometimes the output is just plain text or a different binary format.

Python packages you have installed can register LiveReport types with
``analytics-host`` so that you run them from the command line.  Let's see what
reports you have installed:

.. command-output:: analytics-host -l
	:cwd: data

You have several "analysis templates" installed.  You can download data from
iotile.cloud for fast local access (``save_hdf5``), you can print basic_info
about a data source (``basic_info``) and you can create an interactive html
report about a data stream, which a specific time series of data produced
by a device (``stream_overview``).

Let's look at the data source ``thermo_device.hdf5`` that you downloaded.

.. note::

	You always specify the kind of report that you want to generate by
	passing its name using the ``-t`` parameter such as ``-t basic_info``
	or ``-t save_hdf5``.  

	If you want the output saved to a file (which is the typical case),
	you need to specify the output file path using ``-o OUTPUT_FILE_PATH``.

	Most analysis templates require an output file to be specified but several
	simple templates will just display their output on the console if 
	you don't specify an output path.

.. command-output:: analytics-host -t basic_info -c thermo_device.hdf5
	:cwd: data

Here we see that our downloaded data comes from a random device that is
supposed to measure temperature and was named 'Freezer Temperature'.  Note
that we always pass the `-c` parameter so that we don't have to confirm all of
our actions.  Otherwise you will be prompted before actually generating a
report.

You can also see the data streams that the device has by giving an argument to
the report (``-a streams=true``).  We'll see in the next section how to discover
what parameters you can pass and what they do, but for now let's just see the
output.

.. command-output:: analytics-host -t basic_info -c thermo_device.hdf5 -a streams=true
	:cwd: data

Looks at the ``Streams`` section of the command output.  You can see an entry for 
every time series of data that is known about this device as well as how many 
data points they contain.

This report tells us that we have a lot of system data available about this device
and just one user friendly temperature stream named `Temperature`.  Let's view the
temperature data.  Again, we'll look more in depth later at how to configure this
command, for now we just want to look at the report output (which will be saved 
as ``temperature.html`` because we pass ``-o temperature``).

.. command-output:: analytics-host -t stream_overview ./thermo_device.hdf5 -a stream=temp -c -o temperature -a units=Celsius
	:cwd: data
	
You should have a file in your local directory named ``temperature.html``, which
when you open in a browser should look something like this:

.. image:: images/freezer_temp.png

.. important::
	
	Unlike the static image rendered in this documentation, the actual
	``temperature.html`` file you produced is completely dynamic.  Use the tools
	next to each image to pan and zoom around the data, which shows two graphs
	of how often data came in (once per hour) and the actual room temperature
	over a 6 month period.

Take a moment to interact with the report, zoom around the graphs and explore
the data.  You just took your first steps interacting with sensor data using
``iotile-analytics``.

.. note::
	
	If you weren't able to run the command you download :download:`temperature.html <data/temperature.html>`
	and open it locally to see what the command would have generated.


Seeing Report Usage
-------------------

Each LiveReport that you can generate comes with built in documentation
showing how you can use it and what, if any arguments it accepts.  You can
view the help documentation using ``analytics-host -l -t <report_name>``

For example, let's see what arguments are allowed for the ``stream_overview`` report:

.. command-output:: analytics-host -l -t stream_overview
	:cwd: data

There are two components of the help information for a LiveReport.  The first
is just general information about what to expect from this report.  The second
contains any parameters that you can pass in order to adjust the report's output.
Not all reports have parameters and most parameters have sane defaults so it
is safe to not pass anything.

If you want to set a parameter you do it by passing an argument on the command line to ``analytics-host``
of ``-a <parameter_name>=<parameter_value>``.  The parameter is automatically parsed and converted to
the appropriate units as listed in the help text for the LiveReport.  For example, this report takes 
an optional custom linear transformation parameter named ``mdo`` that is specified to be a list of 
3 floating point numbers.  MDO stands for (multiple, divide, offset) and is a list of 3 numbers.

You would pass that on the command line as a string such as ``-a mdo=[1.0,2.0,3.0]``.  If you need to
include a space in the parameter value, make sure to quote it so that the shell does not misinterpret
the value as another argument to the program.  

For example to pass a parameter named ``title`` with a value ``My Report``, you would use:
``-a "title=My Report"``.


Saving Data Offline
-------------------

Any LiveReport can be generated either directly from iotile.cloud by passing
the ``slug`` of the device or archive that you want to use.  A slug is an
alphanumeric identifier that starts with ``d--`` for a device and ``b--`` for
an archive.

If you have data that you wish to download and save, you can use the ``save_hdf5`` report to cache all
data offline.

.. note::

	You will need to login with your iotile.cloud email address and password
	in order to download data from iotile.cloud and you can only access data
	that belongs to devices or archives that you have access to.


For example, let's say you want to download data from device ``d--abcd-0000-5678-1234`` and save it to
a file named ``my-device.hdf5``  You would do:

.. code:: bash

	$ analytics-host -t save_hdf5 d--abcd-0000-5678-1234 -o my-device -c
	Please enter your IOTile.cloud email: user@your-email.com
	Please enter your IOTile.cloud password:
	Rendered report to: my-device.hdf5

See how the final line says ``Rendered report to: my-device.hdf5``.  That is
the offline file that you can use for any live report generation without
needing internet access.  In fact this how we generated the file
``thermo_device.hdf5`` that you used in an earlier tutorial.
