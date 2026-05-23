from datetime import datetime

import pytest

from app.adapters import get_adapter, registered_platforms
from app.adapters.base import NormalizedPost
from app.adapters.meta import MetaAdapter
from app.adapters.nimble import NimbleAdapter
from app.adapters.x import XAdapter


def test_x_adapter_normalizes_single_tweet_payload():
    payload = {
        "data": {
            "id": "tw_123",
            "author_id": "u_1",
            "text": "Checkout is broken",
            "created_at": "2026-05-23T12:00:00Z",
        },
        "includes": {"users": [{"id": "u_1", "name": "Jane Doe", "username": "jane"}]},
    }

    posts = XAdapter().normalize(payload)

    assert len(posts) == 1
    assert posts[0] == NormalizedPost(
        platform="x",
        external_id="tw_123",
        text="Checkout is broken",
        author_name="Jane Doe",
        author_handle="jane",
        url="https://x.com/jane/status/tw_123",
        created_at=datetime.fromisoformat("2026-05-23T12:00:00+00:00"),
        raw=payload["data"],
    )


def test_meta_adapter_normalizes_instagram_data_payload():
    payload = {
        "object": "instagram",
        "data": {
            "id": "ig_42",
            "username": "coffee_fan",
            "caption": "App keeps crashing",
            "permalink": "https://instagram.com/p/abc",
            "timestamp": "2026-05-23T12:30:00Z",
        },
    }

    posts = MetaAdapter().normalize(payload)

    assert len(posts) == 1
    assert posts[0].platform == "instagram"
    assert posts[0].external_id == "ig_42"
    assert posts[0].author_handle == "coffee_fan"
    assert posts[0].text == "App keeps crashing"
    assert posts[0].url == "https://instagram.com/p/abc"


def test_meta_adapter_normalizes_facebook_webhook_entries():
    payload = {
        "object": "page",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "post_id": "fb_9",
                            "from": {"name": "Sam"},
                            "message": "Need help",
                            "created_time": "2026-05-23T13:00:00Z",
                        }
                    }
                ]
            }
        ],
    }

    posts = MetaAdapter().normalize(payload)

    assert len(posts) == 1
    assert posts[0].platform == "facebook"
    assert posts[0].external_id == "fb_9"
    assert posts[0].author_name == "Sam"
    assert posts[0].text == "Need help"


def test_nimble_adapter_normalizes_items():
    payload = {
        "brand_id": "brand_1",
        "items": [
            {
                "platform": "reddit",
                "id": "r_1",
                "author": "u/example",
                "text": "Acme checkout is down",
                "url": "https://reddit.com/r/example/comments/r_1",
                "posted_at": "2026-05-23T14:00:00Z",
            }
        ],
    }

    posts = NimbleAdapter().normalize(payload)

    assert len(posts) == 1
    assert posts[0].platform == "reddit"
    assert posts[0].external_id == "r_1"
    assert posts[0].brand_id == "brand_1"
    assert posts[0].author_name == "u/example"
    assert posts[0].text == "Acme checkout is down"


def test_registry_exposes_platform_aliases():
    assert get_adapter("x").platform == "x"
    assert get_adapter("twitter").platform == "x"
    assert get_adapter("instagram").platform == "meta"
    assert get_adapter("facebook").platform == "meta"
    assert "nimble" in registered_platforms()


def test_registry_rejects_unknown_platform():
    with pytest.raises(ValueError):
        get_adapter("unknown")
