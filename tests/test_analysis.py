"""Tests for the analysis module — style profiling and theme extraction."""

import json

from click.testing import CliRunner

from ventureoracle.analysis.style import (
    _format_samples,
    analyze_style,
    build_profile,
    extract_themes,
)
from ventureoracle.cli import cli
from ventureoracle.db.database import get_session
from ventureoracle.db.models import AuthorProfile, Content, ContentSource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_STYLE_RESPONSE = json.dumps(
    {
        "tone": "analytical and conversational",
        "vocabulary_level": "intermediate",
        "sentence_structure": "Mix of short punchy sentences and longer compound ones",
        "rhetorical_devices": ["analogy", "rhetorical question"],
        "signature_phrases": ["here's the thing", "let's be real"],
        "typical_length": "800-1200 words",
        "voice_description": "A sharp, opinionated voice that blends data with storytelling.",
    }
)

MOCK_THEMES_RESPONSE = json.dumps(
    {
        "themes": [
            {
                "topic": "AI safety",
                "strength": 0.9,
                "subtopics": ["alignment", "regulation"],
                "evidence": "Mentioned in 8 of 10 posts",
            },
            {
                "topic": "Venture capital",
                "strength": 0.7,
                "subtopics": ["seed stage", "market trends"],
                "evidence": "Recurring focus on VC dynamics",
            },
        ],
        "interests": [
            {"area": "machine learning", "depth": "deep", "frequency": "very often"},
            {"area": "startup strategy", "depth": "moderate", "frequency": "often"},
        ],
        "worldview": "Techno-optimist with a healthy skepticism toward hype.",
    }
)


def _make_contents(session, count=3):
    """Create and persist fake Content objects for testing."""
    source = ContentSource(
        platform="file", identifier="/fake/path", display_name="test"
    )
    session.add(source)
    session.commit()

    contents = []
    for i in range(count):
        c = Content(
            source_id=source.id,
            title=f"Post {i + 1}",
            body=f"This is sample content about AI and venture capital, post number {i + 1}.",
            word_count=12,
            content_hash=Content.compute_hash(f"content-{i}"),
        )
        session.add(c)
        contents.append(c)
    session.commit()
    return contents


# ---------------------------------------------------------------------------
# Unit tests — _format_samples
# ---------------------------------------------------------------------------


def test_format_samples_basic():
    """_format_samples should format content into labeled sections."""
    session = get_session()
    contents = _make_contents(session, count=2)

    result = _format_samples(contents)
    assert "--- Sample 1 — Post 1 ---" in result
    assert "--- Sample 2 — Post 2 ---" in result
    assert "AI and venture capital" in result


def test_format_samples_truncates_long_body():
    """Bodies longer than 3000 chars should be truncated."""
    session = get_session()
    source = ContentSource(platform="file", identifier="/x", display_name="t")
    session.add(source)
    session.commit()

    long_body = "x" * 5000
    c = Content(
        source_id=source.id,
        title="Long",
        body=long_body,
        word_count=5000,
        content_hash=Content.compute_hash(long_body),
    )
    session.add(c)
    session.commit()

    result = _format_samples([c])
    # Each sample body is sliced to [:3000]
    assert len(result) < 5000


def test_format_samples_max_15():
    """Only first 15 samples should be included."""
    session = get_session()
    contents = _make_contents(session, count=20)

    result = _format_samples(contents)
    assert "Sample 15" in result
    assert "Sample 16" not in result


# ---------------------------------------------------------------------------
# Unit tests — analyze_style (mocked Claude)
# ---------------------------------------------------------------------------


def test_analyze_style(monkeypatch):
    """analyze_style should return parsed style dict from Claude."""
    monkeypatch.setattr(
        "ventureoracle.analysis.style.ask_claude_json",
        lambda prompt, system="", **kw: MOCK_STYLE_RESPONSE,
    )

    session = get_session()
    contents = _make_contents(session)
    result = analyze_style(contents)

    assert result["tone"] == "analytical and conversational"
    assert result["vocabulary_level"] == "intermediate"
    assert "voice_description" in result
    assert isinstance(result["rhetorical_devices"], list)


def test_extract_themes(monkeypatch):
    """extract_themes should return parsed themes dict from Claude."""
    monkeypatch.setattr(
        "ventureoracle.analysis.style.ask_claude_json",
        lambda prompt, system="", **kw: MOCK_THEMES_RESPONSE,
    )

    session = get_session()
    contents = _make_contents(session)
    result = extract_themes(contents)

    assert len(result["themes"]) == 2
    assert result["themes"][0]["topic"] == "AI safety"
    assert len(result["interests"]) == 2
    assert "worldview" in result


# ---------------------------------------------------------------------------
# Integration tests — build_profile (mocked Claude, real DB)
# ---------------------------------------------------------------------------


def _mock_ask_claude_json(prompt, system="", **kw):
    """Route mock responses based on prompt content."""
    if "writing style" in prompt.lower() or "style profile" in prompt.lower():
        return MOCK_STYLE_RESPONSE
    return MOCK_THEMES_RESPONSE


def test_build_profile(monkeypatch):
    """build_profile should create an AuthorProfile with correct fields."""
    monkeypatch.setattr(
        "ventureoracle.analysis.style.ask_claude_json", _mock_ask_claude_json
    )

    session = get_session()
    contents = _make_contents(session)
    profile = build_profile(contents)

    assert isinstance(profile, AuthorProfile)
    assert profile.sample_count == 3
    assert profile.writing_style["tone"] == "analytical and conversational"
    assert len(profile.themes) == 2
    assert len(profile.interests) == 2
    assert "sharp" in profile.voice_description.lower()


def test_build_profile_persists_in_db(monkeypatch):
    """build_profile should persist the profile in the database."""
    monkeypatch.setattr(
        "ventureoracle.analysis.style.ask_claude_json", _mock_ask_claude_json
    )

    session = get_session()
    contents = _make_contents(session)
    build_profile(contents)

    # Query from a fresh session to confirm persistence
    profiles = session.query(AuthorProfile).all()
    assert len(profiles) == 1
    assert profiles[0].themes[0]["topic"] == "AI safety"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_profile_show_with_data():
    """profile show should display an existing profile."""
    session = get_session()
    profile = AuthorProfile(
        writing_style={"tone": "analytical"},
        themes=[{"topic": "AI", "strength": 0.9}],
        interests=[{"area": "ML", "depth": "deep"}],
        voice_description="A sharp analytical voice.",
        sample_count=5,
    )
    session.add(profile)
    session.commit()

    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "show"])
    assert result.exit_code == 0
    assert "Author Profile" in result.output
    assert "analytical" in result.output
    assert "Voice" in result.output


def test_profile_analyze_with_content(monkeypatch):
    """profile analyze should build a profile from ingested content."""
    monkeypatch.setattr(
        "ventureoracle.analysis.style.ask_claude_json", _mock_ask_claude_json
    )

    session = get_session()
    _make_contents(session, count=5)

    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "analyze"])
    assert result.exit_code == 0
    assert "Profile built" in result.output
    assert "5 samples" in result.output


def test_profile_analyze_no_content():
    """profile analyze should warn when no content exists."""
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "analyze"])
    assert result.exit_code == 0
    assert "No content" in result.output
