"""Pytest wrapper for LLM judge calibration assertions."""

from tests.calibrate_judge import run_calibration


def test_judge_calibration():
    """Verify that LLM judge achieves >= 80% agreement with human ground truth."""
    summary = run_calibration()
    assert summary["agreement_rate_pct"] >= 80.0, (
        f"Calibration agreement {summary['agreement_rate_pct']}% is below the 80% minimum threshold."
    )
    assert summary["cohens_kappa"] >= 0.70, (
        f"Cohen's Kappa {summary['cohens_kappa']} indicates insufficient inter-rater reliability."
    )
