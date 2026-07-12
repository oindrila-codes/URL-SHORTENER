from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


class ShortenRequest(BaseModel):
    long_url: HttpUrl
    # optional: caller can request the link expire after N minutes
    expires_in_minutes: Optional[int] = Field(default=None, ge=1)


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    expires_at: Optional[datetime] = None


class StatsResponse(BaseModel):
    short_code: str
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    click_count: int
