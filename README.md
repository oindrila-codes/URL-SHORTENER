# URL-SHORTENER
# URL Shortener (FastAPI + SQLite)

A backend service that shortens URLs, redirects visitors, tracks click
counts, and supports optional link expiry — built to demonstrate backend
system-design fundamentals, not just CRUD.

## Features
- `POST /shorten` — create a short link, optionally with an expiry time
- `GET /{short_code}` — redirects to the original URL (increments click count)
- `GET /stats/{short_code}` — view metadata + click count
- **Rate limiting** — token bucket algorithm, per-client-IP, in-memory
- **Caching** — cache-aside pattern for the hot redirect path (in-memory,
  structured so it's a drop-in swap for Redis later)
- **Expiry** — links can optionally expire after N minutes

## Setup
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Server runs at `http://localhost:8000`. Interactive API docs (Swagger UI)
at `http://localhost:8000/docs`.

## Run tests
```bash
pytest -v
```

 click timestamps (not just a counter)
- Background job to purge expired links from the DB instead of checking
  expiry on every read
