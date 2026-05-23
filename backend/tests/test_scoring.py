from app.pipeline.score_formula import compute_score, severity_label


def test_score_critical_when_high_engagement_and_velocity():
    s = compute_score(
        post_count=11, likes=300, shares=80, comments=20,
        max_followers=200_000, neg_count=9, recent_2h=6,
    )
    assert s["severity_score"] > 700
    assert s["influence_multiplier"] == 1.5


def test_score_zero_when_no_posts():
    s = compute_score(0, 0, 0, 0, 0, 0, 0)
    assert s["severity_score"] == 0


def test_severity_labels():
    t = {"critical": 700, "high": 400, "medium": 200}
    assert severity_label(701, t) == "critical"
    assert severity_label(500, t) == "high"
    assert severity_label(300, t) == "medium"
    assert severity_label(50, t) == "low"
