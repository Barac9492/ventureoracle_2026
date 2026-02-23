"""Tests for the discovery module — RSS scanning, web search, and topic recommendations."""

import json

from click.testing import CliRunner

from ventureoracle.cli import cli
from ventureoracle.db.database import get_session
from ventureoracle.db.models import (
    AuthorProfile,
    Content,
    ContentSource,
    DiscoveredContent,
    TopicRecommendation,
)
from ventureoracle.discovery.recommender import recommend_topics
from ventureoracle.discovery.search import scan_rss_feed, search_brave


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RSS_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tech Blog</title>
    <link>http://techblog.example.com</link>
    <item>
      <title>The Rise of AI Agents</title>
      <link>http://techblog.example.com/ai-agents</link>
      <description>AI agents are transforming how we build software.</description>
      <pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>VC Funding Trends 2024</title>
      <link>http://techblog.example.com/vc-2024</link>
      <description>Venture capital is shifting toward AI-native companies.</description>
      <pubDate>Tue, 02 Jan 2024 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title></title>
      <link>http://techblog.example.com/empty-title</link>
      <description>This item has an empty title and should be skipped.</description>
    </item>
  </channel>
</rss>
"""

BRAVE_RESPONSE_JSON = {
    "web": {
        "results": [
            {
                "title": "Emerging AI Trends",
                "url": "https://example.com/ai-trends",
                "description": "A look at the latest trends in artificial intelligence.",
            },
            {
                "title": "Startup Ecosystem Report",
                "url": "https://example.com/startups",
                "description": "Annual report on the global startup ecosystem.",
            },
        ]
    }
}

MOCK_RECOMMENDATIONS_RESPONSE = json.dumps(
    {
        "recommendations": [
            {
                "title": "Why AI Agents Will Replace SaaS",
                "rationale": "Aligns with your AI focus and contrarian voice",
                "source_urls": ["http://techblog.example.com/ai-agents"],
                "relevance": 0.92,
            },
            {
                "title": "The Seed-Stage Shakeout",
                "rationale": "Matches your VC expertise and market analysis style",
                "source_urls": ["http://techblog.example.com/vc-2024"],
                "relevance": 0.85,
            },
        ]
    }
)


class MockHttpxResponse:
    def __init__(self, content=None, json_data=None):
        self.content = content
        self._json = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


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
            url=f"http://example.com/post-{i}",
            title=f"Discovery {i + 1}",
            summary=f"Summary of discovery {i + 1} about AI trends.",
            content_hash=Content.compute_hash(f"discovery-{i}"),
        )
        session.add(d)
        discoveries.append(d)
    session.commit()
    return discoveries


# ---------------------------------------------------------------------------
# scan_rss_feed tests
# ---------------------------------------------------------------------------


def test_scan_rss_feed(monkeypatch):
    """scan_rss_feed should parse RSS and return DiscoveredContent objects."""

    def mock_get(*args, **kwargs):
        return MockHttpxResponse(content=RSS_XML)

    monkeypatch.setattr("ventureoracle.discovery.search.httpx.get", mock_get)

    results = scan_rss_feed("http://techblog.example.com/feed")

    assert len(results) == 2  # Empty-title item should be skipped
    assert results[0].title == "The Rise of AI Agents"
    assert results[1].title == "VC Funding Trends 2024"
    assert results[0].source_type == "rss"
    assert results[0].content_hash  # Hash should be computed


def test_scan_rss_feed_deduplication(monkeypatch):
    """Items with same title+url should produce same content_hash."""

    def mock_get(*args, **kwargs):
        return MockHttpxResponse(content=RSS_XML)

    monkeypatch.setattr("ventureoracle.discovery.search.httpx.get", mock_get)

    results = scan_rss_feed("http://techblog.example.com/feed")
    # Run again — hashes should be deterministic
    results2 = scan_rss_feed("http://techblog.example.com/feed")
    assert results[0].content_hash == results2[0].content_hash


# ---------------------------------------------------------------------------
# search_brave tests
# ---------------------------------------------------------------------------


def test_search_brave(monkeypatch):
    """search_brave should parse Brave API response into DiscoveredContent."""

    def mock_get(*args, **kwargs):
        return MockHttpxResponse(json_data=BRAVE_RESPONSE_JSON)

    monkeypatch.setattr("ventureoracle.discovery.search.httpx.get", mock_get)
    monkeypatch.setenv("BRAVE_API_KEY", "test-key-123")

    # Reset settings cache so the env var is picked up
    import ventureoracle.config as cfg_mod
    cfg_mod._settings = None

    results = search_brave("AI trends", count=5)

    assert len(results) == 2
    assert results[0].title == "Emerging AI Trends"
    assert results[0].source_type == "web_search"
    assert results[1].url == "https://example.com/startups"

    cfg_mod._settings = None  # Clean up


def test_search_brave_no_api_key(monkeypatch):
    """search_brave should return empty list without API key."""
    monkeypatch.setenv("BRAVE_API_KEY", "")

    import ventureoracle.config as cfg_mod
    cfg_mod._settings = None

    results = search_brave("AI trends")
    assert results == []

    cfg_mod._settings = None


# ---------------------------------------------------------------------------
# recommend_topics tests
# ---------------------------------------------------------------------------


def test_recommend_topics(monkeypatch):
    """recommend_topics should return TopicRecommendation objects."""
    monkeypatch.setattr(
        "ventureoracle.discovery.recommender.ask_claude_json",
        lambda prompt, system="", **kw: MOCK_RECOMMENDATIONS_RESPONSE,
    )

    session = get_session()
    profile = _make_profile(session)
    discoveries = _make_discoveries(session)

    results = recommend_topics(profile, discoveries, count=2)

    assert len(results) == 2
    assert isinstance(results[0], TopicRecommendation)
    assert results[0].title == "Why AI Agents Will Replace SaaS"
    assert results[0].relevance == 0.92
    assert results[1].relevance == 0.85
    assert len(results[0].source_urls) == 1


def test_recommend_topics_empty_discoveries(monkeypatch):
    """recommend_topics should work with empty discoveries list."""
    monkeypatch.setattr(
        "ventureoracle.discovery.recommender.ask_claude_json",
        lambda prompt, system="", **kw: json.dumps({"recommendations": []}),
    )

    session = get_session()
    profile = _make_profile(session)

    results = recommend_topics(profile, [], count=3)
    assert results == []


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_discover_scan_cli(monkeypatch):
    """discover scan should scan a feed and display results."""

    def mock_get(*args, **kwargs):
        return MockHttpxResponse(content=RSS_XML)

    monkeypatch.setattr("ventureoracle.discovery.search.httpx.get", mock_get)

    runner = CliRunner()
    result = runner.invoke(cli, ["discover", "scan", "http://techblog.example.com/feed"])

    assert result.exit_code == 0
    assert "Discovered 2 items" in result.output
    assert "AI Agents" in result.output


def test_discover_search_no_key(monkeypatch):
    """discover search should warn when no API key is set."""
    monkeypatch.setenv("BRAVE_API_KEY", "")

    import ventureoracle.config as cfg_mod
    cfg_mod._settings = None

    runner = CliRunner()
    result = runner.invoke(cli, ["discover", "search", "AI trends"])

    assert result.exit_code == 0
    assert "No results" in result.output

    cfg_mod._settings = None


def test_discover_topics_no_profile():
    """discover topics should warn when no profile exists."""
    runner = CliRunner()
    result = runner.invoke(cli, ["discover", "topics"])

    assert result.exit_code == 0
    assert "No profile" in result.output


def test_discover_topics_no_discoveries():
    """discover topics should warn when no discoveries exist."""
    session = get_session()
    _make_profile(session)

    runner = CliRunner()
    result = runner.invoke(cli, ["discover", "topics"])

    assert result.exit_code == 0
    assert "No discoveries" in result.output


def test_discover_topics_with_data(monkeypatch):
    """discover topics should generate recommendations with profile and discoveries."""
    monkeypatch.setattr(
        "ventureoracle.discovery.recommender.ask_claude_json",
        lambda prompt, system="", **kw: MOCK_RECOMMENDATIONS_RESPONSE,
    )

    session = get_session()
    _make_profile(session)
    _make_discoveries(session, count=5)

    runner = CliRunner()
    result = runner.invoke(cli, ["discover", "topics", "--count", "2"])

    assert result.exit_code == 0
    assert "Recommended Topics" in result.output
    assert "AI Agents" in result.output
