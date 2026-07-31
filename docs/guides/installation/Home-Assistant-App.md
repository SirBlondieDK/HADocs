# Home Assistant App

The Home Assistant App runs the HADocs analysis engine and web interface directly inside Home Assistant.

## Install

1. Open **Settings → Apps → Repositories** in Home Assistant.
2. Add the HADocs repository:

   ```text
   https://github.com/SirBlondieDK/HADocs
   ```

3. Refresh the App Store if HADocs does not appear immediately.
4. Install **HADocs**.
5. Configure the Home Assistant URL and Long-Lived Access Token.
6. Start HADocs.
7. Open the HADocs web interface.
8. Run your first analysis from **Overview**.

## Release channel

The Home Assistant App currently uses `sirblondiedk/hadocs:dev`, the project's preview/development channel. Rebuild or reinstall the app after a new image is published to pull the update.

Persistent data is stored in the mapped `/config`, `/cache`, and `/output` directories.

## HASK Preview

The App exposes `hask_preview_enabled` and `hask_enabled` as separate options;
both default to `false`. When explicitly enabled, the configured
`/config/hask-bundle` must contain a valid read-only consumer bundle. A missing
or corrupt explicit bundle is reported and is not replaced silently. Candidate
evaluation retains its independent database, candidate-evidence, and native
status gates. Preview performs no controller login or network probe and has no
effect on normal analysis or scores.

For the shared product workflow, see the [project README](../../../README.md#web-interface), or return to the [documentation home](../../README.md).
