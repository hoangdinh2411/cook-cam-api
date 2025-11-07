

from typing import Optional
import redis.asyncio as redis

from utils.config import REDIS_URL

rds: Optional[redis.Redis] = None
async def get_redis() -> redis.Redis:
    global rds
    if rds is None:
        rds = redis.from_url(REDIS_URL, decode_responses=True)
    return rds




