# Versioning

HADocs stable release tags use `v<major>.<minor>.<patch>`. Release candidates add
the channel suffix, for example `v0.17.0-rc3`.

Product surfaces display `0.17.0-rc3`, while Python package metadata normalizes
the same release to the PEP 440 form `0.17.0rc3`.

Do not infer release stability from a Docker tag. `sirblondiedk/hadocs:dev` is the current preview/development channel, and no `latest` Docker channel is configured.

Update version metadata consistently across packaging, release notes, and published artifacts as part of the release process.

Return to the [release process](Release-Process.md) or the [documentation home](../README.md).
