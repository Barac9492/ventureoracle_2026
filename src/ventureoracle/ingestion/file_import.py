"""Local file ingestor for Markdown, plain text, and other files."""

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

from ventureoracle.db.models import Content, ContentSource
from ventureoracle.ingestion.base import BaseIngestor


class FileIngestor(BaseIngestor):
    """Ingest content from local files (Markdown, plain text)."""

    SUPPORTED_EXTENSIONS = {".md", ".txt", ".markdown", ".rst"}

    @property
    def platform_name(self) -> str:
        return "file"

    def ingest(self, source: ContentSource, since: datetime | None = None) -> list[Content]:
        """Read local files and return Content objects."""
        path = Path(source.identifier)
        contents = []

        if path.is_file():
            content = self._read_file(source, path)
            if content:
                contents.append(content)
        elif path.is_dir():
            for ext in self.SUPPORTED_EXTENSIONS:
                for file_path in path.glob(f"*{ext}"):
                    content = self._read_file(source, file_path)
                    if content:
                        contents.append(content)

        logger.info("Ingested %d files from %s", len(contents), path)
        return contents

    def _read_file(self, source: ContentSource, path: Path) -> Content | None:
        """Read a single file and return a Content object."""
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return None

        body = path.read_text(encoding="utf-8").strip()
        if not body:
            return None

        return Content(
            source_id=source.id,
            title=path.stem,
            body=body,
            word_count=len(body.split()),
            content_hash=Content.compute_hash(body),
        )
