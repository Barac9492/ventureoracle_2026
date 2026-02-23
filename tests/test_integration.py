"""End-to-end integration tests — full pipeline from ingestion to prediction."""

import json

from click.testing import CliRunner

from ventureoracle.cli import cli
from ventureoracle.db.database import get_session
from ventureoracle.db.models import (
    AuthorProfile,
    Content,
    ContentSource,
    DiscoveredContent,
    Prediction,
    TopicRecommendation,
)


# ---------------------------------------------------------------------------
# Mock responses
# ---------------------------------------------------------------------------

MOCK_STYLE = json.dumps(
    {
        "tone": "analytical and direct",
        "vocabulary_level": "advanced",
        "sentence_structure": "Alternates between short punchy and long compound",
        "rhetorical_devices": ["data-driven analogies", "contrarian framing"],
        "signature_phrases": ["the real question is", "here's what matters"],
        "typical_length": "1000-1500 words",
        "voice_description": "A sharp, data-driven voice that challenges conventional wisdom.",
    }
)

MOCK_THEMES = json.dumps(
    {
        "themes": [
            {"topic": "AI infrastructure", "strength": 0.95, "subtopics": ["GPU economics", "model serving"], "evidence": "Core focus in 8/10 posts"},
            {"topic": "Developer tools", "strength": 0.7, "subtopics": ["CLI", "SDK design"], "evidence": "Recurring interest"},
        ],
        "interests": [
            {"area": "machine learning ops", "depth": "expert", "frequency": "every post"},
            {"area": "startup go-to-market", "depth": "deep", "frequency": "frequently"},
        ],
        "worldview": "Builder-pragmatist who values shipping over theorizing.",
    }
)

MOCK_RECOMMENDATIONS = json.dumps(
    {
        "recommendations": [
            {
                "title": "Why GPU Clouds Are the New AWS",
                "rationale": "Aligns with AI infrastructure expertise",
                "source_urls": ["http://example.com/gpu"],
                "relevance": 0.93,
            },
        ]
    }
)

MOCK_PREDICTIONS = json.dumps(
    {
        "predictions": [
            {
                "domain": "AI infrastructure",
                "claim": "Inference costs will drop 10x in 18 months",
                "reasoning": "Hardware competition + quantization advances",
                "confidence": 0.8,
                "timeframe": "18 months",
                "evidence": ["NVIDIA competition from AMD/Intel", "Quantization breakthroughs"],
                "counterarguments": "Demand may outpace supply reductions",
            },
        ]
    }
)

RSS_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI News</title>
    <item>
      <title>GPU Costs Plummet</title>
      <link>http://example.com/gpu-costs</link>
      <description>New competition drives inference costs down dramatically.</description>
    </item>
    <item>
      <title>MLOps Trends 2026</title>
      <link>http://example.com/mlops</link>
      <description>The latest trends in machine learning operations.</description>
    </item>
  </channel>
</rss>
"""


class MockHttpxResponse:
    def __init__(self, content=None):
        self.content = content

    def raise_for_status(self):
        pass


def _mock_claude(prompt, system="", **kw):
    """Route mock responses based on prompt content."""
    lower = prompt.lower()
    if "writing style" in lower or "style profile" in lower:
        return MOCK_STYLE
    if "themes" in lower and "interests" in lower and "writing samples" in lower:
        return MOCK_THEMES
    if "recommend" in lower and "writing topics" in lower:
        return MOCK_RECOMMENDATIONS
    if "predictions" in lower or "generate" in lower:
        return MOCK_PREDICTIONS
    return MOCK_STYLE


# ---------------------------------------------------------------------------
# Full pipeline integration test
# ---------------------------------------------------------------------------


def test_full_pipeline(monkeypatch, tmp_path):
    """Test the complete pipeline: ingest -> profile -> discover -> recommend -> predict."""
    # Mock external calls
    monkeypatch.setattr("ventureoracle.analysis.style.ask_claude_json", _mock_claude)
    monkeypatch.setattr("ventureoracle.discovery.recommender.ask_claude_json", _mock_claude)
    monkeypatch.setattr("ventureoracle.prediction.engine.ask_claude_json", _mock_claude)
    monkeypatch.setattr(
        "ventureoracle.discovery.search.httpx.get",
        lambda *a, **kw: MockHttpxResponse(content=RSS_XML),
    )

    runner = CliRunner()

    # Step 1: Ingest local files
    for i in range(3):
        f = tmp_path / f"post_{i}.md"
        f.write_text(f"# Post {i}\n\nThis is a deep dive into AI infrastructure and GPU economics, post {i}.")
    result = runner.invoke(cli, ["ingest", "file", str(tmp_path)])
    assert result.exit_code == 0
    assert "Ingested" in result.output

    # Verify content in DB
    session = get_session()
    contents = session.query(Content).all()
    assert len(contents) == 3

    # Step 2: Build profile
    result = runner.invoke(cli, ["profile", "analyze"])
    assert result.exit_code == 0
    assert "Profile built" in result.output

    profile = session.query(AuthorProfile).first()
    assert profile is not None
    assert profile.sample_count == 3
    assert profile.writing_style["tone"] == "analytical and direct"

    # Step 3: Discover content via RSS scan
    result = runner.invoke(cli, ["discover", "scan", "http://example.com/feed"])
    assert result.exit_code == 0
    assert "Discovered 2 items" in result.output

    discoveries = session.query(DiscoveredContent).all()
    assert len(discoveries) == 2

    # Step 4: Get topic recommendations
    result = runner.invoke(cli, ["discover", "topics", "--count", "1"])
    assert result.exit_code == 0
    assert "Recommended Topics" in result.output

    recs = session.query(TopicRecommendation).all()
    assert len(recs) == 1
    assert recs[0].relevance == 0.93

    # Step 5: Generate predictions
    result = runner.invoke(cli, ["predict", "generate", "--count", "1"])
    assert result.exit_code == 0
    assert "Generated 1 predictions" in result.output

    preds = session.query(Prediction).all()
    assert len(preds) == 1
    assert preds[0].confidence == 0.8
    assert preds[0].domain == "AI infrastructure"

    # Step 6: Dashboard should reflect all data
    result = runner.invoke(cli, ["dashboard"])
    assert result.exit_code == 0
    assert "3" in result.output  # 3 content pieces


def test_profile_then_predict_without_discoveries(monkeypatch, tmp_path):
    """Profile + predict should work even without any discoveries."""
    monkeypatch.setattr("ventureoracle.analysis.style.ask_claude_json", _mock_claude)
    monkeypatch.setattr("ventureoracle.prediction.engine.ask_claude_json", _mock_claude)

    runner = CliRunner()

    # Ingest a file
    f = tmp_path / "post.md"
    f.write_text("# AI Post\n\nDeep analysis of transformer architectures and their implications.")
    runner.invoke(cli, ["ingest", "file", str(f)])

    # Build profile
    result = runner.invoke(cli, ["profile", "analyze"])
    assert result.exit_code == 0

    # Generate predictions (no discoveries — should still work)
    result = runner.invoke(cli, ["predict", "generate", "--count", "1"])
    assert result.exit_code == 0
    assert "Generated 1 predictions" in result.output


def test_resolve_and_calibrate(monkeypatch, tmp_path):
    """Resolve predictions and check calibration stats."""
    monkeypatch.setattr("ventureoracle.analysis.style.ask_claude_json", _mock_claude)
    monkeypatch.setattr("ventureoracle.prediction.engine.ask_claude_json", _mock_claude)

    runner = CliRunner()

    # Set up: ingest -> profile -> predict
    f = tmp_path / "post.md"
    f.write_text("# AI Post\n\nContent about AI trends and predictions.")
    runner.invoke(cli, ["ingest", "file", str(f)])
    runner.invoke(cli, ["profile", "analyze"])
    runner.invoke(cli, ["predict", "generate", "--count", "1"])

    # Get prediction ID
    session = get_session()
    pred = session.query(Prediction).first()
    assert pred is not None

    # Resolve as correct
    result = runner.invoke(cli, ["predict", "resolve", pred.id[:8], "correct"])
    assert result.exit_code == 0
    assert "resolved as: correct" in result.output

    # Check calibration
    result = runner.invoke(cli, ["predict", "calibration"])
    assert result.exit_code == 0
    assert "Calibration" in result.output
