"""
Basic test suite using FastAPI's TestClient (built on httpx).
Run with: pytest -v
"""

import os
import pytest
from fastapi.testclient import TestClient

# Use a separate test DB so we don't pollute shortener.db
os.environ.setdefault("TESTING", "1")

from main import app
from database import Base, engine
from cache import cache
from rate_limiter import rate_limiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """Clear cache, DB tables, and rate-limit buckets before every test
    so tests don't leak state into each other (the rate limiter is a
    module-level singleton, so without this reset, tokens consumed in
    one test would carry over and make later tests fail unpredictably)."""
    cache.clear()
    rate_limiter.buckets.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_shorten_and_redirect():
    resp = client.post("/shorten", json={"long_url": "https://www.example.com/page"})
    assert resp.status_code == 200
    data = resp.json()
    assert "short_code" in data
    assert len(data["short_code"]) == 7

    redirect = client.get(f"/{data['short_code']}", follow_redirects=False)
    assert redirect.status_code == 302
    assert redirect.headers["location"] == "https://www.example.com/page"


def test_unknown_code_returns_404():
    resp = client.get("/doesnotexist", follow_redirects=False)
    assert resp.status_code == 404


def test_stats_tracks_click_count():
    resp = client.post("/shorten", json={"long_url": "https://www.example.com/x"})
    code = resp.json()["short_code"]

    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)

    stats = client.get(f"/stats/{code}")
    assert stats.status_code == 200
    assert stats.json()["click_count"] == 2


def test_expired_link_returns_410():
    resp = client.post(
        "/shorten",
        json={"long_url": "https://www.example.com/soon-gone", "expires_in_minutes": 1},
    )
    code = resp.json()["short_code"]

    # Manually force expiry in the DB to avoid sleeping in tests.
    from database import SessionLocal
    import models
    from datetime import datetime, timedelta, timezone

    db = SessionLocal()
    entry = db.query(models.URL).filter(models.URL.short_code == code).first()
    entry.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        minutes=1
    )
    db.commit()
    db.close()

    redirect = client.get(f"/{code}", follow_redirects=False)
    assert redirect.status_code == 410


def test_rate_limit_blocks_after_burst():
    # capacity=10 tokens, so the 11th rapid request should be rejected.
    for _ in range(10):
        r = client.post("/shorten", json={"long_url": "https://www.example.com/a"})
        assert r.status_code == 200

    r = client.post("/shorten", json={"long_url": "https://www.example.com/a"})
    assert r.status_code == 429
