"""SQLAlchemy ORM models for VentureOracle."""

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Content Layer
# ---------------------------------------------------------------------------


class ContentSource(Base):
    """A platform or feed from which content is ingested."""

    __tablename__ = "content_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String(50))  # linkedin, substack, rss, file
    identifier: Mapped[str] = mapped_column(String(500))  # URL, username, or file path
    display_name: Mapped[str] = mapped_column(String(200))
    config_json: Mapped[str | None] = mapped_column(JSON, nullable=True)
    is_own_content: Mapped[bool] = mapped_column(default=True)
    last_ingested_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)

    contents: Mapped[list["Content"]] = relationship(back_populates="source")


class Content(Base):
    """A single piece of content (article, post, etc.)."""

    __tablename__ = "contents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source_id: Mapped[str] = mapped_column(ForeignKey("content_sources.id"))
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64))  # SHA-256
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(default=_utcnow)

    source: Mapped["ContentSource"] = relationship(back_populates="contents")

    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Profile Layer
# ---------------------------------------------------------------------------


class AuthorProfile(Base):
    """The user's learned writing profile."""

    __tablename__ = "author_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    version: Mapped[int] = mapped_column(Integer, default=1)
    writing_style: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    themes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interests: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    voice_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    built_at: Mapped[datetime] = mapped_column(default=_utcnow)


# ---------------------------------------------------------------------------
# Discovery Layer
# ---------------------------------------------------------------------------


class TopicRecommendation(Base):
    """A recommended writing topic."""

    __tablename__ = "topic_recommendations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(500))
    rationale: Mapped[str] = mapped_column(Text)
    source_urls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    relevance: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="new")  # new, accepted, rejected, written
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)


class DiscoveredContent(Base):
    """Content discovered from the web."""

    __tablename__ = "discovered_contents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    source_type: Mapped[str] = mapped_column(String(50))  # rss, web_search, hacker_news
    url: Mapped[str] = mapped_column(String(2000))
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    content_hash: Mapped[str] = mapped_column(String(64))
    discovered_at: Mapped[datetime] = mapped_column(default=_utcnow)
    status: Mapped[str] = mapped_column(String(20), default="new")


# ---------------------------------------------------------------------------
# Prediction Layer
# ---------------------------------------------------------------------------


class Prediction(Base):
    """A specific prediction generated by the engine."""

    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    domain: Mapped[str] = mapped_column(String(100))
    claim: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    timeframe: Mapped[str] = mapped_column(String(100))
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    counterarguments: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, correct, incorrect, expired
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
