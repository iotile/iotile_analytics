# Release Notes

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
