"""Scheduler — periodic auto-ingest and auto-discover tasks."""

import logging
import time

import schedule
from sqlalchemy import select

from ventureoracle.db.database import get_session
from ventureoracle.db.models import ContentSource, DiscoveredContent

logger = logging.getLogger(__name__)


def auto_ingest():
    """Re-ingest all saved content sources."""
    from ventureoracle.ingestion.file_import import FileIngestor
    from ventureoracle.ingestion.linkedin import LinkedInIngestor
    from ventureoracle.ingestion.rss import RssIngestor
    from ventureoracle.ingestion.substack import SubstackIngestor

    ingestors = {
        "rss": RssIngestor(),
        "substack": SubstackIngestor(),
        "linkedin": LinkedInIngestor(),
        "file": FileIngestor(),
    }

    session = get_session()
    sources = list(session.execute(select(ContentSource)).scalars().all())

    if not sources:
        logger.info("No content sources to auto-ingest")
        return

    total = 0
    for source in sources:
        ingestor = ingestors.get(source.platform)
        if not ingestor:
            logger.warning("No ingestor for platform: %s", source.platform)
            continue

        try:
            contents = ingestor.ingest(source, since=source.last_ingested_at)
            # Deduplicate by content_hash
            existing_hashes = {
                row[0]
                for row in session.execute(
                    select(ContentSource.id).where(ContentSource.id == source.id)
                ).all()
            }
            new_contents = [c for c in contents if c.content_hash not in existing_hashes]
            for c in new_contents:
                session.add(c)
            total += len(new_contents)
            logger.info("Auto-ingested %d new items from %s", len(new_contents), source.display_name)
        except Exception as e:
            logger.error("Auto-ingest failed for %s: %s", source.display_name, e)

    session.commit()
    logger.info("Auto-ingest complete: %d new items total", total)


def auto_discover():
    """Re-scan RSS sources for new discoveries."""
    from ventureoracle.discovery.search import scan_rss_feed

    session = get_session()
    sources = list(
        session.execute(
            select(ContentSource).where(ContentSource.platform.in_(["rss", "substack"]))
        ).scalars().all()
    )

    if not sources:
        logger.info("No RSS sources to auto-discover")
        return

    total = 0
    for source in sources:
        try:
            discoveries = scan_rss_feed(source.identifier)
            # Deduplicate by content_hash
            existing = {
                row[0]
                for row in session.execute(select(DiscoveredContent.content_hash)).all()
            }
            new_discoveries = [d for d in discoveries if d.content_hash not in existing]
            for d in new_discoveries:
                session.add(d)
            total += len(new_discoveries)
            logger.info("Auto-discovered %d new items from %s", len(new_discoveries), source.display_name)
        except Exception as e:
            logger.error("Auto-discover failed for %s: %s", source.display_name, e)

    session.commit()
    logger.info("Auto-discover complete: %d new items total", total)


def start_scheduler(ingest_hours: int = 6, discover_hours: int = 12):
    """Start the scheduler loop with configurable intervals."""
    logger.info(
        "Starting scheduler: auto-ingest every %dh, auto-discover every %dh",
        ingest_hours,
        discover_hours,
    )

    schedule.every(ingest_hours).hours.do(auto_ingest)
    schedule.every(discover_hours).hours.do(auto_discover)

    # Run once immediately
    auto_ingest()
    auto_discover()

    while True:
        schedule.run_pending()
        time.sleep(60)
