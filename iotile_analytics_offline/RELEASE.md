# Release Notes

## HEAD

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