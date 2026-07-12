# Learning Path: URL Shortener Project

A step-by-step guide to actually understand every concept in this project
— not just read the code, but be able to explain and defend it in an
interview. Go in order; each phase builds on the last.

Estimated total time: **2-3 weeks** at a steady pace (1-2 hours/day).
Don't rush — depth here is the entire point of doing this project.

---

## Phase 1: Foundations (before touching the code)

**Goal:** understand the pieces this project is made of, in isolation.

1. **HTTP basics**
   - What a request/response cycle actually is (method, headers, body, status code)
   - Status codes: 2xx (success), 3xx (redirect), 4xx (client error) — focus especially on 301 vs 302, 404, 410, 429
   - Resource: MDN's "HTTP overview" article; freeCodeCamp's HTTP crash course video

2. **REST API design basics**
   - What makes an API "RESTful" (resources, not actions, in the URL)
   - GET vs POST semantics (idempotent vs not)
   - Resource: "REST API Tutorial" (restfulapi.net)

3. **What an ORM is, and why**
   - Writing raw SQL vs using an ORM like SQLAlchemy — trade-offs
   - Resource: SQLAlchemy's official "ORM Quickstart" (skim it, don't memorize)

**Checkpoint:** Can you explain, in one sentence each, what GET/POST are for,
what a 302 redirect does, and what an ORM saves you from writing by hand?

---

## Phase 2: Read the code top-down, file by file

**Goal:** understand what each file does and why it's separated this way.

Read in this order (matches how a request actually flows):

1. `database.py` — how the DB connection is set up, what `get_db()` does
2. `models.py` — the table schema, and *why* `id` and `short_code` are separate
3. `schemas.py` — Pydantic validation, why input/output shapes are defined explicitly
4. `utils.py` — short code generation, why random over ID-encoding
5. `cache.py` — the cache-aside pattern
6. `rate_limiter.py` — token bucket algorithm
7. `main.py` — how everything gets wired together per endpoint

**How to actually study each file (don't just read — do this):**
- Read the docstring at the top of the file first — it explains the *why*, not just the *what*
- For each function, cover the code and try to guess what it does from the name alone, then check
- Rewrite one function from scratch in a blank file, without looking, then compare to the original

**Checkpoint:** Without looking at the code, describe out loud what happens,
file by file, when someone calls `POST /shorten`.

---

## Phase 3: Deep-dive each system-design concept

This is the part that actually differentiates this project. Spend real
time here — this is what interviewers probe.

### 3a. Caching (cache-aside pattern)
- What "cache-aside" means vs other caching strategies (write-through, write-back) — you don't need to implement the others, just know they exist and how cache-aside differs
- Why reads get cached but writes don't in this project
- What a **cache invalidation** problem is (when does cached data go stale, and how would you know) — this project doesn't handle invalidation; know that gap
- Resource: "Caching Strategies and How to Choose the Right One" (AWS blog, freely available) — read just the cache-aside section

### 3b. Rate limiting (token bucket)
- Trace through `rate_limiter.py` by hand: pick a `capacity` and `refill_rate`,
  simulate 15 requests arriving at different times, and calculate by hand
  whether each one is allowed
- Compare to a **fixed window counter** (look this up) — write down, in your
  own words, the burst problem at window boundaries that token bucket avoids
- Resource: "Rate Limiting Algorithms" articles (search this exact phrase) —
  read about at least token bucket, fixed window, and sliding window so you
  can compare all three if asked

### 3c. Database schema design
- Why `short_code` is indexed and unique
- What an index actually does under the hood (conceptually — a lookup
  structure, not a full table scan) — you don't need internals, just the idea
- Why internal auto-increment IDs shouldn't be exposed publicly (enumeration attacks — look up what this term means)

### 3d. Concurrency / thread safety
- Why `cache.py` and `rate_limiter.py` use `threading.Lock()`
- What a **race condition** is — construct a concrete example: two requests
  incrementing `click_count` at the exact same time without a lock, and
  what could go wrong
- Resource: any short explainer on "race condition" with a simple counter example

**Checkpoint for this whole phase:** Explain each of the four concepts above
to a friend (or out loud to yourself) without any notes, in under 2 minutes each.

---

## Phase 4: Run it, break it, extend it

**Goal:** move from "I read this" to "I built and debugged this."

1. Run the server locally (`uvicorn main:app --reload`), hit every endpoint manually with `curl` or the `/docs` Swagger UI
2. Run the test suite (`pytest -v`), read every test and explain what failure mode each one guards against
3. **Deliberately break something and fix it:**
   - Comment out the `threading.Lock()` in `rate_limiter.py` — does anything visibly break? (Race conditions are often invisible until load increases — this is worth understanding, not just fixing)
   - Change the redirect from 302 to 301, reload, and see if you can reason about why click counts would stop updating (you may need to test in a real browser, since `curl` doesn't cache redirects the way browsers do)
4. **Extend it yourself** — pick ONE from the README's "possible extensions"
   list and actually build it:
   - Easiest: a background job that deletes expired links from the DB
   - Medium: custom/vanity short codes (user picks the code instead of random)
   - Harder: swap the in-memory cache for real Redis (`pip install redis`,
     run Redis locally via Docker, change only `cache.py`)

**Checkpoint:** You've made at least one real change to the codebase, run
the tests again to confirm you didn't break anything, and can explain what
you changed and why.

---

## Phase 5: Interview-readiness drill

**Goal:** simulate the actual pressure of explaining this live.

Practice answering these out loud, timed to under 90 seconds each, with
no notes:

1. "Walk me through what happens when I call `POST /shorten`."
2. "Why 302 instead of 301 for the redirect?"
3. "Why don't you just base62-encode the auto-increment ID as the short code?"
4. "What's a cache-aside pattern, and why doesn't a write touch the cache here?"
5. "Explain token bucket rate limiting like I've never heard of it."
6. "This cache and rate limiter are in-memory — what breaks if you deploy
   this on 3 servers behind a load balancer? How would you fix it?"
7. "What would you add next if you had another week?"

If you stumble on any of these, that's your signal for what to re-study —
go back to the relevant part of Phase 3.

---

## Suggested pace

| Week | Focus |
|---|---|
| Week 1 | Phase 1 + Phase 2 (foundations + read the code) |
| Week 2 | Phase 3 (deep-dive each concept) + start Phase 4 |
| Week 3 | Finish Phase 4 (one real extension) + Phase 5 (interview drill) |

You can compress this if you already know some pieces (e.g., if you've
used SQLAlchemy before, skip ahead) — but don't skip Phase 5. That's the
step that actually converts "I understand this" into "I can defend this
under interview pressure," which is the whole point of doing this project.
