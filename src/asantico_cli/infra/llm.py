"""LLM client, model routing, offline triage cache, and audit logging.

This is the only module that talks to the LLM. The domain layer stays pure;
all network and I/O for triage live here.

Routing controls cost: routine work goes to the cheaper model, while
emergencies and ambiguous cases escalate to the stronger model. Grading runs
offline against a recorded fixtures cache keyed by a hash of the redacted text,
so no API key is required. Every call appends one redacted audit line; the PII
restore map is never written to disk.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from asantico_cli.domain.redaction import redact, restore
from asantico_cli.domain.triage import Trade, TriageResult, Urgency, should_escalate
from asantico_cli.infra.config import ensure_config_dir, get_config_dir

MODEL_HAIKU = "haiku"
MODEL_OPUS = "opus"

_RESULT_STRING_FIELDS = ("property_name", "unit", "tenant_contact", "issue_summary")


def route_model(urgency: Urgency, ambiguous: bool) -> str:
    """Select the model for a request based on urgency and ambiguity.

    Routine, confident cases use the cheaper model; emergencies and ambiguous
    cases escalate to the stronger model.

    Args:
        urgency: The classified urgency level.
        ambiguous: True if any field confidence is below the threshold.

    Returns:
        "haiku" for routine confident cases, "opus" for emergency or ambiguous.
    """
    if urgency == "emergency" or ambiguous:
        return MODEL_OPUS
    return MODEL_HAIKU


def prompt_hash(redacted_text: str) -> str:
    """Compute the stable cache and audit key for redacted text.

    Args:
        redacted_text: Text that has already passed through redaction.

    Returns:
        A hex SHA-256 digest of the redacted text.
    """
    return hashlib.sha256(redacted_text.encode("utf-8")).hexdigest()


def get_triage_cache_dir() -> Path:
    """Return the directory holding recorded offline triage responses.

    Honors the ASANTICO_TRIAGE_CACHE environment variable, otherwise defaults
    to the repository fixtures cache so grading runs without an API key.

    Returns:
        Path to the triage cache directory.
    """
    override = os.environ.get("ASANTICO_TRIAGE_CACHE")
    if override:
        return Path(override)
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "tests" / "fixtures" / "triage_cache"


def get_audit_log_path() -> Path:
    """Return the path to the triage audit log (~/.asantico/triage_audit.jsonl).

    Returns:
        Path to the audit log file inside the config directory.
    """
    return get_config_dir() / "triage_audit.jsonl"


def _result_from_response(data: dict[str, Any]) -> TriageResult:
    """Build a TriageResult from a parsed model or cache response.

    Args:
        data: Parsed JSON with triage fields.

    Returns:
        A TriageResult with needs_review left at its default of False.
    """
    confidence = {k: float(v) for k, v in dict(data.get("confidence", {})).items()}
    urgency: Urgency = data["urgency"]
    trade: Trade = data["trade"]
    return TriageResult(
        urgency=urgency,
        trade=trade,
        property_name=data.get("property_name"),
        unit=data.get("unit"),
        tenant_contact=data.get("tenant_contact"),
        issue_summary=data.get("issue_summary", ""),
        confidence=confidence,
    )


def _restore_result(result: TriageResult, mapping: dict[str, str]) -> TriageResult:
    """Return a copy of result with PII tokens restored for local display.

    Args:
        result: A triage result whose string fields may contain tokens.
        mapping: Token to original mapping from redaction.

    Returns:
        A new TriageResult with string fields restored.
    """
    restored: dict[str, Any] = {}
    for field_name in _RESULT_STRING_FIELDS:
        value = getattr(result, field_name)
        restored[field_name] = restore(value, mapping) if value is not None else None
    return TriageResult(
        urgency=result.urgency,
        trade=result.trade,
        property_name=restored["property_name"],
        unit=restored["unit"],
        tenant_contact=restored["tenant_contact"],
        issue_summary=restored["issue_summary"],
        confidence=dict(result.confidence),
        needs_review=result.needs_review,
    )


def _load_cached_response(redacted_text: str) -> dict[str, Any]:
    """Load a recorded triage response for redacted text from the cache.

    Args:
        redacted_text: The redacted request text.

    Returns:
        Parsed JSON response dict.

    Raises:
        RuntimeError: If no recorded response exists for this text.
    """
    cache_path = get_triage_cache_dir() / f"{prompt_hash(redacted_text)}.json"
    if not cache_path.exists():
        raise RuntimeError(
            "No recorded triage response for this request. Expected cache file "
            f"at {cache_path}. Regenerate the offline cache or run with --live."
        )
    with open(cache_path, encoding="utf-8") as handle:
        return json.load(handle)


def _build_prompt(redacted_text: str) -> str:
    """Build the triage instruction prompt for the live model.

    Args:
        redacted_text: Redacted request text (no raw PII).

    Returns:
        A prompt string requesting strict JSON output.
    """
    return (
        "You triage property maintenance requests for Asantico. Classify the "
        "request and return only JSON with keys urgency (emergency, urgent, or "
        "routine), trade (plumbing, electrical, hvac, appliance, or general), "
        "property_name, unit, tenant_contact, issue_summary, and confidence (a "
        "map of field name to a number from 0 to 1). Do not invent PII; tokens "
        "such as NAME_1 or PHONE_1 are already redacted, keep them as is. Do "
        "not use em dashes.\n\nRequest:\n" + redacted_text
    )


def _call_model(model: str, redacted_text: str) -> dict[str, Any]:
    """Call the routed live model and return parsed JSON.

    The live path reuses the existing environment and is intentionally not
    exercised during offline grading.

    Args:
        model: The routed model name ("haiku" or "opus").
        redacted_text: Redacted request text.

    Returns:
        Parsed JSON response dict.

    Raises:
        RuntimeError: If the LLM SDK or credentials are unavailable.
    """
    try:
        import anthropic  # type: ignore
    except ImportError as exc:  # pragma: no cover - live path
        raise RuntimeError(
            "Live triage requires the anthropic SDK and an API key in the "
            "environment. Install it or run offline without --live."
        ) from exc

    model_ids = {
        MODEL_HAIKU: os.environ.get("ASANTICO_HAIKU_MODEL", "claude-haiku-4-5"),
        MODEL_OPUS: os.environ.get("ASANTICO_OPUS_MODEL", "claude-opus-4-7"),
    }
    client = anthropic.Anthropic()  # pragma: no cover - live path
    message = client.messages.create(  # pragma: no cover - live path
        model=model_ids.get(model, model_ids[MODEL_HAIKU]),
        max_tokens=1024,
        messages=[{"role": "user", "content": _build_prompt(redacted_text)}],
    )
    text = "".join(  # pragma: no cover - live path
        block.text for block in message.content if getattr(block, "type", "") == "text"
    )
    return json.loads(text)  # pragma: no cover - live path


def _write_audit_line(
    *,
    model: str,
    redacted_text: str,
    digest: str,
    result: TriageResult,
) -> None:
    """Append one redacted audit line for a triage call.

    Logs redacted text only. The PII restore map is never written.

    Args:
        model: The routed model name.
        redacted_text: The redacted request text.
        digest: The prompt hash for this request.
        result: The triage result (urgency, trade, needs_review).
    """
    ensure_config_dir()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "prompt_hash": digest,
        "urgency": result.urgency,
        "trade": result.trade,
        "needs_review": result.needs_review,
        "redacted_text": redacted_text,
    }
    with open(get_audit_log_path(), "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def triage_request(
    raw_text: str,
    *,
    live: bool,
    threshold: float,
) -> TriageResult:
    """Triage a raw work order request into a structured TriageResult.

    Redacts PII before any model call or cache lookup. Offline, reads a recorded
    response from the fixtures cache keyed by the redacted text hash. Live,
    routes by urgency and calls the model, escalating to the stronger model when
    the first pass is an emergency or ambiguous. Appends a redacted audit line.

    Args:
        raw_text: The raw, possibly PII-bearing request text.
        live: True to call the model, False to use the recorded cache.
        threshold: Minimum acceptable per-field confidence.

    Returns:
        A TriageResult with needs_review set and PII restored for local display.
    """
    redacted_text, mapping = redact(raw_text)
    digest = prompt_hash(redacted_text)

    if live:
        model = MODEL_HAIKU
        result = _result_from_response(_call_model(model, redacted_text))
        ambiguous = any(score < threshold for score in result.confidence.values())
        routed = route_model(result.urgency, ambiguous)
        if routed == MODEL_OPUS and model != MODEL_OPUS:
            model = MODEL_OPUS
            result = _result_from_response(_call_model(model, redacted_text))
    else:
        result = _result_from_response(_load_cached_response(redacted_text))
        ambiguous = any(score < threshold for score in result.confidence.values())
        model = route_model(result.urgency, ambiguous)

    result.needs_review = should_escalate(result, threshold)

    # Audit uses redacted data only, before any PII is restored.
    _write_audit_line(
        model=model,
        redacted_text=redacted_text,
        digest=digest,
        result=result,
    )

    return _restore_result(result, mapping)
