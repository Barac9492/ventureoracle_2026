"""Abstract base class for platform content ingestors."""

from abc import ABC, abstractmethod
from datetime import datetime

from ventureoracle.db.models import Content, ContentSource


class BaseIngestor(ABC):
    """Abstract base for all content ingestors."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform identifier, e.g., 'linkedin'."""
        ...

    @abstractmethod
    def ingest(self, source: ContentSource, since: datetime | None = None) -> list[Content]:
        """Fetch and return normalized Content objects from the platform."""
        ...
