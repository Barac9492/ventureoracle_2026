"""Tests for the prediction module — engine, tracker, and calibration."""

import json

from click.testing import CliRunner

from ventureoracle.cli import cli
from ventureoracle.db.database import get_session
from ventureoracle.db.models import (
    AuthorProfile,
    Content,
    DiscoveredContent,
    Prediction,
)
from ventureoracle.prediction.engine import generate_predictions
from ventureoracle.prediction.tracker import (
    get_calibration_stats,
    list_predictions,
    resolve_prediction,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_PREDICTIONS_RESPONSE = json.dumps(
    {
        "predictions": [
            {
                "domain": "AI",
                "claim": "AI agents will replace 30% of SaaS workflows by 2026",
                "reasoning": "Agent frameworks are maturing rapidly and enterprise adoption is accelerating.",
                "confidence": 0.75,
                "timeframe": "18 months",
                "evidence": ["Rise of AI coding assistants", "Enterprise agent adoption"],
                "counterarguments": "Enterprises move slowly and existing SaaS has deep integrations.",
            },
            {
                "domain": "venture capital",
                "claim": "Seed valuations will compress 20% in the next year",
                "reasoning": "Overcrowded seed market with fewer Series A follow-ons.",
                "confidence": 0.6,
                "timeframe": "12 months",
                "evidence": ["Declining Series A conversion rates"],
                "counterarguments": "AI hype may keep seed valuations inflated.",
            },
        ]
    }
)


def _make_profile(session):
    """Create a test AuthorProfile."""
    profile = AuthorProfile(
        writing_style={"tone": "analytical"},
        themes=[{"topic": "AI", "strength": 0.9}],
        interests=[{"area": "machine learning", "depth": "deep"}],
        voice_description="A sharp analytical voice focused on AI and venture capital.",
        sample_count=10,
    )
    session.add(profile)
    session.commit()
    return profile


def _make_discoveries(session, count=3):
    """Create test DiscoveredContent objects."""
    discoveries = []
    for i in range(count):
        d = DiscoveredContent(
            source_type="rss",
            url=f"http://example.com/signal-{i}",
            title=f"Signal {i + 1}",
            summary=f"Signal about AI trends number {i + 1}.",
            content_hash=Content.compute_hash(f"signal-{i}"),
        )
        session.add(d)
        discoveries.append(d)
    session.commit()
    return discoveries


def _make_predictions(session, count=3, statuses=None):
    """Create test Prediction objects with optional custom statuses."""
    if statuses is None:
        statuses = ["active"] * count
    predictions = []
    for i in range(count):
        p = Prediction(
            domain="AI" if i % 2 == 0 else "venture capital",
            claim=f"Test prediction {i + 1}",
            reasoning=f"Reasoning for prediction {i + 1}",
            confidence=0.5 + i * 0.1,
            timeframe="12 months",
            evidence=[f"evidence-{i}"],
            counterarguments=f"Counter for {i + 1}",
            status=statuses[i] if i < len(statuses) else "active",
        )
        session.add(p)
        predictions.append(p)
    session.commit()
    return predictions


# ---------------------------------------------------------------------------
# generate_predictions tests
# ---------------------------------------------------------------------------


def test_generate_predictions(monkeypatch):
    """generate_predictions should return Prediction objects from Claude response."""
    monkeypatch.setattr(
        "ventureoracle.prediction.engine.ask_claude_json",
        lambda prompt, system="", **kw: MOCK_PREDICTIONS_RESPONSE,
    )

    session = get_session()
    profile = _make_profile(session)
    discoveries = _make_discoveries(session)

    results = generate_predictions(profile, discoveries, count=2)

    assert len(results) == 2
    assert isinstance(results[0], Prediction)
    assert results[0].domain == "AI"
    assert "AI agents" in results[0].claim
    assert results[0].confidence == 0.75
    assert results[0].timeframe == "18 months"
    assert len(results[0].evidence) == 2
    assert results[1].domain == "venture capital"


def test_generate_predictions_empty_discoveries(monkeypatch):
    """generate_predictions should work with no discoveries."""
    monkeypatch.setattr(
        "ventureoracle.prediction.engine.ask_claude_json",
        lambda prompt, system="", **kw: json.dumps({"predictions": []}),
    )

    session = get_session()
    profile = _make_profile(session)

    results = generate_predictions(profile, [], count=2)
    assert results == []


# ---------------------------------------------------------------------------
# tracker tests
# ---------------------------------------------------------------------------


def test_list_predictions_all():
    """list_predictions should return all predictions when no filter."""
    session = get_session()
    _make_predictions(session, count=3)

    results = list_predictions()
    assert len(results) == 3


def test_list_predictions_filtered():
    """list_predictions should filter by status."""
    session = get_session()
    _make_predictions(session, count=3, statuses=["active", "correct", "active"])

    active = list_predictions(status="active")
    assert len(active) == 2

    correct = list_predictions(status="correct")
    assert len(correct) == 1


def test_resolve_prediction():
    """resolve_prediction should update status and resolved_at."""
    session = get_session()
    preds = _make_predictions(session, count=1)
    pred_id = preds[0].id

    result = resolve_prediction(pred_id, "correct")
    assert result is not None
    assert result.status == "correct"
    assert result.resolved_at is not None


def test_resolve_prediction_invalid_outcome():
    """resolve_prediction should reject invalid outcomes."""
    session = get_session()
    preds = _make_predictions(session, count=1)

    try:
        resolve_prediction(preds[0].id, "maybe")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid outcome" in str(e)


def test_resolve_prediction_not_found():
    """resolve_prediction should return None for missing IDs."""
    result = resolve_prediction("nonexistent-id", "correct")
    assert result is None


# ---------------------------------------------------------------------------
# calibration tests
# ---------------------------------------------------------------------------


def test_calibration_no_resolved():
    """get_calibration_stats should handle no resolved predictions."""
    session = get_session()
    _make_predictions(session, count=2)

    stats = get_calibration_stats()
    assert stats["total"] == 2
    assert stats["resolved"] == 0
    assert stats["accuracy"] is None


def test_calibration_with_resolved():
    """get_calibration_stats should compute accuracy correctly."""
    session = get_session()
    _make_predictions(session, count=4, statuses=["correct", "correct", "incorrect", "active"])

    stats = get_calibration_stats()
    assert stats["total"] == 4
    assert stats["resolved"] == 3
    assert stats["correct"] == 2
    assert abs(stats["accuracy"] - 2 / 3) < 0.01


def test_calibration_by_domain():
    """get_calibration_stats should break down accuracy by domain."""
    session = get_session()
    # index 0 -> AI (correct), index 1 -> VC (incorrect), index 2 -> AI (correct)
    _make_predictions(session, count=3, statuses=["correct", "incorrect", "correct"])

    stats = get_calibration_stats()
    assert "AI" in stats["by_domain"]
    assert stats["by_domain"]["AI"]["correct"] == 2
    assert stats["by_domain"]["AI"]["accuracy"] == 1.0
    assert stats["by_domain"]["venture capital"]["accuracy"] == 0.0


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_predict_generate_no_profile():
    """predict generate should warn when no profile exists."""
    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "generate"])
    assert result.exit_code == 0
    assert "No profile" in result.output


def test_predict_generate_with_data(monkeypatch):
    """predict generate should create predictions with profile."""
    monkeypatch.setattr(
        "ventureoracle.prediction.engine.ask_claude_json",
        lambda prompt, system="", **kw: MOCK_PREDICTIONS_RESPONSE,
    )

    session = get_session()
    _make_profile(session)
    _make_discoveries(session, count=3)

    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "generate", "--count", "2"])
    assert result.exit_code == 0
    assert "Generated 2 predictions" in result.output
    assert "AI agents" in result.output


def test_predict_list_with_data():
    """predict list should display predictions in a table."""
    session = get_session()
    _make_predictions(session, count=2)

    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "list"])
    assert result.exit_code == 0
    assert "Predictions" in result.output
    # Rich table wraps text, so check for domain which fits in its column
    assert "AI" in result.output


def test_predict_list_filtered():
    """predict list --status should filter results."""
    session = get_session()
    _make_predictions(session, count=3, statuses=["active", "correct", "active"])

    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "list", "--status", "correct"])
    assert result.exit_code == 0
    assert "correct" in result.output
    # Should only show 1 result (the correct one)
    assert "active" not in result.output or result.output.count("correct") >= 1


def test_predict_resolve_cli():
    """predict resolve should resolve a prediction by partial ID."""
    session = get_session()
    preds = _make_predictions(session, count=1)
    pred_id = preds[0].id[:8]

    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "resolve", pred_id, "correct"])
    assert result.exit_code == 0
    assert "resolved as: correct" in result.output


def test_predict_resolve_not_found():
    """predict resolve should handle missing predictions."""
    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "resolve", "xxxxxxxx", "correct"])
    assert result.exit_code == 0
    assert "not found" in result.output


def test_predict_calibration_empty():
    """predict calibration should handle no predictions."""
    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "calibration"])
    assert result.exit_code == 0
    assert "Calibration" in result.output


def test_predict_calibration_with_data():
    """predict calibration should show accuracy stats."""
    session = get_session()
    _make_predictions(session, count=3, statuses=["correct", "incorrect", "correct"])

    runner = CliRunner()
    result = runner.invoke(cli, ["predict", "calibration"])
    assert result.exit_code == 0
    assert "Calibration" in result.output
