import math
ALLOWED = {"funny", "beauty", "creative", "curiosity"}

def score(c):
    engagement = (c.likes + 2*c.comments + 3*c.shares) / max(c.views, 1)
    return round(math.log10(c.views + 1) + min(engagement, 1.0)*10, 4)

def select(candidates, max_items=20):
    seen, eligible = set(), []
    for c in candidates:
        if c.id in seen or c.category not in ALLOWED: continue
        seen.add(c.id)
        if not c.authorized or not c.license or not c.authorization_reference: continue
        if not c.source_url or not c.local_path.is_file(): continue
        c.score = score(c); eligible.append(c)
    return sorted(eligible, key=lambda x:(x.score,x.views), reverse=True)[:max_items]
