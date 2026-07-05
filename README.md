# HADocs

**Home Assistant Documentation & Analysis**

HADocs is a read-only Smart Home Intelligence tool for Home Assistant.

## New in v0.9.0

v0.9.0 introduces the **Incident Collapse Engine**.

Previous versions could find root causes, but large installations could still show too many incidents. v0.9.0 groups related symptoms into a clearer hierarchy.

Example:

```text
Mobile App

3 affected devices
176 affected entities
Estimated fix: 2 minutes

Devices:
- Sebastian Wall Display
- Sofia Wall Display
- Tabet Stue
```

Instead of showing the integration and every device as separate top-level problems, HADocs now shows one parent incident with child details.

## Safety

HADocs is read-only.

It does not call services, change entities, edit automations, modify dashboards, or send commands to devices.
