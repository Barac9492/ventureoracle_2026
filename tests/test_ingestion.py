"""Tests for content ingestion."""

import json
from pathlib import Path

from ventureoracle.db.database import get_session
from ventureoracle.db.models import Content, ContentSource
from ventureoracle.ingestion.file_import import FileIngestor
from ventureoracle.ingestion.linkedin import LinkedInIngestor


def test_file_ingestor_reads_markdown(tmp_path):
    """FileIngestor should read .md files."""
    md_file = tmp_path / "post.md"
    md_file.write_text("# My Post\n\nThis is my writing about AI trends.")

    session = get_session()
    source = ContentSource(
        platform="file",
        identifier=str(md_file),
        display_name="test",
    )
    session.add(source)
    session.commit()

    ingestor = FileIngestor()
    contents = ingestor.ingest(source)

    assert len(contents) == 1
    assert "AI trends" in contents[0].body
    assert contents[0].word_count > 0
    assert contents[0].content_hash


def test_file_ingestor_reads_directory(tmp_path):
    """FileIngestor should read all supported files in a directory."""
    (tmp_path / "a.md").write_text("Post A about venture capital.")
    (tmp_path / "b.txt").write_text("Post B about startups.")
    (tmp_path / "c.py").write_text("# Not a content file")

    session = get_session()
    source = ContentSource(
        platform="file",
        identifier=str(tmp_path),
        display_name="test-dir",
    )
    session.add(source)
    session.commit()

    ingestor = FileIngestor()
    contents = ingestor.ingest(source)

    assert len(contents) == 2  # .md and .txt only, not .py


def test_file_ingestor_skips_empty(tmp_path):
    """FileIngestor should skip empty files."""
    (tmp_path / "empty.md").write_text("")

    session = get_session()
    source = ContentSource(
        platform="file",
        identifier=str(tmp_path / "empty.md"),
        display_name="empty",
    )
    session.add(source)
    session.commit()

    ingestor = FileIngestor()
    contents = ingestor.ingest(source)

    assert len(contents) == 0


def test_linkedin_ingestor_json(tmp_path):
    """LinkedInIngestor should parse JSON export."""
    data = [
        {"ShareCommentary": "My thoughts on AI safety", "Date": "2024-01-15T10:00:00"},
        {"ShareCommentary": "VC market analysis", "Date": "2024-02-20T14:30:00"},
        {"ShareCommentary": "", "Date": "2024-03-01T09:00:00"},  # Empty, should skip
    ]
    json_file = tmp_path / "shares.json"
    json_file.write_text(json.dumps(data))

    session = get_session()
    source = ContentSource(
        platform="linkedin",
        identifier=str(json_file),
        display_name="LinkedIn",
    )
    session.add(source)
    session.commit()

    ingestor = LinkedInIngestor()
    contents = ingestor.ingest(source)

    assert len(contents) == 2  # Skips the empty one
    assert "AI safety" in contents[0].body


def test_content_hash_deduplication():
    """Same text should produce the same hash."""
    text = "This is my post about startups."
    hash1 = Content.compute_hash(text)
    hash2 = Content.compute_hash(text)
    assert hash1 == hash2

    different_hash = Content.compute_hash("Different text entirely.")
    assert hash1 != different_hash
