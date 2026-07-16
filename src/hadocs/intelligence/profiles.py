from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProfileKind(str, Enum):
    ACTION = "action"
    EVENT = "event"
    MEASUREMENT = "measurement"
    CONTROL = "control"
    AVAILABILITY = "availability"
    DIAGNOSTIC = "diagnostic"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class EntityProfile:
    kind: ProfileKind
    affects_health: bool
    expected_unknown: bool
    reachability_signal: bool
    event_driven: bool = False
    diagnostic: bool = False
    configuration: bool = False
    reason: str = ""


ACTION_PROFILE = EntityProfile(
    kind=ProfileKind.ACTION,
    affects_health=False,
    expected_unknown=True,
    reachability_signal=False,
    reason="Stateless action entities do not represent persistent device state.",
)

EVENT_PROFILE = EntityProfile(
    kind=ProfileKind.EVENT,
    affects_health=False,
    expected_unknown=True,
    reachability_signal=False,
    event_driven=True,
    reason="Event-driven entities may have no persistent value while idle.",
)

MEASUREMENT_PROFILE = EntityProfile(
    kind=ProfileKind.MEASUREMENT,
    affects_health=True,
    expected_unknown=False,
    reachability_signal=False,
    reason="Measurement entities are expected to provide a value when available.",
)

CONTROL_PROFILE = EntityProfile(
    kind=ProfileKind.CONTROL,
    affects_health=True,
    expected_unknown=False,
    reachability_signal=True,
    reason="Control entities are useful supporting device-health signals.",
)

AVAILABILITY_PROFILE = EntityProfile(
    kind=ProfileKind.AVAILABILITY,
    affects_health=True,
    expected_unknown=False,
    reachability_signal=True,
    reason="Availability entities are authoritative reachability signals.",
)

DIAGNOSTIC_PROFILE = EntityProfile(
    kind=ProfileKind.DIAGNOSTIC,
    affects_health=False,
    expected_unknown=True,
    reachability_signal=False,
    diagnostic=True,
    reason="Diagnostic entities should not drive primary health severity.",
)

CONFIGURATION_PROFILE = EntityProfile(
    kind=ProfileKind.CONFIGURATION,
    affects_health=False,
    expected_unknown=True,
    reachability_signal=False,
    configuration=True,
    reason="Configuration entities do not represent live device health.",
)

UNKNOWN_PROFILE = EntityProfile(
    kind=ProfileKind.UNKNOWN,
    affects_health=False,
    expected_unknown=False,
    reachability_signal=False,
    reason="No specific entity profile matched.",
)
