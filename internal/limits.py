import datetime
import aiosqlite

import hikari
import lightbulb

from .config import (
    TEXT_USAGE_LIMIT_PER_USER,
    IMAGE_USAGE_LIMIT_PER_USER,
    logs_db_file,
    logger,
)
from .service import get_owner_ids


class UsageLimitExceeded(Exception):
    pass


@lightbulb.hook(
    lightbulb.ExecutionSteps.CHECKS, skip_when_failed=True, name="usage_limit"
)
async def usage_limit(_: lightbulb.ExecutionPipeline, ctx: lightbulb.Context):
    uid = str(ctx.user.id)

    if int(uid) in await get_owner_ids():
        logger.info("Bot admin - ignoring usage limit")
        return

    used_images = await get_used_today(uid, "image")
    used_text = await get_used_today(uid, "text")

    logger.info(f"User {uid} - {used_images} images and {used_text} text responses")

    interaction = ctx.interaction
    subcommand: str | None = None

    if interaction.options:
        option = interaction.options[0]
        if option.type == hikari.OptionType.SUB_COMMAND:
            subcommand = option.name

    if IMAGE_USAGE_LIMIT_PER_USER is not None:
        if used_images >= IMAGE_USAGE_LIMIT_PER_USER and subcommand == "image":
            raise UsageLimitExceeded("usage limit exceeded")
    if TEXT_USAGE_LIMIT_PER_USER is not None:
        if used_text >= TEXT_USAGE_LIMIT_PER_USER and subcommand in [
            "text",
            "with_image",
        ]:
            raise UsageLimitExceeded("usage limit exceeded")

    return


async def increase_usage_limit(uid: int, feature: str):
    async with aiosqlite.connect(logs_db_file) as db:
        async with db.execute(
            """
            INSERT INTO daily_usage (day_date, uid, feature, used, updated_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(day_date, uid, feature)
            DO UPDATE SET used = used + 1, updated_at = CURRENT_TIMESTAMP
            RETURNING used
            """,
            (
                datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
                uid,
                feature,
            ),
        ) as cur:
            row = await cur.fetchone()
        await db.commit()
        return int(row[0])


async def get_used_today(uid: str, feature: str) -> int:
    async with aiosqlite.connect(logs_db_file) as db:
        async with db.execute(
            "SELECT used FROM daily_usage WHERE day_date = ? AND uid = ? AND feature = ?",
            (
                datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
                uid,
                feature,
            ),
        ) as cur:
            row = await cur.fetchone()
        return int(row[0]) if row else 0
