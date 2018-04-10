# Release Notes

## 0.1.0

- Initial public release
- Supports saving an AnalysisGroup to an HDF5 file and loading that group back
  from a file later.  Use `.save('<path>', 'hdf5')` to save and use
  `AnalysisGroup.FromSaved('<path>', 'hdf5')` to load.
