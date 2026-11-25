import math
from .models import Candidate

ALLOWED = {"funny", "beauty", "creative", "curiosity"}

def score(c: Candidate) -> float:
    # Engagement ratios are smoothed to avoid rewarding tiny samples too heavily.
    views = max(c.views, 1)
    engagement = (c.likes + 2*c.comments + 3*c.shares) / views
    reach = math.log10(c.views + 1)
    return round(reach + min(engagement, 1.0) * 10, 4)

def select(candidates: list[Candidate], min_items: int = 10, max_items: int = 20) -> list[Candidate]:
    eligible = []
    seen = set()
    for c in candidates:
        if c.id in seen or c.category not in ALLOWED: continue
        seen.add(c.id)
        if not c.authorized or not c.license or not c.authorization_reference: continue
        if not c.local_path.is_file() or not c.source_url: continue
        c.score = score(c)
        eligible.append(c)
    eligible.sort(key=lambda x: (x.score, x.views), reverse=True)
    # Never fabricate entries to reach the target; report a shortfall in the run manifest.
    return eligible[:max_items]
