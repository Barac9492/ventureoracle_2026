"""Centralized Claude prompt templates for content analysis."""

STYLE_ANALYSIS_SYSTEM = """You are an expert writing analyst. You analyze writing samples to extract
precise characterizations of an author's style, tone, and patterns. Be specific and evidence-based."""

STYLE_ANALYSIS_PROMPT = """Analyze the following writing samples from the same author. Extract their
writing style profile.

WRITING SAMPLES:
{samples}

Respond with a JSON object containing:
{{
  "tone": "description of overall tone (e.g., analytical, conversational, authoritative)",
  "vocabulary_level": "accessible | intermediate | advanced | technical",
  "sentence_structure": "description of typical sentence patterns",
  "rhetorical_devices": ["list", "of", "common", "devices"],
  "signature_phrases": ["characteristic", "phrases", "or", "patterns"],
  "typical_length": "description of typical post length",
  "voice_description": "A 2-3 paragraph description of this author's unique voice that could guide someone to write in their style"
}}"""

THEME_EXTRACTION_SYSTEM = """You are an expert content analyst. You identify recurring themes, topics,
and interests from a body of writing. Be comprehensive and rank by prominence."""

THEME_EXTRACTION_PROMPT = """Analyze the following writing samples and extract the author's key themes
and interests.

WRITING SAMPLES:
{samples}

Respond with a JSON object containing:
{{
  "themes": [
    {{"topic": "theme name", "strength": 0.0-1.0, "subtopics": ["sub1", "sub2"], "evidence": "brief evidence"}}
  ],
  "interests": [
    {{"area": "interest area", "depth": "surface | moderate | deep | expert", "frequency": "how often it appears"}}
  ],
  "worldview": "brief description of the author's perspective and intellectual orientation"
}}"""
