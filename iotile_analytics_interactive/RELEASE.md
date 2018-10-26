# Release Notes

## 0.6.0

- Update to bokeh 1.0.0.

## 0.5.1

- Add support for passing an iotile.cloud token on the command line using 
  --token={token}
- Add support for passing a pre-existing report id on the command line using
  --web-push-id={id}

## 0.5.0

- Add support for streaming report generation.  Now there are FileHandler
  classes that can be passed to a LiveReport and handle all of the files 
  produced by that report.  This allows the possibility of streaming those 
  files to a remote server without ever saving them to disk.  This particular
  streaming support is added by the StreamingWebPushHandler class.
- Updates analytics-host to use the new FileHandler functionality to implement
  report bundling and web push.

## 0.4.5

- Fix label of branded archive reports to properly find archive label.

## 0.4.4

- Support uploading generated reports to an existing report record on the cloud

## 0.4.3

- Resolve issue with uploading reports on python 3.

## 0.4.2

- Fix issue with jquery being escaped.

## 0.4.1

- Fix bug when generating reports from archives

## 0.4.0

- Add support for uploading created files to iotile.cloud and linking them
  with a device or archive.
- Add options to analytics_host to upload files and attach them to a device that
  the user has access to.
- Add LiveReport class that includes support for "Action Tables" which are lists
  of links that can be customized by subclasses and are designed to function like
  macros for iotile.cloud, where you specify a list of possible next steps for
  a user and 

## 0.3.0

- Add support for stream_overview report that shows detailed information about
  a specific data stream.
- Add TimeSelectViewer that shows how many data points you have as a function
  of time in a given stream.  This is just an initial implementation.  The 
  long term goal is for it to be a kind of mini-map for stream data showing you
  where in time you have data and letting you quickly select the region you
  want to focus in. 

## 0.2.0

- Switch to Bokeh for visualizations
- Create AnalyticsApp and AnalyticsObject to facilitate integration of Bokeh
  apps with python callbacks running inside of a notebook or jupyter lab.
- Add LiveReport objects that render interactive html documents containing
  graphs and other information.  LiveReports support loading local data using
  a JSONP based callback mechanism that works without needing a web browser.
- Add `analytics-host` command line program that allows you to pick a report
  that you would like to run against an AnalysisGroup and saves the output to
  a file on your computer.
- Add default arch branded report that can be used `BrandedReport` and populates
  the LiveReport template with a pretty header and footer.

## 0.1.1

- Add support for bar charts to BaseViewer

## 0.1.0

- Update Viewer to support Pandas DataFrame arguments

## 0.0.1

- Initial release with new package names
- Includes basic graph viewing functionality
