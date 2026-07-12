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

## Example usage
```bash
# Create a short link
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url": "https://www.google.com"}'

# -> {"short_code": "aZ3xQ1b", "short_url": "http://localhost:8000/aZ3xQ1b", ...}

# Visit it (redirects with 302)
curl -L http://localhost:8000/aZ3xQ1b

# Check stats
curl http://localhost:8000/stats/aZ3xQ1b
```

