"""LinkedIn content ingestor via data export file."""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

from ventureoracle.db.models import Content, ContentSource
from ventureoracle.ingestion.base import BaseIngestor


class LinkedInIngestor(BaseIngestor):
    """Ingest content from a LinkedIn data export.

    LinkedIn API requires partner-level access, so this ingestor works
    with the data export zip/JSON that any user can download from
    LinkedIn Settings > Get a copy of your data.

    The 'identifier' on ContentSource should be the path to the
    exported Shares.json or Posts directory.
    """

    @property
    def platform_name(self) -> str:
        return "linkedin"

    def ingest(self, source: ContentSource, since: datetime | None = None) -> list[Content]:
        """Parse LinkedIn export files and return Content objects."""
        path = Path(source.identifier)
        contents = []

        if path.suffix == ".json":
            contents = self._parse_json(source, path, since)
        elif path.is_dir():
            for json_file in path.glob("*.json"):
                contents.extend(self._parse_json(source, json_file, since))
        else:
            # Try reading as plain text (one post per file)
            contents = self._parse_text_file(source, path)

        logger.info("Ingested %d items from LinkedIn export at %s", len(contents), path)
        return contents

    def _parse_json(
        self, source: ContentSource, path: Path, since: datetime | None
    ) -> list[Content]:
        """Parse a LinkedIn export JSON file."""
        contents = []
        data = json.loads(path.read_text(encoding="utf-8"))

        # LinkedIn export formats vary; handle common structures
        items = data if isinstance(data, list) else data.get("shares", data.get("posts", []))

        for item in items:
            body = ""
            if isinstance(item, str):
                body = item
            elif isinstance(item, dict):
                body = item.get("ShareCommentary", item.get("text", item.get("body", "")))

            if not body or not body.strip():
                continue

            published_at = None
            if isinstance(item, dict) and "Date" in item:
                try:
                    published_at = datetime.fromisoformat(item["Date"])
                except (ValueError, TypeError):
                    pass

            if since and published_at and published_at < since:
                continue

            content = Content(
                source_id=source.id,
                url=item.get("ShareLink", "") if isinstance(item, dict) else "",
                title="",
                body=body,
                published_at=published_at,
                word_count=len(body.split()),
                content_hash=Content.compute_hash(body),
            )
            contents.append(content)

        return contents

    def _parse_text_file(self, source: ContentSource, path: Path) -> list[Content]:
        """Parse a plain text file as a single post."""
        body = path.read_text(encoding="utf-8").strip()
        if not body:
            return []

        return [
            Content(
                source_id=source.id,
                title=path.stem,
                body=body,
                word_count=len(body.split()),
                content_hash=Content.compute_hash(body),
            )
        ]
