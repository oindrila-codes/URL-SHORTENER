"""
URL Shortener - main application.

Endpoints:
  POST /shorten             -> create a short link
  GET  /{short_code}        -> redirect to the original URL (302)
  GET  /stats/{short_code}  -> view click count / metadata (no redirect)


from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db
from utils import generate_short_code
from rate_limiter import enforce_rate_limit
from cache import cache

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener")

BASE_HOST = "http://localhost:8000"
MAX_GENERATION_RETRIES = 5


@app.post("/shorten", response_model=schemas.ShortenResponse)
def shorten_url(
    payload: schemas.ShortenRequest,
    db: Session = Depends(get_db),
    _rate_limit=Depends(enforce_rate_limit),
):
    expires_at = None
    if payload.expires_in_minutes:
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            minutes=payload.expires_in_minutes
        )

    # Retry on the rare random-code collision (see utils.py docstring).
    for _ in range(MAX_GENERATION_RETRIES):
        code = generate_short_code()
        if not db.query(models.URL).filter(models.URL.short_code == code).first():
            break
    else:
        raise HTTPException(500, "Could not generate a unique code, try again.")

    url_entry = models.URL(
        short_code=code,
        long_url=str(payload.long_url),
        expires_at=expires_at,
    )
    db.add(url_entry)
    db.commit()
    db.refresh(url_entry)

    return schemas.ShortenResponse(
        short_code=code,
        short_url=f"{BASE_HOST}/{code}",
        long_url=url_entry.long_url,
        expires_at=expires_at,
    )


@app.get("/{short_code}")
def redirect_to_long_url(short_code: str, db: Session = Depends(get_db)):
    cached_url = cache.get(short_code)

    if cached_url is None:
        entry = (
            db.query(models.URL).filter(models.URL.short_code == short_code).first()
        )
        if not entry:
            raise HTTPException(404, "Short link not found.")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if entry.expires_at and entry.expires_at < now:
            raise HTTPException(410, "This link has expired.")

        cache.set(short_code, entry.long_url)
        long_url = entry.long_url
    else:
        long_url = cached_url
        entry = (
            db.query(models.URL).filter(models.URL.short_code == short_code).first()
        )

    # Click count always updates the DB directly (writes bypass the cache -
    # a cache-aside pattern only accelerates reads, not writes).
    if entry:
        entry.click_count += 1
        db.commit()

    return RedirectResponse(url=long_url, status_code=302)


@app.get("/stats/{short_code}", response_model=schemas.StatsResponse)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    entry = db.query(models.URL).filter(models.URL.short_code == short_code).first()
    if not entry:
        raise HTTPException(404, "Short link not found.")

    return schemas.StatsResponse(
        short_code=entry.short_code,
        long_url=entry.long_url,
        created_at=entry.created_at,
        expires_at=entry.expires_at,
        click_count=entry.click_count,
    )
