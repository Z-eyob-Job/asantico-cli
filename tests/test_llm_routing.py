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


class TestExtractJsonObject:
    """Tests for the pure extract_json_object helper (live path parsing).

    The helper is exercised offline with no API call.
    """

    EXPECTED = {
        "urgency": "routine",
        "trade": "appliance",
        "property_name": "Garden",
        "unit": "UNIT_1",
        "tenant_contact": None,
        "issue_summary": "Dishwasher not draining",
        "confidence": {"urgency": 0.9, "trade": 0.88},
    }

    def _payload(self) -> str:
        return json.dumps(self.EXPECTED)

    def test_bare_json(self) -> None:
        """A bare JSON object parses directly."""
        assert llm.extract_json_object(self._payload()) == self.EXPECTED

    def test_json_fence(self) -> None:
        """JSON wrapped in a ```json code fence parses to the same dict."""
        fenced = f"```json\n{self._payload()}\n```"
        assert llm.extract_json_object(fenced) == self.EXPECTED

    def test_plain_fence(self) -> None:
        """JSON wrapped in a plain ``` code fence parses to the same dict."""
        fenced = f"```\n{self._payload()}\n```"
        assert llm.extract_json_object(fenced) == self.EXPECTED

    def test_prose_preamble(self) -> None:
        """JSON with leading and trailing prose parses to the same dict."""
        wrapped = (
            "Sure, here is the triage result you asked for:\n"
            f"{self._payload()}\n"
            "Let me know if you need anything else."
        )
        assert llm.extract_json_object(wrapped) == self.EXPECTED

    def test_fence_and_preamble_combined(self) -> None:
        """Prose plus a fenced block still parses to the same dict."""
        combined = f"Here you go:\n```json\n{self._payload()}\n```\nThanks."
        assert llm.extract_json_object(combined) == self.EXPECTED

    def test_unparseable_raises_clear_error(self) -> None:
        """A non-JSON response raises a clear RuntimeError with a preview."""
        garbage = "I cannot help with that request right now."
        with pytest.raises(RuntimeError) as excinfo:
            llm.extract_json_object(garbage)
        message = str(excinfo.value)
        assert "Could not parse JSON" in message
        assert "I cannot help" in message

    def test_non_object_json_raises(self) -> None:
        """A JSON array (non-object) raises a clear RuntimeError."""
        with pytest.raises(RuntimeError, match="non-object JSON"):
            llm.extract_json_object("[1, 2, 3]")


class TestResultFromResponseCoercion:
    """Tests that string fields are coerced to strings at the model boundary.

    These run offline with no API call. They guard the live path where a model
    may return a nested object or list for a field the schema expects flat.
    """

    def _base(self) -> dict:
        return {
            "urgency": "routine",
            "trade": "appliance",
            "property_name": "Garden",
            "unit": "UNIT_1",
            "issue_summary": "Dishwasher not draining",
            "confidence": {"urgency": 0.9},
        }

    def test_tenant_contact_as_dict_is_flattened(self) -> None:
        """A dict tenant_contact flattens to a comma joined string."""
        data = {**self._base(), "tenant_contact": {"name": "NAME_1", "phone": "PHONE_1"}}
        result = llm._result_from_response(data)
        assert isinstance(result.tenant_contact, str)
        assert result.tenant_contact == "NAME_1, PHONE_1"

    def test_tenant_contact_as_list_is_flattened(self) -> None:
        """A list tenant_contact flattens to a comma joined string."""
        data = {**self._base(), "tenant_contact": ["NAME_1", "PHONE_1", "EMAIL_1"]}
        result = llm._result_from_response(data)
        assert isinstance(result.tenant_contact, str)
        assert result.tenant_contact == "NAME_1, PHONE_1, EMAIL_1"

    def test_string_field_stays_string(self) -> None:
        """A normal string field passes through unchanged."""
        data = {**self._base(), "tenant_contact": "NAME_1"}
        result = llm._result_from_response(data)
        assert result.tenant_contact == "NAME_1"

    def test_none_optional_field_stays_none(self) -> None:
        """A missing optional field stays None."""
        data = self._base()
        result = llm._result_from_response(data)
        assert result.tenant_contact is None

    def test_unit_as_int_is_coerced(self) -> None:
        """A numeric unit is coerced to a string."""
        data = {**self._base(), "unit": 204}
        result = llm._result_from_response(data)
        assert result.unit == "204"

    def test_nested_dict_field_does_not_break_restore(self) -> None:
        """A coerced field of tokens still round-trips through restore."""
        data = {**self._base(), "tenant_contact": {"name": "NAME_1", "phone": "PHONE_1"}}
        result = llm._result_from_response(data)
        mapping = {"NAME_1": "Maria Delgado", "PHONE_1": "206-555-0142"}
        restored = llm._restore_result(result, mapping)
        assert restored.tenant_contact == "Maria Delgado, 206-555-0142"

    def test_flatten_helper_handles_scalar_dict_list(self) -> None:
        """The flatten helper handles scalars, dicts, and lists."""
        assert llm._flatten_to_str("x") == "x"
        assert llm._flatten_to_str(204) == "204"
        assert llm._flatten_to_str({"a": "1", "b": "2"}) == "1, 2"
        assert llm._flatten_to_str(["1", "2"]) == "1, 2"

    def test_restore_result_leaves_non_string_untouched(self) -> None:
        """_restore_result does not call .replace on a non-string field."""
        result = TriageResult(
            urgency="routine",
            trade="appliance",
            property_name="Garden",
            unit={"raw": "204"},  # type: ignore[arg-type]
            tenant_contact=None,
            issue_summary="Issue",
            confidence={},
        )
        restored = llm._restore_result(result, {})
        assert restored.unit == {"raw": "204"}
