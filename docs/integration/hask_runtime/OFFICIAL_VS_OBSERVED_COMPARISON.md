# Official vs Observed Comparison

`DOCUMENTED_AND_OBSERVED` confirms only that the documented operation responded with a compatible outer structure on Core 2026.7.3.

Observed extensions such as `last_reported`, additional config fields, detailed full-registry fields, and config-entry lifecycle fields are not promoted beyond official documentation. They are version-tagged structural observations.

Documented but deliberately not observed includes history, logbook, error log, camera data, calendar-event content, subscriptions, validation operations, and every mutating or authentication capability. Reasons include privacy, side effects, required caller input, or absence of a safe test target.

Observed but not independently documented commands are catalogued separately and excluded from the 50-capability denominator. `repairs/issues` failed as unknown and is not an observed capability.

