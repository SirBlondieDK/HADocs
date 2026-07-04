IGNORED_DOMAINS = {
    "button",
    "update",
    "event",
    "image",
    "notify",
    "conversation",
    "stt",
    "tts",
    "ai_task",
    "weather",
    "zone",
}

IGNORED_ENTITY_PATTERNS = [
    "favorite_current_song",
    "do_not_disturb",
    "power_on_behavior",
    "color_power_on_behavior",
    "last_seen",
    "linkquality",
    "pre_release",
    "create_snapshot",
    "_start",
    "_stop",
    "_restart",
    "_genstart",
    "_reboot",
    "_hibernate",
    "_reset",
    "_shut_down",
    "_shutdown",
    "format_sd_card",
    "manual_alarm_start",
    "manual_alarm_stop",
    "sync_time",
]

CRITICAL_ENTITY_PATTERNS = [
    "homeassistant_status",
    "hp_mini_status",
    "adguard_status",
    "zigbee2mqtt_status",
    "zigbee2mqtt_bridge_connection_state",
    "frigate_status",
    "remote_ui",
    "internet_online",
    "deco_online",
]

PHYSICAL_DOMAINS = {
    "light",
    "switch",
    "sensor",
    "binary_sensor",
    "camera",
    "media_player",
    "device_tracker",
    "lawn_mower",
    "siren",
}

SYSTEM_PLATFORMS = {
    "hassio",
    "hacs",
    "backup",
    "cloud",
    "conversation",
    "stt",
    "tts",
    "openai_conversation",
    "google_generative_ai_conversation",
}
