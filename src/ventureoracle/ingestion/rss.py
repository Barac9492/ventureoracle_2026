"""Generic RSS/Atom feed ingestor using atoma."""

from datetime import datetime

import atoma
import httpx

from ventureoracle.db.models import Content, ContentSource
from ventureoracle.ingestion.base import BaseIngestor


class RssIngestor(BaseIngestor):
    """Ingest content from any RSS/Atom feed."""

    @property
    def platform_name(self) -> str:
        return "rss"

    def ingest(self, source: ContentSource, since: datetime | None = None) -> list[Content]:
        """Fetch entries from an RSS feed and return Content objects."""
        response = httpx.get(source.identifier, timeout=15, follow_redirects=True)
        response.raise_for_status()
        raw = response.content

        # Try RSS first, then Atom
        try:
            return self._parse_rss(raw, source, since)
        except atoma.FeedParseError:
            return self._parse_atom(raw, source, since)

    def _parse_rss(
        self, raw: bytes, source: ContentSource, since: datetime | None
    ) -> list[Content]:
        feed = atoma.parse_rss_bytes(raw)
        contents = []

        for item in feed.items:
            published_at = item.pub_date
            if since and published_at and published_at < since:
                continue

            body = item.description or ""
            if hasattr(item, "content_encoded") and item.content_encoded:
                body = item.content_encoded
            if not body.strip():
                continue

            contents.append(Content(
                source_id=source.id,
                external_id=item.guid or item.link,
                url=item.link or "",
                title=item.title or "",
                body=body,
                author=item.author or "",
                published_at=published_at,
                word_count=len(body.split()),
                content_hash=Content.compute_hash(body),
            ))

        return contents

    def _parse_atom(
        self, raw: bytes, source: ContentSource, since: datetime | None
    ) -> list[Content]:
        feed = atoma.parse_atom_bytes(raw)
        contents = []

        for entry in feed.entries:
            published_at = entry.published or entry.updated
            if since and published_at and published_at < since:
                continue

            body = ""
            if entry.content:
                body = entry.content.value if hasattr(entry.content, "value") else str(entry.content)
            elif entry.summary:
                body = entry.summary.value if hasattr(entry.summary, "value") else str(entry.summary)
            if not body.strip():
                continue

            url = entry.links[0].href if entry.links else ""

            contents.append(Content(
                source_id=source.id,
                external_id=entry.id or url,
                url=url,
                title=entry.title.value if hasattr(entry.title, "value") else str(entry.title or ""),
                body=body,
                author=entry.authors[0].name if entry.authors else "",
                published_at=published_at,
                word_count=len(body.split()),
                content_hash=Content.compute_hash(body),
            ))

        return contents
