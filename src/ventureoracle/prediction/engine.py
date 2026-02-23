"""Prediction engine — Claude-powered trend analysis and forecasting."""

import json

from ventureoracle.db.models import AuthorProfile, DiscoveredContent, Prediction
from ventureoracle.llm.client import ask_claude_json

PREDICTION_SYSTEM = """You are a strategic analyst and forecaster. You synthesize domain expertise
with current signals to generate well-reasoned predictions. Each prediction must include clear
reasoning, confidence calibration, and counterarguments. Be intellectually honest about uncertainty."""

PREDICTION_PROMPT = """Based on this domain expert's knowledge and recent signals, generate predictions.

EXPERT PROFILE:
Voice: {voice}
Domain Themes: {themes}
Key Interests: {interests}

RECENT SIGNALS FROM THE FIELD:
{signals}

Generate {count} predictions about trends, outcomes, or developments in this expert's domain.
For each prediction, provide calibrated confidence (be honest — if uncertain, say so).

Respond with a JSON object:
{{
  "predictions": [
    {{
      "domain": "category (e.g., AI, venture capital, fintech)",
      "claim": "the specific prediction statement",
      "reasoning": "chain of reasoning that supports this prediction",
      "confidence": 0.0-1.0,
      "timeframe": "when this should resolve (e.g., '6 months', '1 year')",
      "evidence": ["supporting signal 1", "supporting signal 2"],
      "counterarguments": "key risks or reasons this could be wrong"
    }}
  ]
}}"""


def generate_predictions(
    profile: AuthorProfile,
    discoveries: list[DiscoveredContent],
    count: int = 3,
) -> list[Prediction]:
    """Generate predictions based on user profile and discovered trends."""
    signals_text = "\n".join(
        f"- [{d.title}]({d.url}): {d.summary[:200]}" for d in discoveries[:20]
    )

    prompt = PREDICTION_PROMPT.format(
        voice=profile.voice_description or "Not yet analyzed",
        themes=json.dumps(profile.themes) if profile.themes else "Not yet analyzed",
        interests=json.dumps(profile.interests) if profile.interests else "Not yet analyzed",
        signals=signals_text or "No recent signals available.",
        count=count,
    )

    response = ask_claude_json(prompt, system=PREDICTION_SYSTEM)
    data = json.loads(response)

    predictions = []
    for pred in data.get("predictions", []):
        prediction = Prediction(
            domain=pred.get("domain", "general"),
            claim=pred.get("claim", ""),
            reasoning=pred.get("reasoning", ""),
            confidence=pred.get("confidence", 0.5),
            timeframe=pred.get("timeframe", "unknown"),
            evidence=pred.get("evidence", []),
            counterarguments=pred.get("counterarguments", ""),
        )
        predictions.append(prediction)

    return predictions
