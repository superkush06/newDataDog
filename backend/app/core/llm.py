"""LLM + embedding wrappers.

Generation: Groq (free-tier-friendly, OpenAI-compatible API).
- llama-3.1-8b-instant: sentiment classification + LLMO judge pass (cheap, fast)
- llama-3.3-70b-versatile: cluster summary + brand-voice response drafting (quality)

Embeddings: local sentence-transformers (no API, no rate limits).
- all-MiniLM-L6-v2 (384-dim, ~80MB) — first call downloads the model.
"""
import json
from groq import AsyncGroq

from app.config import settings

_client = None
_embedder = None

# Models in one place so the swap is editable from here
SENTIMENT_MODEL = "llama-3.1-8b-instant"
JUDGE_MODEL = "llama-3.1-8b-instant"
SUMMARY_MODEL = "llama-3.3-70b-versatile"
DRAFT_MODEL = "llama-3.3-70b-versatile"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


def _get_embedder():
    """Lazy-load sentence-transformers (one-time HF download on first call)."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


# ---------- prompt builders (pure; covered by tests) -------------------------

def build_summary_prompt(texts: list[str]) -> str:
    head = (
        f"Below are {len(texts)} social posts grouped by similarity. "
        "Return JSON: {name: 3-5 word theme, summary: 2-3 sentences "
        "covering the core complaint/request/praise, who is affected and "
        "how widespread, tags: 3-5 topic tags}."
    )
    return head + "\n\n" + "\n".join(texts[:20])


def build_draft_prompt(brand: dict, cluster: dict, post_text: str, char_limit: int) -> str:
    return (
        f"You are drafting a social media response on behalf of {brand['name']}. "
        f"Voice: {brand.get('voice_guidelines', '')}. The customer said: \"{post_text}\". "
        f"Context: {cluster['summary']} ({cluster['post_count']} similar reports). "
        "Draft a response that (1) acknowledges the specific issue, (2) is "
        "empathetic without being formulaic, (3) offers a concrete next step, "
        f"(4) stays under {char_limit} characters. Do not make promises the brand "
        "has not authorized. If unsure, route to human."
    )


# ---------- Groq calls --------------------------------------------------------

async def embed_batch(texts: list[str]) -> list[list[float]]:
    """384-dim vectors via local sentence-transformers. Returns plain Python lists."""
    model = _get_embedder()
    arr = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return arr.tolist()


async def classify_sentiment(text: str) -> str:
    client = _get_client()
    resp = await client.chat.completions.create(
        model=SENTIMENT_MODEL,
        messages=[{
            "role": "user",
            "content": ("Classify this customer post as positive, negative, neutral, "
                        "or question. Return only the label.\n\n" + text),
        }],
        max_tokens=4,
        temperature=0,
    )
    label = (resp.choices[0].message.content or "").strip().lower().strip(".")
    return label if label in {"positive", "negative", "neutral", "question"} else "neutral"


async def summarize_cluster(texts: list[str]) -> tuple[str, str, list[str]]:
    client = _get_client()
    resp = await client.chat.completions.create(
        model=SUMMARY_MODEL,
        messages=[{"role": "user", "content": build_summary_prompt(texts)}],
        response_format={"type": "json_object"},
        max_tokens=500,
    )
    try:
        d = json.loads(resp.choices[0].message.content or "{}")
        return d.get("name", "Untitled"), d.get("summary", ""), d.get("tags", [])
    except Exception:
        return "Untitled", "", []


async def draft_response(brand: dict, cluster: dict, post_text: str, char_limit: int) -> str:
    client = _get_client()
    resp = await client.chat.completions.create(
        model=DRAFT_MODEL,
        messages=[{"role": "user", "content": build_draft_prompt(brand, cluster, post_text, char_limit)}],
        max_tokens=400,
    )
    return (resp.choices[0].message.content or "").strip()


async def classify_action_type(cluster: dict, top_posts: list) -> str:
    """Cheap rule first; reserve LLM calls for higher-stakes ambiguity later."""
    neg = sum(1 for p in top_posts if len(p) > 7 and "negative" in (p[7] or ""))
    thresholds = cluster.get("thresholds") or {"critical": 700}
    if (cluster.get("severity_score") or 0) >= thresholds.get("critical", 700):
        return "escalation"
    if neg >= 5:
        return "response"
    return "insight"
