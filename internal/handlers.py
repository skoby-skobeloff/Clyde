import asyncio
import time
import os
import aiosqlite
from functools import wraps

from .config import db_file, data_logger

def exponential(retry_cnt: int, retry_min: int, retry_max: int):
    """Exponentially back off on failure."""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                got_exc = None
                for attempt in range(retry_cnt):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        got_exc = exc
                        await asyncio.sleep(min(retry_min * (2**attempt), retry_max))
                raise got_exc

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            got_exc = None
            for attempt in range(retry_cnt):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    got_exc = exc
                    time.sleep(min(retry_min * (2**attempt), retry_max))
            raise got_exc

        return sync_wrapper

    return decorator

async def init_db():
    if not os.path.exists(db_file):
        async with aiosqlite.connect(db_file) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                date TEXT PRIMARY KEY,
                guild_count INTEGER,
                member_count INTEGER
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS model_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                model TEXT,
                guild_id INTEGER,
                tps REAL,
                ttft REAL,
                status TEXT,
                error_type TEXT,
                tokens INTEGER
            )
            """)

            await db.commit()
        data_logger.info("[STATS] data DB created")

