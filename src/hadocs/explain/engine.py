from dataclasses import dataclass


@dataclass
class Explanation:
    title: str
    what_it_means: str
    why_it_matters: str
    what_to_try_first: list[str]


EXPLANATIONS = {
    "mobile_app": Explanation(
        title="Mobile App devices appear offline",
        what_it_means="One or more phones, tablets or wall displays running the Home Assistant Companion App are not currently reporting normally.",
        why_it_matters="A single offline mobile device can create many unavailable sensors, such as battery, Wi-Fi, charging and activity sensors.",
        what_to_try_first=[
            "Open the Home Assistant Companion App on the affected device.",
            "Make sure the device is connected to Wi-Fi.",
            "Check that the app can reach Home Assistant.",
            "Restart or refresh the app if needed.",
        ],
    ),
    "mqtt": Explanation(
        title="MQTT or Zigbee2MQTT may need attention",
        what_it_means="MQTT is a message system used by many Home Assistant devices and integrations. Zigbee2MQTT also uses MQTT.",
        why_it_matters="If MQTT or Zigbee2MQTT has a problem, many lights, sensors and switches may appear unavailable at the same time.",
        what_to_try_first=[
            "Check that the Mosquitto broker is running.",
            "Check that Zigbee2MQTT is running.",
            "Check the Zigbee coordinator USB connection.",
            "Restart Zigbee2MQTT before troubleshooting every single device.",
        ],
    ),
    "zigbee2mqtt": Explanation(
        title="Zigbee2MQTT may need attention",
        what_it_means="Zigbee2MQTT connects Zigbee devices to Home Assistant through MQTT.",
        why_it_matters="If Zigbee2MQTT or the coordinator is unavailable, many Zigbee devices can appear offline.",
        what_to_try_first=[
            "Check the Zigbee2MQTT service.",
            "Check the coordinator USB device.",
            "Check MQTT broker status.",
            "Restart Zigbee2MQTT if needed.",
        ],
    ),
    "hassio": Explanation(
        title="Home Assistant add-ons may need attention",
        what_it_means="Some Home Assistant Supervisor or add-on entities are unavailable.",
        why_it_matters="Add-ons can expose multiple status and version entities. If an add-on is stopped, several entities may become unavailable.",
        what_to_try_first=[
            "Open Home Assistant Settings.",
            "Go to Add-ons.",
            "Check whether the affected add-ons are running.",
            "Restart only the affected add-on if needed.",
        ],
    ),
    "wled": Explanation(
        title="WLED controller may be offline",
        what_it_means="A WLED controller or one of its segments is not reporting normally.",
        why_it_matters="WLED exposes many entities for effects, palettes, brightness, speed and segments. One offline controller can create many unavailable entities.",
        what_to_try_first=[
            "Check whether the WLED controller has power.",
            "Open the WLED web interface if available.",
            "Check Wi-Fi connection.",
            "Restart the controller if needed.",
        ],
    ),
    "frigate": Explanation(
        title="Frigate or camera streams may need attention",
        what_it_means="Frigate or one or more camera-related entities are not reporting normally.",
        why_it_matters="If Frigate, camera streams or detector services have issues, multiple camera and detection sensors can become unavailable.",
        what_to_try_first=[
            "Open the Frigate interface.",
            "Check whether Frigate is running.",
            "Check camera streams.",
            "Check Coral/VAAPI detector status if used.",
        ],
    ),
    "tapo_control": Explanation(
        title="Tapo camera or doorbell may need attention",
        what_it_means="A Tapo device or related camera entities are unavailable.",
        why_it_matters="Camera integrations often expose many storage, detection and stream entities.",
        what_to_try_first=[
            "Check whether the device has power.",
            "Check whether the device is reachable in the Tapo app.",
            "Check Wi-Fi connection.",
            "Restart the device if needed.",
        ],
    ),
    "icloud": Explanation(
        title="iCloud tracking may need attention",
        what_it_means="One or more Apple devices are not reporting normally through iCloud.",
        why_it_matters="iCloud tracking can create unavailable device trackers or battery sensors when devices are offline, sleeping or not reachable.",
        what_to_try_first=[
            "Check whether the Apple device is online.",
            "Check iCloud integration status.",
            "Check whether two-factor authentication or login is required.",
        ],
    ),
    "tuya": Explanation(
        title="Tuya cloud device may need attention",
        what_it_means="A Tuya device is not reporting normally.",
        why_it_matters="Tuya devices depend on cloud and local network availability depending on setup.",
        what_to_try_first=[
            "Check the Tuya/Smart Life app.",
            "Check whether the device has power.",
            "Check Wi-Fi connection.",
            "Reload the Tuya integration if needed.",
        ],
    ),
    "shelly": Explanation(
        title="Shelly device may need attention",
        what_it_means="A Shelly device is not reporting normally.",
        why_it_matters="Shelly devices are often used for important switches, relays and power monitoring.",
        what_to_try_first=[
            "Check whether the Shelly device has power.",
            "Open the Shelly web interface.",
            "Check Wi-Fi signal.",
            "Restart the device if needed.",
        ],
    ),
    "wiz": Explanation(
        title="WiZ light may need attention",
        what_it_means="A WiZ light is not reporting normally.",
        why_it_matters="WiZ bulbs can expose signal, power and effect entities in addition to the light itself.",
        what_to_try_first=[
            "Check whether the bulb has power.",
            "Check Wi-Fi connection.",
            "Try controlling it from the WiZ app.",
            "Power cycle the bulb if needed.",
        ],
    ),
    "missing_area": Explanation(
        title="Some devices are missing an area",
        what_it_means="Some physical devices are not assigned to a room/area in Home Assistant.",
        why_it_matters="Area assignments make documentation, dashboards and future relationship analysis much easier to understand.",
        what_to_try_first=[
            "Open Home Assistant Settings.",
            "Go to Devices & Services.",
            "Assign missing devices to the correct room/area.",
        ],
    ),
}

EXPLANATIONS["mobile_app_group"] = EXPLANATIONS["mobile_app"]


def explain_key(key: str) -> Explanation:
    key = (key or "").lower()
    return EXPLANATIONS.get(
        key,
        Explanation(
            title="This root cause needs attention",
            what_it_means="HADocs found related unavailable or unknown entities.",
            why_it_matters="Related symptoms often point to one device, integration or configuration area that should be checked first.",
            what_to_try_first=[
                "Open the affected integration in Home Assistant.",
                "Check whether affected devices are powered and connected.",
                "If the device was removed intentionally, clean it up in Home Assistant.",
            ],
        ),
    )


def explain_incident(incident) -> dict:
    key = ""
    if getattr(incident, "affected_integrations", None):
        key = incident.affected_integrations[0]
    if getattr(incident, "category", "") == "mobile_app_group":
        key = "mobile_app_group"
    if getattr(incident, "category", "") == "missing_area":
        key = "missing_area"

    explanation = explain_key(key)

    return {
        "title": explanation.title,
        "what_it_means": explanation.what_it_means,
        "why_it_matters": explanation.why_it_matters,
        "what_to_try_first": explanation.what_to_try_first,
    }
