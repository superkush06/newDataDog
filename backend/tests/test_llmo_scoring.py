import pytest

from app.pipeline.llmo_scoring import (
    compute_llmo_score, citation_frequency, share_of_voice,
    citation_accuracy, sentiment_quality,
)


def test_citation_frequency_position_weighted():
    audits = [
        {"position": 1, "mentioned": True},
        {"position": 3, "mentioned": True},
        {"position": 0, "mentioned": False},
    ]
    # (1.0 + 0.4 + 0) / 3 * 100 ≈ 46.7
    assert 46 < citation_frequency(audits) < 48


def test_share_of_voice_basic():
    audits = [
        {"mentioned": True, "competitors_mentioned": ["A", "B"]},
        {"mentioned": True, "competitors_mentioned": ["A"]},
    ]
    # 2 brand vs 3 competitor = 2/5 = 40
    assert share_of_voice(audits) == 40.0


def test_citation_accuracy_only_when_mentioned():
    audits = [
        {"mentioned": True, "drift_score": 0.1},
        {"mentioned": True, "drift_score": 0.5},
        {"mentioned": False, "drift_score": 0.0},
    ]
    # avg(90, 50) = 70
    assert citation_accuracy(audits) == 70.0


def test_sentiment_quality_rescaled():
    audits = [
        {"mentioned": True, "sentiment": 0.4},
        {"mentioned": True, "sentiment": -0.2},
    ]
    # avg sentiment = 0.1; rescaled (0.1+1)/2*100 = 55
    assert sentiment_quality(audits) == pytest.approx(55.0)


def test_compute_llmo_score_weights():
    s = compute_llmo_score(
        citation_freq=60, sov=40, citation_acc=70, sentiment_qual=55,
    )
    # 0.30*60 + 0.25*40 + 0.25*70 + 0.20*55 = 18+10+17.5+11 = 56.5
    assert s == 56.5
