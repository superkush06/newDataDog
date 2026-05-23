"""Pure scoring functions. No I/O. Easy to test."""

WEIGHTS = {"volume": 10, "like": 2, "share": 5, "comment": 3, "sentiment": 3.5}


def compute_score(
    post_count: int, likes: int, shares: int, comments: int,
    max_followers: int, neg_count: int, recent_2h: int,
) -> dict:
    n = post_count or 0
    volume = n * WEIGHTS["volume"]
    engagement = likes * WEIGHTS["like"] + shares * WEIGHTS["share"] + comments * WEIGHTS["comment"]
    pct_neg = (neg_count / n) if n else 0
    sentiment = pct_neg * 100 * WEIGHTS["sentiment"]
    velocity = (recent_2h / n * 100) if n else 0
    influence = 1.5 if max_followers > 50_000 else 1.0
    score = (volume + engagement + sentiment + velocity) * influence
    return {
        "volume": volume, "engagement": engagement, "sentiment": sentiment,
        "velocity": velocity, "influence_multiplier": influence,
        "severity_score": score,
    }


def severity_label(score: float, thresholds: dict) -> str:
    if score >= thresholds["critical"]:
        return "critical"
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["medium"]:
        return "medium"
    return "low"
