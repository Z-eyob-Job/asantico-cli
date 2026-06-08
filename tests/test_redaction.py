"""Tests for the pure PII redaction domain module (Phase 2)."""

import json
from pathlib import Path

from asantico_cli.domain.redaction import redact, restore

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "workorders"


class TestRedact:
    """Tests for the redact function."""

    def test_phone_is_caught(self) -> None:
        """A phone number is replaced with a PHONE token and removed."""
        redacted, mapping = redact("Call the tenant at 206-555-0142 today.")
        assert "206-555-0142" not in redacted
        assert "PHONE_1" in redacted
        assert mapping["PHONE_1"] == "206-555-0142"

    def test_phone_formats_variants(self) -> None:
        """Parenthesized and dotted phone formats are both caught."""
        redacted, mapping = redact("Cell (206) 555-0188 or 206.555.0190.")
        assert "(206) 555-0188" not in redacted
        assert "206.555.0190" not in redacted
        assert mapping["PHONE_1"] == "(206) 555-0188"
        assert mapping["PHONE_2"] == "206.555.0190"

    def test_email_is_caught(self) -> None:
        """An email address is replaced with an EMAIL token and removed."""
        redacted, mapping = redact("Reach me at james.obrien@example.com please.")
        assert "james.obrien@example.com" not in redacted
        assert "EMAIL_1" in redacted
        assert mapping["EMAIL_1"] == "james.obrien@example.com"

    def test_unit_number_is_caught_but_property_kept(self) -> None:
        """The unit number is tokenized while the property name is preserved."""
        redacted, mapping = redact("Dishwasher at Garden unit 204 is broken.")
        assert "unit UNIT_1" in redacted
        assert mapping["UNIT_1"] == "204"
        assert "Garden" in redacted

    def test_name_is_caught_after_cue(self) -> None:
        """A cue-introduced tenant name is tokenized."""
        redacted, mapping = redact("Tenant Maria Delgado reported a leak.")
        assert "Maria Delgado" not in redacted
        assert mapping["NAME_1"] == "Maria Delgado"

    def test_stable_token_for_repeated_value(self) -> None:
        """The same original value maps to the same token on repeat."""
        redacted, mapping = redact(
            "Call 206-555-0142. If no answer, call 206-555-0142 again."
        )
        assert redacted.count("PHONE_1") == 2
        assert "PHONE_2" not in mapping


class TestAdjacentPii:
    """Regression tests for a name immediately adjacent to a phone number."""

    def test_name_then_phone_separate_clean_tokens(self) -> None:
        """Adjacent name and phone each get a single clean token."""
        original = "Tenant Marcus Lee 206-555-0173"
        redacted, mapping = redact(original)
        assert mapping["NAME_1"] == "Marcus Lee"
        assert mapping["PHONE_1"] == "206-555-0173"
        assert "NAME_1" in redacted
        assert "PHONE_1" in redacted
        assert restore(redacted, mapping) == original

    def test_name_directly_followed_by_phone_no_separator(self) -> None:
        """A name directly abutting a phone (no space) still tokenizes cleanly."""
        original = "Tenant Marcus Lee206-555-0173"
        redacted, mapping = redact(original)
        assert mapping["NAME_1"] == "Marcus Lee"
        assert mapping["PHONE_1"] == "206-555-0173"
        assert restore(redacted, mapping) == original

    def test_no_doubled_suffix_token_is_produced(self) -> None:
        """A malformed doubled-suffix token like NAME_1_1 is never produced."""
        for original in [
            "Tenant Marcus Lee 206-555-0173",
            "Tenant Marcus Lee206-555-0173",
            "Tenant Maria Delgado (206) 555-0142",
            "Contact James O'Brien 206.555.0190",
        ]:
            redacted, mapping = redact(original)
            assert "NAME_1_1" not in redacted, original
            assert "NAME_1_1" not in mapping, original
            assert restore(redacted, mapping) == original, original


class TestRestore:
    """Tests for the restore function."""

    def test_exact_round_trip(self) -> None:
        """restore(redact(text)) reproduces the original text exactly."""
        original = (
            "Tenant Maria Delgado at The Meridian unit 312 reports a burst pipe. "
            "Call her at 206-555-0142 or email maria.delgado@example.com."
        )
        redacted, mapping = redact(original)
        assert restore(redacted, mapping) == original

    def test_round_trip_on_all_fixtures(self) -> None:
        """Every work order fixture round-trips exactly through redact/restore."""
        for path in sorted(FIXTURE_DIR.glob("*.json")):
            raw_text = json.loads(path.read_text(encoding="utf-8"))["raw_text"]
            redacted, mapping = redact(raw_text)
            assert restore(redacted, mapping) == raw_text, path.name


class TestNoOriginalPiiSurvives:
    """Verify redacted text leaks no original PII."""

    def test_redacted_text_contains_zero_original_pii(self) -> None:
        """All known PII tokens are absent from the redacted text."""
        original = (
            "Tenant James O'Brien in unit 417 can be reached at (206) 555-0188 "
            "or james.obrien@example.com."
        )
        redacted, _ = redact(original)
        for pii in [
            "James O'Brien",
            "417",
            "(206) 555-0188",
            "james.obrien@example.com",
        ]:
            assert pii not in redacted

    def test_heavy_pii_fixture_is_fully_redacted(self) -> None:
        """wo_09 heavy-PII fixture leaks no original PII after redaction."""
        path = FIXTURE_DIR / "wo_09_heavy_pii_appliance.json"
        raw_text = json.loads(path.read_text(encoding="utf-8"))["raw_text"]
        redacted, mapping = redact(raw_text)

        original_pii = [
            "James O'Brien",
            "Linda O'Brien",
            "(206) 555-0188",
            "206.555.0190",
            "james.obrien@example.com",
            "417",
        ]
        for pii in original_pii:
            assert pii not in redacted, pii

        # The mapping must round-trip the fixture exactly.
        assert restore(redacted, mapping) == raw_text
        # Property name is not PII and should remain visible for triage.
        assert "Clark Roadhouse" in redacted
