"""Topic recommendation engine — matches discoveries to user profile."""

import json

from ventureoracle.db.models import AuthorProfile, DiscoveredContent, TopicRecommendation
from ventureoracle.llm.client import ask_claude_json

RECOMMENDATION_SYSTEM = """You are a content strategist helping an expert writer find their next
great topic. You understand their style, interests, and audience."""

RECOMMENDATION_PROMPT = """Given this author's profile and recent discoveries, recommend writing topics.

AUTHOR PROFILE:
Voice: {voice}
Themes: {themes}
Interests: {interests}

RECENT DISCOVERIES:
{discoveries}

Recommend {count} writing topics that would resonate with this author's expertise and audience.

Respond with a JSON object:
{{
  "recommendations": [
    {{
      "title": "proposed article title",
      "rationale": "why this topic fits this author",
      "source_urls": ["urls that inspired this"],
      "relevance": 0.0-1.0
    }}
  ]
}}"""


def recommend_topics(
    profile: AuthorProfile,
    discoveries: list[DiscoveredContent],
    count: int = 5,
) -> list[TopicRecommendation]:
    """Generate topic recommendations based on profile and discoveries."""
    discovery_text = "\n".join(
        f"- [{d.title}]({d.url}): {d.summary[:200]}" for d in discoveries[:20]
    )

    prompt = RECOMMENDATION_PROMPT.format(
        voice=profile.voice_description or "Not yet analyzed",
        themes=json.dumps(profile.themes) if profile.themes else "Not yet analyzed",
        interests=json.dumps(profile.interests) if profile.interests else "Not yet analyzed",
        discoveries=discovery_text,
        count=count,
    )

    response = ask_claude_json(prompt, system=RECOMMENDATION_SYSTEM)
    data = json.loads(response)

    recommendations = []
    for rec in data.get("recommendations", []):
        topic = TopicRecommendation(
            title=rec.get("title", ""),
            rationale=rec.get("rationale", ""),
            source_urls=rec.get("source_urls", []),
            relevance=rec.get("relevance", 0.5),
        )
        recommendations.append(topic)

    return recommendations
