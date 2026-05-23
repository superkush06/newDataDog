"""Pure LLMO scoring. No I/O."""
from typing import Iterable, Mapping

POSITION_WEIGHTS = {1: 1.0, 2: 0.7, 3: 0.4, 4: 0.2, 0: 0.0}


def citation_frequency(audits: Iterable[Mapping]) -> float:
    audits = list(audits)
    if not audits:
        return 0.0
    weights = [POSITION_WEIGHTS.get(a.get("position", 0), 0.0) for a in audits]
    return sum(weights) / len(audits) * 100.0


def share_of_voice(audits: Iterable[Mapping]) -> float:
    brand_mentions = 0
    competitor_mentions = 0
    for a in audits:
        if a.get("mentioned"):
            brand_mentions += 1
        competitor_mentions += len(a.get("competitors_mentioned") or [])
    total = brand_mentions + competitor_mentions
    if total == 0:
        return 0.0
    return brand_mentions / total * 100.0


def citation_accuracy(audits: Iterable[Mapping]) -> float:
    drifts = [a.get("drift_score", 0.0) for a in audits if a.get("mentioned")]
    if not drifts:
        return 0.0
    return sum(100.0 * (1.0 - d) for d in drifts) / len(drifts)


def sentiment_quality(audits: Iterable[Mapping]) -> float:
    sents = [a.get("sentiment", 0.0) for a in audits if a.get("mentioned")]
    if not sents:
        return 50.0
    avg = sum(sents) / len(sents)
    return (avg + 1.0) / 2.0 * 100.0


def compute_llmo_score(citation_freq: float, sov: float,
                       citation_acc: float, sentiment_qual: float) -> float:
    return round(
        0.30 * citation_freq
        + 0.25 * sov
        + 0.25 * citation_acc
        + 0.20 * sentiment_qual,
        2,
    )
