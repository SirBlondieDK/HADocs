# Legacy Matcher PI2 Executability Assessment

## Result

No legacy matcher is safely executable through normal HADocs scanning today.

### Precise log-pattern exports: `REQUIRES_NATIVE_SIGNAL`

These five exports contain deterministic `contains` or `regex` semantics and an explicit logger scope, but HADocs does not collect Home Assistant or Supervisor logs:

- `mqtt_certificate_verify_failed`
- `recorder_sqlite_corrupt_or_malformed`
- `supervisor_job_blocked_from_execution`
- `template_undefined_error`
- `thread_mdns_error_99`

They could be reconsidered only after a separately approved, privacy-reviewed structured log-event collector. This report does not recommend free-log ingestion as the default PI2 path.

### Rule exports: `REQUIRES_MATCHER_CONTRACT_MIGRATION`

The other 18 legacy rules export claims, inference classification, references, and safety boundaries but no closed required-field list, normalization, conditions, outcomes, platform scope, or canonical evidence target. HADocs must not reconstruct those missing semantics.

The affected rules are:

- `automation_trigger_rate_anomaly`
- `backup_absence_detected`
- `backup_restore_not_verified`
- `container_persistence_unverified`
- `dns_failure_correlated`
- `esphome_reconnect_pattern`
- `matter_commissioning_layered_failure`
- `mqtt_broker_connection_loss`
- `mqtt_entity_unavailability_correlated`
- `persistent_high_disk_usage`
- `recorder_database_write_errors`
- `recorder_growth_without_retention_review`
- `supervisor_job_repeated_failure`
- `template_render_error_detected`
- `thread_border_router_missing`
- `zigbee_interview_repeated_failure`
- `zigbee_multi_device_outage`
- `zigbee_single_device_unavailability_contextual`

Even where HADocs has related entity states or metrics, executing these rules would require local thresholds, correlation windows, grouping, or contextual exclusions absent from Consumer Contract 1.1.0.

## Classification counts

- `PI2_EXECUTABLE_NOW`: 0
- `REQUIRES_MATCHER_CONTRACT_MIGRATION`: 18
- `REQUIRES_NATIVE_SIGNAL`: 5
- `INSUFFICIENT_AUTHORITATIVE_SEMANTICS`: 0 (represented more specifically by migration requirement)
- `OUT_OF_SCOPE`: 0

