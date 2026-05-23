from app.core.llm import build_draft_prompt, build_summary_prompt


def test_draft_prompt_includes_brand_and_post():
    brand = {"name": "Acme", "voice_guidelines": "Warm, witty."}
    cluster = {"summary": "Checkout crash on iOS 18", "post_count": 11}
    p = build_draft_prompt(brand, cluster, "checkout broken", 280)
    assert "Acme" in p
    assert "Warm, witty" in p
    assert "checkout broken" in p
    assert "280" in p
    assert "11 similar" in p


def test_summary_prompt_lists_count():
    p = build_summary_prompt(["a", "b", "c"])
    assert "3 social" in p
