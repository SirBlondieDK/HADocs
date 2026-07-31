# Config Entry Analysis

No external config-entry list/lifecycle command was found in the reviewed official Developer API documentation. A live `config_entries/get` response was structurally observed on Core 2026.7.3, but it is therefore `OBSERVED_UNDOCUMENTED` for this program.

Observed fields included entry/domain identity, lifecycle state, disabled state, reason/translation metadata, timestamps, feature flags and support capabilities. None included an explicit connection test or standardized `connection_result`.

Even if the command becomes officially documented, `loaded`, `setup_error`, and `setup_retry` remain lifecycle facts, not connectivity outcomes. Reasons and translation keys are integration-specific. Authentication, setup, disabled, and connectivity states cannot be safely collapsed.

