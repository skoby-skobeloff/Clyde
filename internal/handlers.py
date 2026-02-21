import asyncio
import time
import os
import aiosqlite
from functools import wraps
from typing import Optional

from .config import stats_db_file, logs_db_file, data_logger


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


async def init_logs_db():
    if not os.path.exists(logs_db_file):
        async with aiosqlite.connect(logs_db_file) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                day_date TEXT NOT NULL,
                uid TEXT NOT NULL,
                feature TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (day_date, uid, feature)
            );
            """)

            await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_usage_uid_day
            ON daily_usage (uid, day_date);
            """)

            await db.commit()
        data_logger.info("[STATS] log DB created")


async def init_stats_db():
    if not os.path.exists(stats_db_file):
        async with aiosqlite.connect(stats_db_file) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                date TEXT PRIMARY KEY,
                guild_count INTEGER,
                member_count INTEGER
            )
            """)

            await db.commit()
        data_logger.info("[STATS] data DB created")
