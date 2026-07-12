"""
Table design:

URL
- id            : internal primary key (auto increment) - never exposed
- short_code     : the public-facing code, e.g. 'aZ3xQ1' (indexed, unique)
- long_url      : the original URL
- created_at     : for analytics / expiry logic
- expires_at     : nullable -> link never expires if NULL
- click_count    : denormalized counter, incremented on every redirect

Why a separate internal `id` from the public `short_code`:
Never expose auto-increment DB ids in a public API - it lets people guess
how many rows/users you have, and lets them enumerate other people's links
by just incrementing a number in the URL.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from database import Base


def utcnow():
    # Stored naive (tzinfo stripped) - SQLite has no native timezone-aware
    # datetime type, so we keep everything naive-but-UTC throughout the
    # app rather than mixing aware/naive values, which is a classic
    # source of "can't compare offset-naive and offset-aware" bugs.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    long_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    expires_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)
