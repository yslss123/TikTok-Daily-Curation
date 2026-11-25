import math
from datetime import datetime, timezone

ALLOWED = {"funny", "beauty", "creative", "curiosity"}


def score(candidate, now: datetime | None = None) -> float:
    """Rank by reach, engagement, recency and classifier confidence."""
    views = max(candidate.views, 1)
    engagement = (
        candidate.likes + 2 * candidate.comments + 3 * candidate.shares
    ) / views
    reach_score = math.log10(views + 1)
    engagement_score = min(engagement, 1.0) * 10
    freshness_score = 0.0
    if candidate.create_time:
        current = now or datetime.now(timezone.utc)
        age_days = max(0.0, (current.timestamp() - candidate.create_time) / 86400)
        freshness_score = max(0.0, 1.0 - age_days / 30.0) * 2
    confidence_score = max(0.0, min(1.0, candidate.classification_confidence))
    return round(reach_score + engagement_score + freshness_score + confidence_score, 4)


def rank_candidates(candidates, max_items=20, now=None):
    """Rank discoverable metadata; local files and reuse permissions are not required."""
    seen = set()
    eligible = []
    for candidate in candidates:
        if not candidate.id or candidate.id in seen or candidate.category not in ALLOWED:
            continue
        if not candidate.source_url:
            continue
        seen.add(candidate.id)
        candidate.score = score(candidate, now=now)
        eligible.append(candidate)
    return sorted(eligible, key=lambda item: (item.score, item.views), reverse=True)[:max_items]


def select_editable(candidates, max_items=20, now=None):
    """Return only files with a local copy and explicit reuse authorization."""
    authorized = [
        item for item in candidates
        if item.authorized
        and bool(item.license.strip())
        and bool(item.authorization_reference.strip())
        and item.local_path.is_file()
    ]
    return rank_candidates(authorized, max_items=max_items, now=now)


# Backwards-compatible alias for the original editor pipeline.
def select(candidates, max_items=20):
    return select_editable(candidates, max_items=max_items)
