from src.hadocs.core.relationships import build_relationship_graph


class DummyEntity:
    def __init__(self):
        self.entity_id = "light.kitchen"
        self.name = "Kitchen Light"
        self.domain = "light"
        self.platform = "mqtt"
        self.state = "on"
        self.area_id = "kitchen"
        self.device_id = "dev1"
        self.importance = "important"
        self.is_ignored = False


class DummyDevice:
    def __init__(self):
        self.device_id = "dev1"
        self.name = "Kitchen Light"
        self.area_id = "kitchen"
        self.classification = "physical"
        self.entities = [DummyEntity()]


class DummyIntegration:
    def __init__(self):
        self.platform = "mqtt"
        self.entities = [DummyEntity()]
        self.devices = [DummyDevice()]


class DummyModel:
    def __init__(self):
        self.entities = {"light.kitchen": DummyEntity()}
        self.devices = {"dev1": DummyDevice()}
        self.integrations = {"mqtt": DummyIntegration()}


def test_relationship_graph_builds():
    graph = build_relationship_graph(DummyModel())
    assert "light.kitchen" in graph.entities
    assert "dev1" in graph.devices
    assert "mqtt" in graph.integrations
