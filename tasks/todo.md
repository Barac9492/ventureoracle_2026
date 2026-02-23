# VentureOracle — Content Engine & Prediction Platform

## Vision
A personal content engine that:
1. Ingests your writings from LinkedIn, Substack, and other platforms
2. Learns your writing style, tone, themes, and interests
3. Discovers ideas across the web that match your interests
4. Recommends topics to write about
5. Predicts trends and outcomes based on your domain expertise

---

## Architecture

### Tech Stack
- **Language**: Python 3.11+
- **LLM**: Claude API (Anthropic SDK) — style analysis, content generation, predictions
- **Database**: SQLite (local-first, simple) via SQLAlchemy
- **Web Scraping**: `httpx` + `beautifulsoup4` + `feedparser` (RSS)
- **CLI**: `click`
- **Config**: YAML-based config files
- **Testing**: `pytest`
- **Task Scheduling**: `schedule` (lightweight, no infra needed)

### Directory Structure
```
ventureoracle_2026/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── tasks/
│   ├── todo.md
│   └── lessons.md
├── config/
│   └── settings.yaml          # API keys, platform configs, interests
├── src/
│   └── ventureoracle/
│       ├── __init__.py
│       ├── cli.py              # Click CLI entry point
│       ├── config.py           # Settings loader
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py       # SQLAlchemy models
│       │   └── database.py     # DB connection & session management
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract base class for platform connectors
│       │   ├── linkedin.py     # LinkedIn scraper/API connector
│       │   ├── substack.py     # Substack RSS/API connector
│       │   └── rss.py          # Generic RSS feed connector
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── style.py        # Writing style profiler (via Claude)
│       │   └── profile.py      # Author profile builder (themes, interests)
│       ├── discovery/
│       │   ├── __init__.py
│       │   ├── search.py       # Web search for trending content
│       │   ├── scorer.py       # Relevance scoring against user profile
│       │   └── recommender.py  # Topic recommendation engine
│       └── prediction/
│           ├── __init__.py
│           ├── engine.py       # Prediction engine core (Claude-powered)
│           ├── tracker.py      # Track predictions over time
│           └── calibration.py  # Score prediction accuracy
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_ingestion.py
    ├── test_analysis.py
    ├── test_discovery.py
    └── test_prediction.py
```

### Data Models

#### Content (ingested posts)
| Field         | Type     | Description                          |
|---------------|----------|--------------------------------------|
| id            | UUID     | Primary key                          |
| platform      | str      | "linkedin", "substack", etc.         |
| url           | str      | Original URL                         |
| title         | str      | Post title (if applicable)           |
| body          | text     | Full post content                    |
| published_at  | datetime | When the post was published          |
| ingested_at   | datetime | When we ingested it                  |
| metadata      | JSON     | Platform-specific data (likes, etc.) |

#### AuthorProfile (learned style)
| Field             | Type     | Description                          |
|-------------------|----------|--------------------------------------|
| id                | UUID     | Primary key                          |
| version           | int      | Profile version (rebuilds over time) |
| writing_style     | JSON     | Tone, vocabulary, sentence structure |
| themes            | JSON     | Key themes and topics                |
| interests         | JSON     | Ranked interest areas                |
| voice_description | text     | Claude-generated style description   |
| built_at          | datetime | When this profile was generated      |

#### TopicRecommendation
| Field         | Type     | Description                          |
|---------------|----------|--------------------------------------|
| id            | UUID     | Primary key                          |
| title         | str      | Recommended topic                    |
| rationale     | text     | Why this topic fits the user         |
| source_urls   | JSON     | Where the idea came from             |
| relevance     | float    | 0-1 relevance score                  |
| status        | str      | "new", "accepted", "rejected", "written" |
| created_at    | datetime | When recommended                     |

#### Prediction
| Field           | Type     | Description                          |
|-----------------|----------|--------------------------------------|
| id              | UUID     | Primary key                          |
| claim           | text     | The prediction statement             |
| confidence      | float    | 0-1 confidence score                 |
| reasoning       | text     | Why this prediction was made         |
| domain          | str      | Category (tech, market, policy, etc.)|
| timeframe       | str      | When it should resolve               |
| source_content  | JSON     | Content IDs that informed this       |
| outcome         | str      | "pending", "correct", "incorrect", "partial" |
| created_at      | datetime | When predicted                       |
| resolved_at     | datetime | When outcome was determined          |

---

## Implementation Phases

### Phase 1: Foundation (Current Sprint)
- [x] Create CLAUDE.md
- [x] Set up Python project (pyproject.toml, dependencies)
- [x] Create database models and migrations
- [x] Build config system (settings.yaml loader)
- [x] Build Substack RSS ingestion connector
- [x] Build generic RSS feed connector
- [x] Build LinkedIn connector (scraper-based)
- [x] Build CLI skeleton with `ingest` command
- [x] Write tests for ingestion

### Phase 2: Style Learning & Profiling
- [x] Build writing style analyzer (Claude-powered)
- [x] Build author profile builder (aggregate across all content)
- [x] Add `profile` CLI command (show learned profile)
- [x] Write tests for analysis

### Phase 3: Discovery & Recommendations
- [x] Build web content search (trending topics, news)
- [x] Build relevance scorer (match content to user profile)
- [x] Build topic recommender
- [x] Add `discover` CLI command
- [x] Write tests for discovery

### Phase 4: Prediction Engine
- [x] Build prediction engine core (Claude-powered trend analysis)
- [x] Build prediction tracker (store and monitor predictions)
- [x] Build calibration system (score accuracy over time)
- [x] Add `predict` CLI command
- [x] Add `predictions` CLI command (view/resolve predictions)
- [x] Write tests for prediction

### Phase 5: Polish & Integration
- [x] Add `dashboard` command (summary view of all features)
- [x] Add scheduling (auto-ingest, auto-discover)
- [x] Improve error handling and logging
- [x] End-to-end integration tests

---

## CLI Commands (Planned)

```
ventureoracle ingest [--platform linkedin|substack|rss] [--url URL]
ventureoracle profile [--rebuild]
ventureoracle discover [--count N]
ventureoracle predict [--domain DOMAIN]
ventureoracle predictions [--status pending|resolved] [--resolve ID]
ventureoracle dashboard
```

---

## Review

### Phase 1 Review
Foundation complete: DB models, config system, ingestion connectors (RSS, Substack, LinkedIn, file), CLI skeleton, LLM client. 19 tests passing.

### Phase 2 Review
Style learning and profiling complete. `analysis/style.py` provides `analyze_style()`, `extract_themes()`, and `build_profile()` — all Claude-powered via `ask_claude_json`. CLI `profile show` and `profile analyze` commands functional. 10 new tests added in `test_analysis.py` covering: `_format_samples` (basic, truncation, max limit), style analysis, theme extraction, profile building with DB persistence, and CLI integration. Full suite: 29/29 passing.

### Phase 3 Review
Discovery and recommendations complete. `discovery/search.py` provides `scan_rss_feed()` and `search_brave()`. `discovery/recommender.py` provides `recommend_topics()` (Claude-powered, includes relevance scoring). CLI `discover scan`, `discover search`, and `discover topics` commands functional. 11 new tests added in `test_discovery.py` covering: RSS scanning, hash deduplication, Brave search (with/without API key), topic recommendations (with/without data), and all 5 CLI edge cases. Full suite: 40/40 passing.

### Phase 4 Review
Prediction engine complete. `prediction/engine.py` provides `generate_predictions()` (Claude-powered). `prediction/tracker.py` provides `list_predictions()`, `resolve_prediction()`, and `get_calibration_stats()` with by-domain breakdown. CLI has `predict generate`, `predict list`, `predict resolve` (with partial ID matching), and `predict calibration`. 18 new tests in `test_prediction.py` covering: prediction generation, tracker CRUD, calibration math (overall + by-domain), outcome validation, and all CLI commands including edge cases. Full suite: 58/58 passing.

### Phase 5 Review
Polish and integration complete. Added `logging` throughout all modules (9 files) with `--verbose` flag on CLI for DEBUG level. Added try/except error handling around all external calls (Claude API, HTTP) in 5 CLI commands with user-friendly error messages. Created `scheduler.py` with `auto_ingest()` and `auto_discover()` tasks + `ventureoracle run` CLI command using `schedule` library. Added `schedule>=1.2` to deps. Created 3 end-to-end integration tests in `test_integration.py`: full pipeline (ingest->profile->discover->recommend->predict), predict without discoveries, and resolve+calibrate flow. Dashboard was already implemented. Final suite: **61/61 passing**. All 5 phases complete.
