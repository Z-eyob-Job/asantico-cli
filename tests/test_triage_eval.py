"""Smoke test for the offline triage eval harness (Phase 7)."""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = REPO_ROOT / "eval" / "triage_eval.py"


def _load_eval_module():
    """Load eval/triage_eval.py by path (the eval dir is not on sys.path)."""
    spec = importlib.util.spec_from_file_location("triage_eval", EVAL_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the config dir (audit log) so the eval writes nowhere global."""
    config_dir = tmp_path / ".asantico"
    monkeypatch.setenv("ASANTICO_CONFIG_DIR", str(config_dir))
    return config_dir


def test_eval_runs_over_all_fixtures(mock_config_dir: Path) -> None:
    """The eval runs offline over every fixture and produces one row each."""
    triage_eval = _load_eval_module()
    report = triage_eval.evaluate()
    assert report.total == 11
    assert 0.0 <= report.urgency_accuracy <= 1.0
    assert 0.0 <= report.trade_accuracy <= 1.0


def test_every_emergency_escalates(mock_config_dir: Path) -> None:
    """The responsible-AI invariant holds: no emergency is missed."""
    triage_eval = _load_eval_module()
    report = triage_eval.evaluate()
    assert report.emergencies_total >= 2
    assert report.emergencies_escalated == report.emergencies_total
    assert report.all_emergencies_escalated is True
    assert not any(row.missed_escalation for row in report.rows)


def test_print_report_does_not_raise(mock_config_dir: Path) -> None:
    """Rendering the report runs without error."""
    triage_eval = _load_eval_module()
    report = triage_eval.evaluate()
    triage_eval.print_report(report)
