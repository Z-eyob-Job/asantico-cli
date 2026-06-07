"""Tests for infra LLM routing, offline triage, and audit logging (Phase 3)."""

import json
from pathlib import Path

import pytest

from asantico_cli.domain.triage import TriageResult
from asantico_cli.infra import llm

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "workorders"


@pytest.fixture
def audit_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the config dir (and audit log) to a temporary location."""
    config_dir = tmp_path / ".asantico"
    monkeypatch.setenv("ASANTICO_CONFIG_DIR", str(config_dir))
    return config_dir


def _raw_text(fixture_name: str) -> str:
    """Read the raw_text field from a work order fixture."""
    path = FIXTURE_DIR / fixture_name
    return json.loads(path.read_text(encoding="utf-8"))["raw_text"]


class TestRouteModel:
    """Tests for the pure route_model function."""

    def test_routine_routes_to_haiku(self) -> None:
        """Routine, non-ambiguous cases use the cheaper model."""
        assert llm.route_model("routine", ambiguous=False) == "haiku"

    def test_emergency_routes_to_opus(self) -> None:
        """Emergencies always escalate to the stronger model."""
        assert llm.route_model("emergency", ambiguous=False) == "opus"

    def test_urgent_routes_to_haiku_when_confident(self) -> None:
        """Urgent but confident cases stay on the cheaper model."""
        assert llm.route_model("urgent", ambiguous=False) == "haiku"

    def test_ambiguous_routes_to_opus(self) -> None:
        """Ambiguity escalates regardless of urgency."""
        assert llm.route_model("routine", ambiguous=True) == "opus"
        assert llm.route_model("urgent", ambiguous=True) == "opus"


class TestOfflineTriage:
    """Tests for offline triage_request against the recorded cache."""

    def test_returns_valid_triage_result(self, audit_dir: Path) -> None:
        """Offline triage returns a populated TriageResult from a fixture."""
        result = llm.triage_request(
            _raw_text("wo_03_routine_appliance.json"),
            live=False,
            threshold=0.7,
        )
        assert isinstance(result, TriageResult)
        assert result.urgency == "routine"
        assert result.trade == "appliance"
        assert result.property_name == "Garden"
        assert result.unit == "204"
        assert result.confidence
        assert result.needs_review is False

    def test_emergency_sets_needs_review(self, audit_dir: Path) -> None:
        """An emergency fixture comes back flagged for human review."""
        result = llm.triage_request(
            _raw_text("wo_01_emergency_plumbing.json"),
            live=False,
            threshold=0.7,
        )
        assert result.urgency == "emergency"
        assert result.needs_review is True

    def test_ambiguous_sets_needs_review(self, audit_dir: Path) -> None:
        """A low-confidence fixture comes back flagged for human review."""
        result = llm.triage_request(
            _raw_text("wo_07_ambiguous_noise.json"),
            live=False,
            threshold=0.7,
        )
        assert result.needs_review is True

    def test_pii_restored_for_local_display(self, audit_dir: Path) -> None:
        """Extracted PII fields are restored to real values for the operator."""
        result = llm.triage_request(
            _raw_text("wo_09_heavy_pii_appliance.json"),
            live=False,
            threshold=0.7,
        )
        assert result.unit == "417"
        assert "James O'Brien" in (result.tenant_contact or "")

    def test_missing_cache_entry_raises(self, audit_dir: Path) -> None:
        """Unseen text without a recorded response fails clearly offline."""
        with pytest.raises(RuntimeError, match="No recorded triage response"):
            llm.triage_request("A request never recorded before.", live=False, threshold=0.7)


class TestAuditLog:
    """Tests for the redacted audit log."""

    def test_audit_line_written(self, audit_dir: Path) -> None:
        """One audit line per call is appended with the expected fields."""
        llm.triage_request(
            _raw_text("wo_03_routine_appliance.json"),
            live=False,
            threshold=0.7,
        )
        audit_path = llm.get_audit_log_path()
        lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert set(entry) >= {
            "timestamp",
            "model",
            "prompt_hash",
            "urgency",
            "trade",
            "needs_review",
        }
        assert entry["urgency"] == "routine"
        assert entry["model"] == "haiku"

    def test_audit_log_contains_zero_original_pii(self, audit_dir: Path) -> None:
        """The audit log records redacted text only, never original PII."""
        llm.triage_request(
            _raw_text("wo_09_heavy_pii_appliance.json"),
            live=False,
            threshold=0.7,
        )
        contents = llm.get_audit_log_path().read_text(encoding="utf-8")
        for pii in [
            "James O'Brien",
            "Linda O'Brien",
            "(206) 555-0188",
            "206.555.0190",
            "james.obrien@example.com",
            "417",
        ]:
            assert pii not in contents, pii

    def test_mapping_never_written_to_audit(self, audit_dir: Path) -> None:
        """The restore map is not present in the audit entry."""
        llm.triage_request(
            _raw_text("wo_01_emergency_plumbing.json"),
            live=False,
            threshold=0.7,
        )
        entry = json.loads(llm.get_audit_log_path().read_text(encoding="utf-8").strip())
        assert "mapping" not in entry
        assert "Maria Delgado" not in json.dumps(entry)
        assert "206-555-0142" not in json.dumps(entry)
