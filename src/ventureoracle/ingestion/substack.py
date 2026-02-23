"""Substack newsletter ingestor via RSS feed."""

from ventureoracle.ingestion.rss import RssIngestor


class SubstackIngestor(RssIngestor):
    """Ingest content from a Substack newsletter.

    Every Substack newsletter exposes an RSS feed at {newsletter_url}/feed.
    This ingestor extends the generic RSS ingestor.
    """

    @property
    def platform_name(self) -> str:
        return "substack"
