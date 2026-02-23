"""Web search and RSS scanning for content discovery."""

import logging
from datetime import datetime

import atoma
import httpx

from ventureoracle.config import get_settings
from ventureoracle.db.models import Content, DiscoveredContent

logger = logging.getLogger(__name__)


def scan_rss_feed(feed_url: str, since: datetime | None = None) -> list[DiscoveredContent]:
    """Scan an RSS feed for new content."""
    logger.debug("Scanning RSS feed: %s", feed_url)
    response = httpx.get(feed_url, timeout=15, follow_redirects=True)
    response.raise_for_status()
    raw = response.content

    discoveries = []

    try:
        feed = atoma.parse_rss_bytes(raw)
        for item in feed.items:
            if since and item.pub_date and item.pub_date < since:
                continue

            title = item.title or ""
            if not title.strip():
                continue

            summary = item.description or ""
            url = item.link or ""

            discoveries.append(DiscoveredContent(
                source_type="rss",
                url=url,
                title=title,
                summary=summary[:1000],
                content_hash=Content.compute_hash(title + url),
            ))
    except atoma.FeedParseError:
        feed = atoma.parse_atom_bytes(raw)
        for entry in feed.entries:
            pub = entry.published or entry.updated
            if since and pub and pub < since:
                continue

            title = entry.title.value if hasattr(entry.title, "value") else str(entry.title or "")
            if not title.strip():
                continue

            summary = ""
            if entry.summary:
                summary = entry.summary.value if hasattr(entry.summary, "value") else str(entry.summary)

            url = entry.links[0].href if entry.links else ""

            discoveries.append(DiscoveredContent(
                source_type="rss",
                url=url,
                title=title,
                summary=summary[:1000],
                content_hash=Content.compute_hash(title + url),
            ))

    logger.info("Discovered %d items from RSS feed %s", len(discoveries), feed_url)
    return discoveries


def search_brave(query: str, count: int = 10) -> list[DiscoveredContent]:
    """Search the web using Brave Search API."""
    settings = get_settings()
    if not settings.brave_api_key:
        logger.warning("No Brave API key configured, skipping web search")
        return []

    response = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": count},
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": settings.brave_api_key,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    discoveries = []
    for result in data.get("web", {}).get("results", []):
        discoveries.append(DiscoveredContent(
            source_type="web_search",
            url=result.get("url", ""),
            title=result.get("title", ""),
            summary=result.get("description", "")[:1000],
            content_hash=Content.compute_hash(result.get("url", "")),
        ))

    return discoveries
