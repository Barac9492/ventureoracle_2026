from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import logging

from ventureoracle.db.database import get_session, init_db
from ventureoracle.db.models import (
    AuthorProfile,
    Content,
    ContentSource,
    DiscoveredContent,
    Prediction,
    TopicRecommendation,
)
from ventureoracle.prediction.tracker import list_predictions

logger = logging.getLogger(__name__)

app = FastAPI(title="VentureOracle API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    content_count = db.execute(select(func.count(Content.id))).scalar() or 0
    source_count = db.execute(select(func.count(ContentSource.id))).scalar() or 0
    discovery_count = db.execute(select(func.count(DiscoveredContent.id))).scalar() or 0
    prediction_count = db.execute(select(func.count(Prediction.id))).scalar() or 0
    recommendation_count = db.execute(select(func.count(TopicRecommendation.id))).scalar() or 0

    prof = db.execute(
        select(AuthorProfile).order_by(AuthorProfile.built_at.desc())
    ).scalar_one_or_none()

    return {
        "metrics": {
            "content_count": content_count,
            "source_count": source_count,
            "discovery_count": discovery_count,
            "prediction_count": prediction_count,
            "recommendation_count": recommendation_count,
        },
        "profile_status": {
            "version": prof.version if prof else None,
            "sample_count": prof.sample_count if prof else 0,
            "built_at": prof.built_at if prof else None,
        }
    }

@app.get("/api/profile")
def get_profile(db: Session = Depends(get_db)):
    prof = db.execute(
        select(AuthorProfile).order_by(AuthorProfile.built_at.desc())
    ).scalar_one_or_none()

    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "id": prof.id,
        "version": prof.version,
        "sample_count": prof.sample_count,
        "voice_description": prof.voice_description,
        "writing_style": prof.writing_style,
        "themes": prof.themes,
        "interests": prof.interests,
        "built_at": prof.built_at,
    }

@app.get("/api/predictions")
def get_predictions(status: str = None):
    # This uses the tracker functionality which manages its own session, but we can just call it
    preds = list_predictions(status=status)
    return [
        {
            "id": p.id,
            "domain": p.domain,
            "claim": p.claim,
            "confidence": p.confidence,
            "status": p.status,
            "created_at": p.created_at,
            "resolved_at": p.resolved_at,
            "reasoning": p.reasoning,
            "counterarguments": p.counterarguments,
            "timeframe": p.timeframe,
            "outcome": p.outcome,
        }
        for p in preds
    ]

@app.get("/api/discoveries")
def get_discoveries(limit: int = 30, db: Session = Depends(get_db)):
    discoveries = list(
        db.execute(
            select(DiscoveredContent).order_by(DiscoveredContent.discovered_at.desc()).limit(limit)
        ).scalars().all()
    )
    
    return [
        {
            "id": d.id,
            "title": d.title,
            "url": d.url,
            "summary": d.summary,
            "platform": d.platform,
            "discovered_at": d.discovered_at,
        }
        for d in discoveries
    ]

@app.get("/api/recommendations")
def get_recommendations(limit: int = 10, db: Session = Depends(get_db)):
    recs = list(
        db.execute(
            select(TopicRecommendation).order_by(TopicRecommendation.created_at.desc()).limit(limit)
        ).scalars().all()
    )
    
    return [
        {
            "id": r.id,
            "title": r.title,
            "rationale": r.rationale,
            "relevance": r.relevance,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in recs
    ]
