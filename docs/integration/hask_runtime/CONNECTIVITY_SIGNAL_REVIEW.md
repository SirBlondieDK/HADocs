# Connectivity Signal Review

No officially documented field satisfies the existing UniFi or MikroTik matcher requirements without inference.

The required fields are an explicit platform-scoped connection test/result and explicit problem signal. States and entity availability are contextual. Registries provide identity/topology. REST API availability tests only Home Assistant itself. Service availability means an action is registered. Events report occurrences. Config-entry lifecycle was observed only through an undocumented command and still has no connection-result field. Diagnostics, Repairs, and System Health were not present as documented external API contracts in the reviewed Developer documentation.

No exact UniFi or MikroTik config-entry/entity platform was observed in the live installation; absence in one installation proves nothing. Connectivity remains `NO_AUTHORITATIVE_SIGNAL_AVAILABLE` for those verticals, while the program-wide conclusion remains `GENERIC_COLLECTOR_REQUIRED` for other safe API opportunities.

