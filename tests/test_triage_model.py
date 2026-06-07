"""Tests for the pure triage domain model (Phase 1)."""

from asantico_cli.domain.triage import TriageResult, should_escalate


def _routine_result(**overrides: object) -> TriageResult:
    """Build a clean routine TriageResult with high confidence for all fields."""
    base = TriageResult(
        urgency="routine",
        trade="appliance",
        property_name="Garden",
        unit="204",
        tenant_contact="tenant",
        issue_summary="Dishwasher not draining fully",
        confidence={
            "urgency": 0.95,
            "trade": 0.92,
            "property_name": 0.98,
            "unit": 0.9,
        },
        needs_review=False,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


class TestShouldEscalate:
    """Tests for the should_escalate escalation rule."""

    def test_escalates_on_emergency(self) -> None:
        """An emergency always escalates, even with high confidence."""
        result = _routine_result(
            urgency="emergency",
            confidence={"urgency": 0.99, "trade": 0.99},
        )
        assert should_escalate(result, threshold=0.7) is True

    def test_escalates_on_low_confidence(self) -> None:
        """Any field below the threshold forces escalation."""
        result = _routine_result(
            confidence={"urgency": 0.95, "trade": 0.40, "unit": 0.9},
        )
        assert should_escalate(result, threshold=0.7) is True

    def test_no_escalation_on_clean_routine(self) -> None:
        """A routine case with all confidences above the threshold stays put."""
        result = _routine_result()
        assert should_escalate(result, threshold=0.7) is False

    def test_threshold_boundary_is_not_low(self) -> None:
        """A confidence exactly at the threshold does not escalate."""
        result = _routine_result(confidence={"urgency": 0.7, "trade": 0.7})
        assert should_escalate(result, threshold=0.7) is False
