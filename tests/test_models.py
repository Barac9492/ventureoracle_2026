"""Tests for database models."""

from ventureoracle.db.database import get_session
from ventureoracle.db.models import (
    AuthorProfile,
    Content,
    ContentSource,
    DiscoveredContent,
    Prediction,
    TopicRecommendation,
)


def test_create_content_source():
    """Should create and persist a ContentSource."""
    session = get_session()
    source = ContentSource(
        platform="substack",
        identifier="https://example.substack.com/feed",
        display_name="Example Newsletter",
    )
    session.add(source)
    session.commit()

    result = session.get(ContentSource, source.id)
    assert result is not None
    assert result.platform == "substack"
    assert result.display_name == "Example Newsletter"


def test_create_content_with_source():
    """Should create Content linked to a ContentSource."""
    session = get_session()
    source = ContentSource(
        platform="rss",
        identifier="https://example.com/feed",
        display_name="Test Feed",
    )
    session.add(source)
    session.commit()

    content = Content(
        source_id=source.id,
        title="Test Article",
        body="This is the body of the article about AI.",
        word_count=9,
        content_hash=Content.compute_hash("This is the body of the article about AI."),
    )
    session.add(content)
    session.commit()

    result = session.get(Content, content.id)
    assert result is not None
    assert result.title == "Test Article"
    assert result.source_id == source.id


def test_create_author_profile():
    """Should create an AuthorProfile."""
    session = get_session()
    profile = AuthorProfile(
        writing_style={"tone": "analytical", "vocabulary_level": "advanced"},
        themes=[{"topic": "AI", "strength": 0.9}],
        interests=[{"area": "venture capital", "depth": "expert"}],
        voice_description="Writes with an analytical, data-driven tone.",
        sample_count=10,
    )
    session.add(profile)
    session.commit()

    result = session.get(AuthorProfile, profile.id)
    assert result is not None
    assert result.writing_style["tone"] == "analytical"
    assert result.sample_count == 10


def test_create_prediction():
    """Should create a Prediction."""
    session = get_session()
    pred = Prediction(
        domain="AI",
        claim="Agent frameworks will consolidate by end of 2026",
        reasoning="Too many frameworks, market will pick winners",
        confidence=0.75,
        timeframe="12 months",
        evidence=["rapid growth in agent tooling", "enterprise demand for stability"],
    )
    session.add(pred)
    session.commit()

    result = session.get(Prediction, pred.id)
    assert result is not None
    assert result.confidence == 0.75
    assert result.status == "active"


def test_create_discovered_content():
    """Should create DiscoveredContent."""
    session = get_session()
    disc = DiscoveredContent(
        source_type="rss",
        url="https://example.com/article",
        title="Interesting Article",
        summary="An interesting article about trends.",
        content_hash=Content.compute_hash("https://example.com/article"),
    )
    session.add(disc)
    session.commit()

    result = session.get(DiscoveredContent, disc.id)
    assert result is not None
    assert result.source_type == "rss"


def test_create_topic_recommendation():
    """Should create a TopicRecommendation."""
    session = get_session()
    rec = TopicRecommendation(
        title="Why AI Agents Will Replace SaaS",
        rationale="Aligns with author's AI expertise and VC perspective",
        source_urls=["https://example.com/1", "https://example.com/2"],
        relevance=0.85,
    )
    session.add(rec)
    session.commit()

    result = session.get(TopicRecommendation, rec.id)
    assert result is not None
    assert result.relevance == 0.85
    assert result.status == "new"
