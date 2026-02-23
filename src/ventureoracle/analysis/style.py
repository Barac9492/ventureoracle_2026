"""Writing style analyzer — uses Claude to profile an author's writing."""

import json

from ventureoracle.analysis.prompts import (
    STYLE_ANALYSIS_PROMPT,
    STYLE_ANALYSIS_SYSTEM,
    THEME_EXTRACTION_PROMPT,
    THEME_EXTRACTION_SYSTEM,
)
from ventureoracle.db.database import get_session
from ventureoracle.db.models import AuthorProfile, Content
from ventureoracle.llm.client import ask_claude_json


def analyze_style(contents: list[Content]) -> dict:
    """Analyze writing style from a list of content pieces."""
    samples = _format_samples(contents)
    prompt = STYLE_ANALYSIS_PROMPT.format(samples=samples)
    response = ask_claude_json(prompt, system=STYLE_ANALYSIS_SYSTEM)
    return json.loads(response)


def extract_themes(contents: list[Content]) -> dict:
    """Extract themes and interests from content."""
    samples = _format_samples(contents)
    prompt = THEME_EXTRACTION_PROMPT.format(samples=samples)
    response = ask_claude_json(prompt, system=THEME_EXTRACTION_SYSTEM)
    return json.loads(response)


def build_profile(contents: list[Content]) -> AuthorProfile:
    """Build a complete author profile from content and save to DB."""
    style = analyze_style(contents)
    themes = extract_themes(contents)

    profile = AuthorProfile(
        writing_style=style,
        themes=themes.get("themes", []),
        interests=themes.get("interests", []),
        voice_description=style.get("voice_description", ""),
        sample_count=len(contents),
    )

    session = get_session()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def _format_samples(contents: list[Content], max_samples: int = 15) -> str:
    """Format content pieces into a string for prompts."""
    pieces = contents[:max_samples]
    formatted = []
    for i, c in enumerate(pieces, 1):
        title = f" — {c.title}" if c.title else ""
        formatted.append(f"--- Sample {i}{title} ---\n{c.body[:3000]}")
    return "\n\n".join(formatted)
