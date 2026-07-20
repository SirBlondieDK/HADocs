# Explain Engine

The Explain Engine turns technical root causes into plain-language explanations.

## Goal

HADocs should not only say what is wrong.

It should help users understand why it matters and what to try first.

## Example

Technical:

```text
Integration issue: mqtt
77 affected entities
```

Human explanation:

```text
MQTT is a message system used by many Home Assistant devices.
If MQTT or Zigbee2MQTT has a problem, many lights, sensors or switches may appear unavailable at the same time.
Start by checking the MQTT broker and Zigbee2MQTT bridge before troubleshooting each device.
```

## First supported topics

- mobile_app
- mqtt
- zigbee2mqtt
- hassio
- wled
- frigate
- tapo_control
- icloud
- tuya
- shelly
- wiz
- missing_area
