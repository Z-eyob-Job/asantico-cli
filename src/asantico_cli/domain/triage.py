"""Domain model for work order triage.

Pure domain layer: no I/O, no network, no LLM calls. This module defines the
structured result of triaging a raw maintenance request and the escalation
rule that routes risky or low-confidence cases to a human.
"""

from dataclasses import dataclass, field
from typing import Literal

Urgency = Literal["emergency", "urgent", "routine"]
Trade = Literal["plumbing", "electrical", "hvac", "appliance", "general"]


@dataclass
class TriageResult:
    """Structured outcome of triaging a single raw work order request.

    Args:
        urgency: Classified urgency level.
        trade: Classified trade category.
        property_name: Extracted property name, or None if not found.
        unit: Extracted unit identifier, or None if not found.
        tenant_contact: Extracted tenant contact string, or None if not found.
        issue_summary: Short summary of the reported issue.
        confidence: Per-field confidence scores in the range 0.0 to 1.0.
        needs_review: True when the case must go to a human before progressing.
    """

    urgency: Urgency
    trade: Trade
    property_name: str | None
    unit: str | None
    tenant_contact: str | None
    issue_summary: str
    confidence: dict[str, float] = field(default_factory=dict)
    needs_review: bool = False


def should_escalate(result: TriageResult, threshold: float) -> bool:
    """Decide whether a triage result must be escalated to a human.

    A case escalates when it is an emergency or when any per-field confidence
    score falls below the threshold.

    Args:
        result: The triage result to evaluate.
        threshold: Minimum acceptable confidence for every field.

    Returns:
        True if the case should be escalated to human review, otherwise False.
    """
    if result.urgency == "emergency":
        return True
    return any(score < threshold for score in result.confidence.values())
