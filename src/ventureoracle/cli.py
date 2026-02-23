"""VentureOracle CLI — Click-based command interface."""

import json
import logging
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)

from ventureoracle.db.database import get_session, init_db
from ventureoracle.db.models import (
    AuthorProfile,
    Content,
    ContentSource,
    DiscoveredContent,
    Prediction,
    TopicRecommendation,
)

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """VentureOracle — Personal content engine, idea discovery, and prediction platform."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    init_db()


# ---------------------------------------------------------------------------
# Ingest commands
# ---------------------------------------------------------------------------


@cli.group()
def ingest():
    """Ingest content from various platforms."""
    pass


@ingest.command("rss")
@click.argument("feed_url")
@click.option("--name", default=None, help="Display name for this source")
def ingest_rss(feed_url: str, name: str | None):
    """Ingest content from an RSS/Atom feed."""
    from ventureoracle.ingestion.rss import RssIngestor

    session = get_session()
    source = ContentSource(
        platform="rss",
        identifier=feed_url,
        display_name=name or feed_url,
        is_own_content=True,
    )
    session.add(source)
    session.commit()

    ingestor = RssIngestor()
    contents = ingestor.ingest(source)

    _save_contents(session, contents)
    console.print(f"[green]Ingested {len(contents)} items from RSS feed[/green]")


@ingest.command("substack")
@click.argument("newsletter_url")
@click.option("--name", default=None, help="Display name for this newsletter")
def ingest_substack(newsletter_url: str, name: str | None):
    """Ingest content from a Substack newsletter."""
    from ventureoracle.ingestion.substack import SubstackIngestor

    # Ensure URL ends with /feed
    feed_url = newsletter_url.rstrip("/")
    if not feed_url.endswith("/feed"):
        feed_url += "/feed"

    session = get_session()
    source = ContentSource(
        platform="substack",
        identifier=feed_url,
        display_name=name or newsletter_url,
        is_own_content=True,
    )
    session.add(source)
    session.commit()

    ingestor = SubstackIngestor()
    contents = ingestor.ingest(source)

    _save_contents(session, contents)
    console.print(f"[green]Ingested {len(contents)} posts from Substack[/green]")


@ingest.command("linkedin")
@click.argument("path")
@click.option("--name", default="LinkedIn", help="Display name")
def ingest_linkedin(path: str, name: str):
    """Ingest content from a LinkedIn data export (JSON file or directory)."""
    from ventureoracle.ingestion.linkedin import LinkedInIngestor

    session = get_session()
    source = ContentSource(
        platform="linkedin",
        identifier=path,
        display_name=name,
        is_own_content=True,
    )
    session.add(source)
    session.commit()

    ingestor = LinkedInIngestor()
    contents = ingestor.ingest(source)

    _save_contents(session, contents)
    console.print(f"[green]Ingested {len(contents)} posts from LinkedIn export[/green]")


@ingest.command("file")
@click.argument("path")
@click.option("--name", default=None, help="Display name")
def ingest_file(path: str, name: str | None):
    """Ingest content from local files (Markdown, text)."""
    from ventureoracle.ingestion.file_import import FileIngestor

    session = get_session()
    source = ContentSource(
        platform="file",
        identifier=path,
        display_name=name or path,
        is_own_content=True,
    )
    session.add(source)
    session.commit()

    ingestor = FileIngestor()
    contents = ingestor.ingest(source)

    _save_contents(session, contents)
    console.print(f"[green]Ingested {len(contents)} files[/green]")


# ---------------------------------------------------------------------------
# Profile commands
# ---------------------------------------------------------------------------


@cli.group()
def profile():
    """Manage your author profile."""
    pass


@profile.command("show")
def profile_show():
    """Display your current author profile."""
    from sqlalchemy import select

    session = get_session()
    prof = session.execute(
        select(AuthorProfile).order_by(AuthorProfile.built_at.desc())
    ).scalar_one_or_none()

    if not prof:
        console.print("[yellow]No profile yet. Run 'ventureoracle profile analyze' first.[/yellow]")
        return

    console.print(Panel(f"[bold]Author Profile[/bold] (v{prof.version}, {prof.sample_count} samples)"))

    if prof.voice_description:
        console.print(Panel(prof.voice_description, title="Voice"))

    if prof.writing_style:
        console.print(Panel(json.dumps(prof.writing_style, indent=2), title="Writing Style"))

    if prof.themes:
        console.print(Panel(json.dumps(prof.themes, indent=2), title="Themes"))

    if prof.interests:
        console.print(Panel(json.dumps(prof.interests, indent=2), title="Interests"))


@profile.command("analyze")
def profile_analyze():
    """Analyze all ingested content and build/rebuild your profile."""
    from sqlalchemy import select

    from ventureoracle.analysis.style import build_profile

    session = get_session()
    contents = list(session.execute(select(Content)).scalars().all())

    if not contents:
        console.print("[yellow]No content ingested yet. Use 'ventureoracle ingest' first.[/yellow]")
        return

    console.print(f"Analyzing {len(contents)} pieces of content...")
    try:
        prof = build_profile(contents)
    except Exception as e:
        logger.error("Profile analysis failed: %s", e)
        console.print(f"[red]Error building profile: {e}[/red]")
        return
    console.print(f"[green]Profile built! Version {prof.version}, {prof.sample_count} samples analyzed.[/green]")


# ---------------------------------------------------------------------------
# Discover commands
# ---------------------------------------------------------------------------


@cli.group()
def discover():
    """Discover ideas and get topic recommendations."""
    pass


@discover.command("scan")
@click.argument("feed_url")
def discover_scan(feed_url: str):
    """Scan an RSS feed for interesting content."""
    from ventureoracle.discovery.search import scan_rss_feed

    try:
        discoveries = scan_rss_feed(feed_url)
    except Exception as e:
        logger.error("RSS scan failed: %s", e)
        console.print(f"[red]Error scanning feed: {e}[/red]")
        return
    session = get_session()

    for d in discoveries:
        session.add(d)
    session.commit()

    console.print(f"[green]Discovered {len(discoveries)} items[/green]")

    table = Table(title="Discoveries")
    table.add_column("Title", style="cyan", max_width=60)
    table.add_column("URL", style="blue", max_width=40)

    for d in discoveries[:10]:
        table.add_row(d.title, d.url)

    console.print(table)


@discover.command("search")
@click.argument("query")
@click.option("--count", default=10, help="Number of results")
def discover_search(query: str, count: int):
    """Search the web for content matching a query (requires Brave API key)."""
    from ventureoracle.discovery.search import search_brave

    try:
        discoveries = search_brave(query, count=count)
    except Exception as e:
        logger.error("Web search failed: %s", e)
        console.print(f"[red]Error searching: {e}[/red]")
        return
    if not discoveries:
        console.print("[yellow]No results. Check your BRAVE_API_KEY in .env[/yellow]")
        return

    session = get_session()
    for d in discoveries:
        session.add(d)
    session.commit()

    console.print(f"[green]Found {len(discoveries)} results[/green]")

    table = Table(title=f"Search: {query}")
    table.add_column("Title", style="cyan", max_width=60)
    table.add_column("URL", style="blue", max_width=40)

    for d in discoveries:
        table.add_row(d.title, d.url)

    console.print(table)


@discover.command("topics")
@click.option("--count", default=5, help="Number of recommendations")
def discover_topics(count: int):
    """Get AI-powered topic recommendations based on your profile and discoveries."""
    from sqlalchemy import select

    from ventureoracle.discovery.recommender import recommend_topics

    session = get_session()

    # Get latest profile
    prof = session.execute(
        select(AuthorProfile).order_by(AuthorProfile.built_at.desc())
    ).scalar_one_or_none()

    if not prof:
        console.print("[yellow]No profile yet. Run 'ventureoracle profile analyze' first.[/yellow]")
        return

    # Get recent discoveries
    discoveries = list(
        session.execute(
            select(DiscoveredContent).order_by(DiscoveredContent.discovered_at.desc()).limit(30)
        ).scalars().all()
    )

    if not discoveries:
        console.print("[yellow]No discoveries yet. Run 'ventureoracle discover scan' first.[/yellow]")
        return

    console.print("Generating topic recommendations...")
    try:
        recommendations = recommend_topics(prof, discoveries, count=count)
    except Exception as e:
        logger.error("Topic recommendation failed: %s", e)
        console.print(f"[red]Error generating recommendations: {e}[/red]")
        return

    for rec in recommendations:
        session.add(rec)
    session.commit()

    table = Table(title="Recommended Topics")
    table.add_column("#", style="dim", width=3)
    table.add_column("Topic", style="cyan", max_width=50)
    table.add_column("Relevance", style="green", width=10)
    table.add_column("Rationale", style="white", max_width=50)

    for i, rec in enumerate(recommendations, 1):
        table.add_row(str(i), rec.title, f"{rec.relevance:.0%}", rec.rationale[:80])

    console.print(table)


# ---------------------------------------------------------------------------
# Predict commands
# ---------------------------------------------------------------------------


@cli.group()
def predict():
    """Generate and track predictions."""
    pass


@predict.command("generate")
@click.option("--count", default=3, help="Number of predictions to generate")
def predict_generate(count: int):
    """Generate new predictions based on your expertise and current signals."""
    from sqlalchemy import select

    from ventureoracle.prediction.engine import generate_predictions

    session = get_session()

    prof = session.execute(
        select(AuthorProfile).order_by(AuthorProfile.built_at.desc())
    ).scalar_one_or_none()

    if not prof:
        console.print("[yellow]No profile yet. Run 'ventureoracle profile analyze' first.[/yellow]")
        return

    discoveries = list(
        session.execute(
            select(DiscoveredContent).order_by(DiscoveredContent.discovered_at.desc()).limit(30)
        ).scalars().all()
    )

    console.print("Generating predictions...")
    try:
        predictions = generate_predictions(prof, discoveries, count=count)
    except Exception as e:
        logger.error("Prediction generation failed: %s", e)
        console.print(f"[red]Error generating predictions: {e}[/red]")
        return

    for pred in predictions:
        session.add(pred)
    session.commit()

    for pred in predictions:
        console.print(Panel(
            f"[bold]{pred.claim}[/bold]\n\n"
            f"[dim]Domain:[/dim] {pred.domain}\n"
            f"[dim]Confidence:[/dim] {pred.confidence:.0%}\n"
            f"[dim]Timeframe:[/dim] {pred.timeframe}\n\n"
            f"[dim]Reasoning:[/dim] {pred.reasoning}\n\n"
            f"[dim]Counterarguments:[/dim] {pred.counterarguments}",
            title="Prediction",
        ))

    console.print(f"[green]Generated {len(predictions)} predictions[/green]")


@predict.command("list")
@click.option("--status", default=None, help="Filter by status (active, correct, incorrect)")
def predict_list(status: str | None):
    """List predictions."""
    from ventureoracle.prediction.tracker import list_predictions

    predictions = list_predictions(status=status)

    if not predictions:
        console.print("[yellow]No predictions yet.[/yellow]")
        return

    table = Table(title="Predictions")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Domain", style="blue", width=15)
    table.add_column("Claim", style="cyan", max_width=50)
    table.add_column("Confidence", style="green", width=10)
    table.add_column("Status", width=12)
    table.add_column("Created", style="dim", width=12)

    for pred in predictions:
        status_style = {
            "active": "yellow",
            "correct": "green",
            "incorrect": "red",
            "expired": "dim",
        }.get(pred.status, "white")

        table.add_row(
            pred.id[:8],
            pred.domain,
            pred.claim[:80],
            f"{pred.confidence:.0%}",
            f"[{status_style}]{pred.status}[/{status_style}]",
            pred.created_at.strftime("%Y-%m-%d") if pred.created_at else "",
        )

    console.print(table)


@predict.command("resolve")
@click.argument("prediction_id")
@click.argument("outcome", type=click.Choice(["correct", "incorrect", "partial", "expired"]))
def predict_resolve(prediction_id: str, outcome: str):
    """Resolve a prediction."""
    from ventureoracle.prediction.tracker import resolve_prediction

    # Support partial ID matching
    session = get_session()
    from sqlalchemy import select

    preds = list(session.execute(select(Prediction)).scalars().all())
    match = None
    for p in preds:
        if p.id.startswith(prediction_id):
            match = p
            break

    if not match:
        console.print(f"[red]Prediction not found: {prediction_id}[/red]")
        return

    result = resolve_prediction(match.id, outcome)
    console.print(f"[green]Prediction resolved as: {outcome}[/green]")


@predict.command("calibration")
def predict_calibration():
    """Show prediction accuracy statistics."""
    from ventureoracle.prediction.tracker import get_calibration_stats

    stats = get_calibration_stats()

    console.print(Panel(
        f"Total predictions: {stats['total']}\n"
        f"Resolved: {stats['resolved']}\n"
        f"Correct: {stats.get('correct', 0)}\n"
        f"Overall accuracy: {stats['accuracy']:.0%}" if stats["accuracy"] is not None
        else f"Total predictions: {stats['total']}\nResolved: {stats['resolved']}\nAccuracy: N/A (no resolved predictions)",
        title="Prediction Calibration",
    ))

    if stats.get("by_domain"):
        table = Table(title="Accuracy by Domain")
        table.add_column("Domain", style="cyan")
        table.add_column("Total", width=8)
        table.add_column("Correct", width=8)
        table.add_column("Accuracy", style="green", width=10)

        for domain, domain_stats in stats["by_domain"].items():
            table.add_row(
                domain,
                str(domain_stats["total"]),
                str(domain_stats["correct"]),
                f"{domain_stats['accuracy']:.0%}",
            )

        console.print(table)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@cli.command("dashboard")
def dashboard():
    """Show a summary dashboard of all VentureOracle activity."""
    from sqlalchemy import func, select

    session = get_session()

    content_count = session.execute(select(func.count(Content.id))).scalar() or 0
    source_count = session.execute(select(func.count(ContentSource.id))).scalar() or 0
    discovery_count = session.execute(select(func.count(DiscoveredContent.id))).scalar() or 0
    prediction_count = session.execute(select(func.count(Prediction.id))).scalar() or 0
    recommendation_count = session.execute(select(func.count(TopicRecommendation.id))).scalar() or 0

    prof = session.execute(
        select(AuthorProfile).order_by(AuthorProfile.built_at.desc())
    ).scalar_one_or_none()

    console.print(Panel("[bold]VentureOracle Dashboard[/bold]", style="blue"))

    table = Table(show_header=False)
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Value", style="green")

    table.add_row("Content sources", str(source_count))
    table.add_row("Ingested pieces", str(content_count))
    table.add_row("Profile status", f"v{prof.version} ({prof.sample_count} samples)" if prof else "Not built")
    table.add_row("Discovered content", str(discovery_count))
    table.add_row("Topic recommendations", str(recommendation_count))
    table.add_row("Predictions", str(prediction_count))

    console.print(table)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


@cli.command("run")
@click.option("--ingest-hours", default=6, help="Hours between auto-ingest runs")
@click.option("--discover-hours", default=12, help="Hours between auto-discover runs")
def run_scheduler(ingest_hours: int, discover_hours: int):
    """Start the scheduler for automatic ingestion and discovery."""
    from ventureoracle.scheduler import start_scheduler

    console.print(
        f"[green]Starting scheduler: ingest every {ingest_hours}h, discover every {discover_hours}h[/green]"
    )
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    try:
        start_scheduler(ingest_hours=ingest_hours, discover_hours=discover_hours)
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler stopped.[/yellow]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _save_contents(session, contents: list[Content]):
    """Save contents to DB, skipping duplicates by hash."""
    from sqlalchemy import select

    existing_hashes = set(
        session.execute(select(Content.content_hash)).scalars().all()
    )

    new_contents = [c for c in contents if c.content_hash not in existing_hashes]
    for c in new_contents:
        session.add(c)
    session.commit()

    skipped = len(contents) - len(new_contents)
    if skipped > 0:
        console.print(f"[dim]Skipped {skipped} duplicate(s)[/dim]")


# ---------------------------------------------------------------------------
# API Server
# ---------------------------------------------------------------------------


@cli.group()
def api():
    """Manage the VentureOracle REST API."""
    pass


@api.command("serve")
@click.option("--host", default="127.0.0.1", help="Host interface to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def api_serve(host: str, port: int, reload: bool):
    """Start the FastAPI backend server."""
    import uvicorn
    console.print(f"[green]Starting API server on http://{host}:{port}[/green]")
    uvicorn.run("ventureoracle.api.app:app", host=host, port=port, reload=reload)
