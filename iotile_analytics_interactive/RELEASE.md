# Release Notes

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
