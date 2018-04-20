# Release Notes

## HEAD

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
