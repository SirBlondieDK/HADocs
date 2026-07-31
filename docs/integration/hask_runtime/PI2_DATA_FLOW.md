# PI2 Data Flow

## Current flow

```text
Home Assistant APIs
  -> InstallationCollector
  -> states/config/services/registries
  -> build_indexes
  -> build_model
  -> native analysis and health calculations
  -> reports/API
```

## Required safe flow

```text
Home Assistant explicit integration diagnostic or config-entry signal
  -> native structured observation
  -> generic Consumer Contract normalization
  -> generic matcher evaluation through the PI1 snapshot
  -> canonical evidence
  -> candidate-only causes (confirmed = 0)
  -> advisory recommendations and verification guidance
  -> additive reports/API
```

The first two nodes of the required flow are absent for the approved UniFi and MikroTik connectivity slices. The pipeline must not substitute platform name, entity unavailability, device reachability, or integration-health score for that missing evidence.

