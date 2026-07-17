from dataclasses import dataclass
from enum import Enum

class IntegrationBehavior(str, Enum):
    LOCAL="local"
    CLOUD="cloud"
    HYBRID="hybrid"

@dataclass(frozen=True)
class IntegrationProfile:
    platform:str
    behavior:IntegrationBehavior
    supports_sleeping_devices:bool=False
    uses_event_entities:bool=False
    has_bridge:bool=False
    bridge_entity_patterns:tuple[str,...]=()
    availability_patterns:tuple[str,...]=()
    notes:tuple[str,...]=()

PROFILES={
    "mqtt":IntegrationProfile(
        platform="mqtt",
        behavior=IntegrationBehavior.LOCAL,
        has_bridge=True,
        availability_patterns=("binary_sensor.*_online","sensor.*_status"),
        notes=("MQTT birth/will and availability are stronger evidence than unknown entity states.",)
    ),
    "zigbee2mqtt":IntegrationProfile(
        platform="zigbee2mqtt",
        behavior=IntegrationBehavior.LOCAL,
        supports_sleeping_devices=True,
        has_bridge=True,
        bridge_entity_patterns=("sensor.zigbee2mqtt_bridge_*",),
        notes=("Sleeping battery devices are expected.","Bridge status outweighs RSSI/linkquality.")
    ),
    "zwave_js":IntegrationProfile(
        platform="zwave_js",
        behavior=IntegrationBehavior.LOCAL,
        supports_sleeping_devices=True,
        notes=("Sleeping is healthy. Dead is authoritative.",)
    ),
    "mobile_app":IntegrationProfile(
        platform="mobile_app",
        behavior=IntegrationBehavior.HYBRID,
        notes=("Retired phones become maintenance after long staleness.",)
    ),
    "frigate":IntegrationProfile(
        platform="frigate",
        behavior=IntegrationBehavior.LOCAL,
        uses_event_entities=True,
        notes=("Event entities may legitimately be idle.",)
    ),
    "onvif":IntegrationProfile(
        platform="onvif",
        behavior=IntegrationBehavior.LOCAL,
        uses_event_entities=True,
        notes=("Motion/event entities often stay unknown until triggered.",)
    ),
    "smartthings":IntegrationProfile(
        platform="smartthings",
        behavior=IntegrationBehavior.CLOUD,
        notes=("Cloud outages affect many entities simultaneously.",)
    ),
}

def get_integration_profile(platform:str)->IntegrationProfile:
    return PROFILES.get(platform, IntegrationProfile(platform=platform, behavior=IntegrationBehavior.LOCAL))
