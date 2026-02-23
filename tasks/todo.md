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
- [ ] Set up Python project (pyproject.toml, dependencies)
- [ ] Create database models and migrations
- [ ] Build config system (settings.yaml loader)
- [ ] Build Substack RSS ingestion connector
- [ ] Build generic RSS feed connector
- [ ] Build LinkedIn connector (scraper-based)
- [ ] Build CLI skeleton with `ingest` command
- [ ] Write tests for ingestion

### Phase 2: Style Learning & Profiling
- [ ] Build writing style analyzer (Claude-powered)
- [ ] Build author profile builder (aggregate across all content)
- [ ] Add `profile` CLI command (show learned profile)
- [ ] Write tests for analysis

### Phase 3: Discovery & Recommendations
- [ ] Build web content search (trending topics, news)
- [ ] Build relevance scorer (match content to user profile)
- [ ] Build topic recommender
- [ ] Add `discover` CLI command
- [ ] Write tests for discovery

### Phase 4: Prediction Engine
- [ ] Build prediction engine core (Claude-powered trend analysis)
- [ ] Build prediction tracker (store and monitor predictions)
- [ ] Build calibration system (score accuracy over time)
- [ ] Add `predict` CLI command
- [ ] Add `predictions` CLI command (view/resolve predictions)
- [ ] Write tests for prediction

### Phase 5: Polish & Integration
- [ ] Add `dashboard` command (summary view of all features)
- [ ] Add scheduling (auto-ingest, auto-discover)
- [ ] Improve error handling and logging
- [ ] End-to-end integration tests

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
_To be filled after each phase completion._
