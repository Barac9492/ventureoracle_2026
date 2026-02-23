"""Prediction tracker — monitors and resolves predictions over time."""

from datetime import datetime, timezone

from sqlalchemy import select

from ventureoracle.db.database import get_session
from ventureoracle.db.models import Prediction


def list_predictions(status: str | None = None) -> list[Prediction]:
    """List predictions, optionally filtered by status."""
    session = get_session()
    stmt = select(Prediction).order_by(Prediction.created_at.desc())
    if status:
        stmt = stmt.where(Prediction.status == status)
    return list(session.execute(stmt).scalars().all())


def resolve_prediction(prediction_id: str, outcome: str) -> Prediction | None:
    """Resolve a prediction as correct, incorrect, or partial."""
    if outcome not in ("correct", "incorrect", "partial", "expired"):
        raise ValueError(f"Invalid outcome: {outcome}. Use: correct, incorrect, partial, expired")

    session = get_session()
    prediction = session.get(Prediction, prediction_id)
    if not prediction:
        return None

    prediction.status = outcome
    prediction.resolved_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(prediction)
    return prediction


def get_calibration_stats() -> dict:
    """Calculate prediction accuracy statistics."""
    session = get_session()
    all_preds = list(session.execute(select(Prediction)).scalars().all())

    resolved = [p for p in all_preds if p.status in ("correct", "incorrect", "partial")]
    if not resolved:
        return {"total": len(all_preds), "resolved": 0, "accuracy": None, "by_domain": {}}

    correct = sum(1 for p in resolved if p.status == "correct")
    accuracy = correct / len(resolved) if resolved else 0

    # Break down by domain
    by_domain = {}
    for p in resolved:
        if p.domain not in by_domain:
            by_domain[p.domain] = {"total": 0, "correct": 0}
        by_domain[p.domain]["total"] += 1
        if p.status == "correct":
            by_domain[p.domain]["correct"] += 1

    for domain_stats in by_domain.values():
        domain_stats["accuracy"] = (
            domain_stats["correct"] / domain_stats["total"] if domain_stats["total"] else 0
        )

    return {
        "total": len(all_preds),
        "resolved": len(resolved),
        "correct": correct,
        "accuracy": accuracy,
        "by_domain": by_domain,
    }
