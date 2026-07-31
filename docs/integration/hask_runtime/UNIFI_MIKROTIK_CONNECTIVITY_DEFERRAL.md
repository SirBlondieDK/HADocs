# UniFi and MikroTik Connectivity Deferral

| Matcher | Contract valid | Exported | Reference consumer validated | HADocs native signal | PI2 runtime status |
|---|---:|---:|---:|---:|---|
| `unifi_controller_connectivity_failure` | true | true | true | false | `deferred` |
| `mikrotik_api_connectivity_failure` | true | true | true | false | `deferred` |

The matchers are not defective. This is a producer-side coverage gap.

Deferral is required because config-entry lifecycle is not a connection-test result; diagnostics and System Health are integration-specific; Repairs has no standardized connectivity contract; entity availability is not a controller/API result; and platform identity alone is insufficient.

Both contracts and all their fixtures remain unchanged.

