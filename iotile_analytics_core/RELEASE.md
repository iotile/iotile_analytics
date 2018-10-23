# Release Notes

## 0.5.0

- Add incremental envelope calculation functions to handle accumulating a 
  large number of arrays with smaller memory footprint.
- Refactor threaded http routines to be iotile.cloud agnostic for use with
  ReportUploader in iotile-analytics-interactive
- Add support for Unattended mode in Environment class.  This triggers 
  ProgressBar to not show realtime progress updates but instead to print a
  single summary line with how long each operation took from start to finish.

## 0.4.6

- Add support for Device Data Masks. If user sets a device mask on IOTile Cloud,
  any analysis will automatically respect that mask and not get any data outside
  the mask's datetime range.

## 0.4.5

- Fix envelope calculation function to not have numerical instability when
  working with logarithmic bin spacing.

## 0.4.4

- Fix another issue uploading reports on python 3.  Makes sure to use
  native str objects on both python 2 and python 3.

## 0.4.3

- Fix url posting on python 3 to use correct string object in the url and
  increase test coverage of CloudSession low-level methods.  Fix related bug
  that prevented passing a string on python 3 as payload.

## 0.4.2

- Fix password prompt in python 3 that requires a unicode string.
- Preemptively fix username prompt in python 2 and 3 to use native string
  objects in both settings.

## 0.4.1

- Add support for posting files to s3 and making post requests to iotile.cloud
  rest APIs.
- Refactor thread pool to not create a new pool for every CloudSession instance.

## 0.4.0

- Allow downloading system data as well as user data.
- Refactor data fetching and handling to accommodate data streams that do not
  have metadata information.

## 0.3.3

- Switch source_info to store properties separately so we can productively 
  iterate over properties in a template and show them all to the user.
- Move to using faster df api for stream data download.

## 0.3.2

- Increase compatibility with iotile-analytics-offline.

## 0.3.1

- Break mock_cloud out into python_iotile_cloud for better shareability across
  other projects.  (Issue #24)

## 0.3.0

- Add support for Timeseries Selector that can be used to create day, week and
  month views of multiple data streams. 

## 0.2.5

- Cache session token for use with AnalyticsGroup

## 0.2.4

- Fix minor bug in Datablock Mock function

## 0.2.3

- Enhance Cloud Mock to include data blocks
- Enhance CloudSession to accept an optional token to avoid getting a password

## 0.2.2

- Add channel.fetch_source_info() to fetch data on the Project, Device or DataBlock source object.
  Option to get its properties as well.
- Add docker/dev_dockerfile to build docker image with local changes

## 0.2.1

- Only get event waveforms if they exist

## 0.2.0

- Add CloudChannel to support multiple sources of data for creating Analysis
  Group objects.
- Bugfixes and revisions

## 0.1.1

- Add support for not verifying iotile.cloud's SSL certificate if the user
  explicitly chooses not to verify it.

## 0.1.0

- Initial release with new package names
