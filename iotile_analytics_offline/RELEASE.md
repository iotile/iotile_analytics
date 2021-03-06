# Release Notes

## 0.3.0

- Add support for filtering raw events and change postprocess event signature
  to include raw event data in case you need to filter raw events based on their
  summary data.

## 0.2.3

- Update compatibility with latest iotile-analytics-{core, interactive} changes
  to support streaming report generation.

## 0.2.2

- Adjust offline save format to allow loading files between python major versions.

## 0.2.1

- Fix bug when saving streams that do not have metadata associated with them.
  Now we correctly unserialize them.

## 0.2.0

- Improve saving of hdf5 files when overwriting old files or reading from
  nonexistent ones.  UsageError is now properly raised
- Fix storage of properties to properly handle nulls and add test coverage.
- Store properties separate from source info so that there is no ambiguity
  what a property is.

## 0.1.0

- Initial public release
- Supports saving an AnalysisGroup to an HDF5 file and loading that group back
  from a file later.  Use `.save('<path>', 'hdf5')` to save and use
  `AnalysisGroup.FromSaved('<path>', 'hdf5')` to load.
- Adds `save_hdf5` LiveReport plugin for quickly exporting data to hdf5 from an
  AnalysisGroup using `analytics-host`.