# Home Assistant Companion Connectivity Contract Assessment

## Assessment

Technically possible, but not recommended as the default unblock.

A companion integration could expose a local typed result only when the owning integration supplies or explicitly authorizes a connection test. Credentials could remain in Home Assistant and output could distinguish disabled, authentication, setup, and connectivity states.

The main risks are substantial:

- Home Assistant integrations do not share a standard connection-test interface;
- adapters would be integration-specific and version-sensitive;
- active tests require explicit opt-in, permissions, rate limits, and side-effect analysis;
- a generic wrapper around entity availability or config-entry state would merely relocate inference;
- reverse engineering vendor APIs would create an unacceptable maintenance and security burden;
- diagnostics payloads require strict allowlists and stable versioned contracts.

The track becomes credible only with an integration-owned typed protocol, explicit test execution, stable result semantics, redacted metadata, and no failed-layer inference. It should be governed as a separate Home Assistant integration project, not hidden inside PI2.

