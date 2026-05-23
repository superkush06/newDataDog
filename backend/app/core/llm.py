"""Google DeepMind / Gemini wrappers — embed, classify, summarize, draft."""
import json
from google import genai
from google.genai import types
from app.config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


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


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """text-embedding-004 → 768-dim vectors, batched."""
    client = _get_client()
    resp = await client.aio.models.embed_content(
        model="text-embedding-004", contents=texts,
    )
    return [e.values for e in resp.embeddings]


async def classify_sentiment(text: str) -> str:
    client = _get_client()
    resp = await client.aio.models.generate_content(
        model="gemini-1.5-flash",
        contents=(
            "Classify this customer post as positive, negative, neutral, "
            "or question. Return only the label.\n\n" + text
        ),
        config=types.GenerateContentConfig(max_output_tokens=4, temperature=0),
    )
    label = (resp.text or "").strip().lower()
    return label if label in {"positive", "negative", "neutral", "question"} else "neutral"


async def summarize_cluster(texts: list[str]) -> tuple[str, str, list[str]]:
    client = _get_client()
    resp = await client.aio.models.generate_content(
        model="gemini-1.5-pro",
        contents=build_summary_prompt(texts),
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    try:
        d = json.loads(resp.text)
        return d.get("name", "Untitled"), d.get("summary", ""), d.get("tags", [])
    except Exception:
        return "Untitled", "", []


async def draft_response(brand: dict, cluster: dict, post_text: str, char_limit: int) -> str:
    client = _get_client()
    resp = await client.aio.models.generate_content(
        model="gemini-1.5-pro",
        contents=build_draft_prompt(brand, cluster, post_text, char_limit),
    )
    return (resp.text or "").strip()


async def classify_action_type(cluster: dict, top_posts: list) -> str:
    """Cheap rule first; LLM only if ambiguous."""
    neg = sum(1 for p in top_posts if len(p) > 7 and "negative" in (p[7] or ""))
    thresholds = cluster.get("thresholds") or {"critical": 700}
    if (cluster.get("severity_score") or 0) >= thresholds.get("critical", 700):
        return "escalation"
    if neg >= 5:
        return "response"
    return "insight"
