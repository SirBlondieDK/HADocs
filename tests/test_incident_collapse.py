from src.hadocs.core.incidents import Incident, collapse_incidents, hidden_incident_count, visible_incidents


def test_mobile_app_collapses_children():
    parent = Incident(
        incident_id="integration:mobile_app",
        title="Integration issue: mobile_app",
        category="integration",
        severity="critical",
        root_cause="mobile_app",
        affected_entities=["a", "b", "c", "d"],
        affected_devices=["Phone 1", "Phone 2"],
        affected_integrations=["mobile_app"],
        estimated_score_gain=8,
        estimated_repair_minutes=10,
    )
    child = Incident(
        incident_id="device:1",
        title="Mobile App device appears offline: Phone 1",
        category="mobile_app_device",
        severity="critical",
        root_cause="Phone 1",
        affected_entities=["a", "b"],
        affected_devices=["Phone 1"],
        affected_integrations=["mobile_app"],
        estimated_score_gain=4,
        estimated_repair_minutes=2,
    )

    collapsed = collapse_incidents([parent, child])

    assert len(collapsed) == 1
    assert collapsed[0].category == "mobile_app_group"
    assert collapsed[0].child_count == 1
    assert collapsed[0].estimated_repair_minutes == 2


def test_visible_incidents_limits_noise():
    incidents = [
        Incident(
            incident_id=f"device:{i}",
            title=f"Device {i}",
            category="physical_device",
            severity="maintenance",
            root_cause=f"Device {i}",
            affected_entities=[str(i)],
            affected_devices=[f"Device {i}"],
            affected_integrations=["mqtt"],
        )
        for i in range(20)
    ]
    collapsed = collapse_incidents(incidents)

    assert len(visible_incidents(collapsed, limit=12)) == 12
    assert hidden_incident_count(collapsed, limit=12) == 8
