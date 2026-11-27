# Maintain the bond-coordinator package

The distribution at this revision is `bond-coordinator` 0.1.0, with
Python compatibility `>=3.11`. This checkout has no `.python-version` pin. Check the declared range when choosing an interpreter.
[Project metadata](../pyproject.toml) declares the package and compatibility.
[The lockfile](../uv.lock) records resolved dependency versions and sources.

## Dependency provenance

- `bond-api` resolves to the vendored copy at `vendor/bond-api`. Its
  [provenance record](../vendor/bond-api/PROVENANCE.json) identifies the
  source revision and records content digests.

## Citation and release records

[Citation metadata](../CITATION.cff), [CodeMeta](../codemeta.json), and
[Zenodo metadata](../.zenodo.json) describe this package. Check the
version fields that are present against the project metadata. A repository
metadata file does not establish that a release has been deposited.

For a documentation review, run `git diff --check` and verify the relative
links added by the change against the tracked checkout. These checks
provide evidence about the documentation and package records.
