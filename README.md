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

## Architecture decisions (what to talk about in interviews)

**Why 302, not 301, for redirects.** 301 is "permanent" and gets cached
by browsers — after the first visit, the browser skips your server
entirely on future clicks, so `click_count` would stop incrementing.
302 forces the browser back to your server every time.

**Why random short codes instead of base62-encoding an auto-increment ID.**
Encoding the ID is simpler (no collision handling) but leaks information:
`id=1042` tells anyone how many links exist, and codes become guessable/
enumerable (increment the code, see someone else's link). Random codes
avoid both problems at the cost of a rare collision check on insert.

**Why the internal DB `id` is never exposed in the API.** Same reasoning
as above, applied generally — auto-increment primary keys are an internal
implementation detail, not a public contract.

**Why cache-aside, and why it's a toy in-memory dict here.** Reads (the
redirect path) are far more frequent than writes (creating a link), so
caching the read path is the highest-leverage place to add a cache. It's
implemented as a bare dict here for a single-process demo; in production
behind multiple instances you'd move this to Redis so all instances share
state — `cache.py` is written so that's a one-file change, not a rewrite.

**Why token bucket over a fixed-window counter for rate limiting.** A
fixed window (e.g. "max 10 requests per minute, resetting on the minute")
lets a client send 10 requests at 0:59 and another 10 at 1:00 — 20
requests in 2 seconds. A token bucket refills continuously, so it allows
short bursts but enforces a true long-run average rate.

**Known limitation, worth naming yourself before an interviewer does:**
both the cache and the rate limiter are in-memory and per-process. Scale
this to multiple app instances behind a load balancer and each instance
would have its own view of rate limits and cache contents — the fix in
both cases is moving that state to Redis, which is why both modules are
deliberately isolated (`cache.py`, `rate_limiter.py`) rather than
inlined into `main.py`.

## Possible extensions (good "what would you add next" answers)
- Move cache + rate limiter state to real Redis
- Custom/vanity short codes (user-chosen instead of random)
- Auth so users can only see/manage their own links
- Analytics: referrer, geolocation, click timestamps (not just a counter)
- Background job to purge expired links from the DB instead of checking
  expiry on every read
