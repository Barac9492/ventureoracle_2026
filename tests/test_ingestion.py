"""Tests for content ingestion."""

import json
from pathlib import Path

from ventureoracle.db.database import get_session
from ventureoracle.db.models import Content, ContentSource
from ventureoracle.ingestion.file_import import FileIngestor
from ventureoracle.ingestion.linkedin import LinkedInIngestor
from ventureoracle.ingestion.rss import RssIngestor
from ventureoracle.ingestion.substack import SubstackIngestor


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


class MockHttpxResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


def test_rss_ingestor(monkeypatch):
    """RssIngestor should parse RSS XML correctly."""
    rss_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Test Blog</title>
        <link>http://test.com</link>
        <description>Test Blog Description</description>
        <item>
          <title>Test Post 1</title>
          <link>http://test.com/post1</link>
          <description>This is the first test post.</description>
          <pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate>
          <guid>http://test.com/post1</guid>
        </item>
      </channel>
    </rss>
    """

    def mock_get(*args, **kwargs):
        return MockHttpxResponse(rss_xml)

    monkeypatch.setattr("httpx.get", mock_get)

    session = get_session()
    source = ContentSource(
        platform="rss",
        identifier="http://test.com/feed",
        display_name="Test RSS",
    )
    session.add(source)
    session.commit()

    ingestor = RssIngestor()
    contents = ingestor.ingest(source)

    assert len(contents) == 1
    assert contents[0].title == "Test Post 1"
    assert "first test post" in contents[0].body
    assert contents[0].url == "http://test.com/post1"


def test_substack_ingestor(monkeypatch):
    """SubstackIngestor should parse Substack RSS identical to generic RSS."""
    rss_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Substack Blog</title>
        <item>
          <title>Substack Post</title>
          <link>http://substack.com/post1</link>
          <description>Substack body content.</description>
        </item>
      </channel>
    </rss>
    """

    def mock_get(*args, **kwargs):
        return MockHttpxResponse(rss_xml)

    monkeypatch.setattr("httpx.get", mock_get)

    session = get_session()
    source = ContentSource(
        platform="substack",
        identifier="http://substack.com/feed",
        display_name="Test Substack",
    )
    session.add(source)
    session.commit()

    ingestor = SubstackIngestor()
    contents = ingestor.ingest(source)

    assert len(contents) == 1
    assert contents[0].title == "Substack Post"
    assert "Substack body" in contents[0].body
