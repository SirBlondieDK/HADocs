# Release process

Releases are prepared from a clean working tree after tests and platform checks pass.

1. Confirm the intended version and scope.
2. Run the complete test suite.
3. Verify affected Home Assistant App, Docker, and Windows workflows.
4. Update `CHANGELOG.md`, `ROADMAP.md`, and relevant documentation.
5. Complete the [release checklist](Release-Checklist.md).
6. Create and push the release tag.
7. Confirm GitHub Actions completes successfully.
8. Publish the GitHub Release and attach the expected artifacts.

Do not publish credentials, private reports, caches, or local configuration in source archives or release artifacts.

See the [versioning guide](Versioning.md) and [release checklist](Release-Checklist.md), or return to the [documentation home](../README.md).
