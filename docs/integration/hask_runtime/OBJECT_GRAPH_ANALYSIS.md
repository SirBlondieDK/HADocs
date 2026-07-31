# Object Graph Analysis

The documented graph centers on entity, device, area, label, target, service, config-entry, and floor identifiers.

Target extraction provides the strongest documented consistency operation: it explicitly returns referenced entities/devices/areas plus missing devices, areas, floors, and labels. Registry snapshots provide topology, while states provide runtime values. These layers must remain separate.

The official display-entity schema documents entity-to-platform, area, label, and device keys. Device registry concepts document configuration entries, connections, identifiers, area and upstream device, but the official command example does not establish a complete wire schema.

No edge proves operational health. Missing, disabled, unavailable, and unknown states require separate context. See [ENTITY_DEVICE_RELATIONSHIPS.json](ENTITY_DEVICE_RELATIONSHIPS.json).

