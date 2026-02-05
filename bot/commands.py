import datetime
import io
import platform
from typing import Optional

import hikari
import lightbulb
import miru

from PIL import Image, UnidentifiedImageError

from .autocomplete import (
    model_autocomplete,
    prompt_preset_autocomplete,
    image_model_autocomplete,
    AIView,
)
from internal.config import (
    DEFAULT_MODEL,
    MAX_DISCORD_MESSAGE_LENGTH,
    PROMPT_PRESETS,
    DEFAULT_IMAGE_MODEL,
    MODELS,
    IMAGE_MODELS,
    chat_histories,
)
from internal.service import AIService, generate_text

loader = lightbulb.Loader()

ai_group = lightbulb.Group("ai", "AI command group")


@ai_group.register()
class AIText(lightbulb.SlashCommand, name="text", description="Generate text with AI"):
    request: str = lightbulb.string("request", "The request to send to the AI.")
    model: Optional[str] = lightbulb.string(
        "model",
        "The model to use.",
        default=DEFAULT_MODEL,
        autocomplete=model_autocomplete,
    )
    prompt: Optional[str] = lightbulb.string(
        "prompt",
        "The prompt or preset to use.",
        default="default",
        autocomplete=prompt_preset_autocomplete,
    )

    @lightbulb.invoke
    async def callback(self, ctx: lightbulb.Context, inter_client: miru.Client) -> None:
        await ctx.defer(ephemeral=False)

        resolved_prompt = PROMPT_PRESETS.get(self.prompt, self.prompt).format(
            "Lunal", "", "", datetime.datetime.now()
        )

        response = await generate_text(
            self.request, self.model, resolved_prompt, ctx.interaction.user.id
        )

        if len(response) > MAX_DISCORD_MESSAGE_LENGTH:
            chunks = []
            while response:
                split_idx = response.rfind("\n\n", 0, MAX_DISCORD_MESSAGE_LENGTH)

                if split_idx in [-1, 0]:
                    split_idx = MAX_DISCORD_MESSAGE_LENGTH

                chunk = response[:split_idx].rstrip()
                response = response[split_idx:].lstrip()
                chunks.append(chunk)
            view = AIView(chunks, ctx.interaction)
            await ctx.respond(chunks[0], components=view)
            inter_client.start_view(view)
        else:
            await ctx.respond(response)


@ai_group.register()
class AITextWithImage(
    lightbulb.SlashCommand, name="with_image", description="Generate text with an image"
):
    request: str = lightbulb.string("request", "The request to send to the AI.")
    image: hikari.Attachment = lightbulb.attachment(
        "image", "The image to send to the AI."
    )
    model: Optional[str] = lightbulb.string(
        "model",
        "The model to use.",
        default=DEFAULT_MODEL,
        autocomplete=model_autocomplete,
    )
    prompt: Optional[str] = lightbulb.string(
        "prompt",
        "The prompt or preset to use.",
        default="default",
        autocomplete=prompt_preset_autocomplete,
    )

    @lightbulb.invoke
    async def callback(
        self, ctx: lightbulb.Context, inter_client: miru.Client
    ) -> Optional[hikari.Message | hikari.Snowflake]:
        await ctx.defer(ephemeral=False)

        try:
            Image.open(io.BytesIO(await self.image.read()))
        except (UnidentifiedImageError, IOError):
            embed = hikari.Embed(
                title="<:error:1368156499167150171> Error",
                description="Please upload a valid image file.",
                color=hikari.Color.from_hex_code("#ed4245"),
            )
            return await ctx.respond(
                embed=embed,
                flags=hikari.MessageFlag.EPHEMERAL,
            )

        resolved_prompt = PROMPT_PRESETS.get(self.prompt, self.prompt).format(
            "Lunal", "", "", datetime.datetime.now()
        )

        image_data = io.BytesIO(await self.image.read())

        response = await generate_text(
            self.request,
            self.model,
            resolved_prompt,
            ctx.interaction.user.id,
            image_data,
        )

        if len(response) > MAX_DISCORD_MESSAGE_LENGTH:
            chunks = []
            while response:
                split_idx = response.rfind("\n\n", 0, MAX_DISCORD_MESSAGE_LENGTH)

                if split_idx in [-1, 0]:
                    split_idx = MAX_DISCORD_MESSAGE_LENGTH

                chunk = response[:split_idx].rstrip()
                response = response[split_idx:].lstrip()
                chunks.append(chunk)
            view = AIView(chunks, interaction=ctx.interaction)
            await ctx.respond(chunks[0], components=view)
            return inter_client.start_view(view)
        else:
            return await ctx.respond(response)


@ai_group.register()
class AIImage(
    lightbulb.SlashCommand,
    name="image",
    description="Generate image from prompt",
    hooks=[lightbulb.prefab.cooldowns.fixed_window(60, 1, "user")],
):
    prompt: str = lightbulb.string("prompt", "The image to generate.")
    model: Optional[str] = lightbulb.string(
        "model",
        "The model to use.",
        default=DEFAULT_IMAGE_MODEL,
        autocomplete=image_model_autocomplete,
    )

    @lightbulb.invoke
    async def callback(self, ctx: lightbulb.Context) -> None:
        await ctx.defer(ephemeral=False)

        image = await AIService.generate_image(
            self.model, self.prompt, str(ctx.user.id)
        )

        if isinstance(image, io.BytesIO):  # image generated
            await ctx.respond(attachments=[hikari.Bytes(image, "image.webp")])
        else:  # blocked by security
            await ctx.respond(image)


@ai_group.register()
class AIClear(
    lightbulb.SlashCommand,
    name="clear",
    description="Clear your chat history with the bot",
):
    @lightbulb.invoke
    async def callback(self, ctx: lightbulb.Context) -> None:
        user_id = ctx.interaction.user.id
        if user_id in chat_histories:
            del chat_histories[user_id]
            await ctx.respond(
                "Your chat history has been cleared.",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
        else:
            await ctx.respond(
                "You don't have any chat history to clear.",
                flags=hikari.MessageFlag.EPHEMERAL,
            )


@loader.command
class Info(
    lightbulb.SlashCommand, name="info", description="Display information about the bot"
):
    @lightbulb.invoke
    async def callback(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        models_length = sum(len(models) for models in MODELS.values()) + len(
            IMAGE_MODELS.keys()
        )
        application = await bot.rest.fetch_application()
        guild_count = application.approximate_guild_count
        user_count = application.approximate_user_install_count

        ie = hikari.Embed(
            title=f"About {bot.get_me().display_name}",
            description=f"Serving {guild_count} servers and"
            f" {user_count} users with AI for free",
            color=hikari.Color.from_hex_code("#5865F2"),
        )

        ie.add_field(name="Python Version", value=platform.python_version())
        ie.add_field(name="Hikari Version", value=hikari.__version__)
        ie.add_field(name="Models Available", value=str(models_length))

        await ctx.respond(embed=ie)


@loader.command
class Ping(
    lightbulb.SlashCommand,
    name="ping",
    description="Ping the bot",
):
    @lightbulb.invoke
    async def callback(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        latency = round(bot.heartbeat_latency * 1000)
        pe = hikari.Embed(
            description=f"**{latency}**ms", color=hikari.Color.from_hex_code("#5865F2")
        )
        await ctx.respond(embed=pe)


@loader.command
class Invite(
    lightbulb.SlashCommand,
    name="invite",
    description="Invite the bot to your server",
):
    @lightbulb.invoke
    async def callback(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        my_id = bot.cache.get_me().id
        button_view = miru.View()
        button_view.add_item(
            miru.LinkButton(
                label="Invite",
                url=f"https://discord.com/api/oauth2/authorize?client_id={my_id}&scope=bot+applications.commands",
            )
        )

        ie = hikari.Embed(
            description="Add me to your server by pressing the button below.",
            color=hikari.Color.from_hex_code("#5865f2"),
        )

        await ctx.respond(
            embed=ie,
            components=button_view.build(),
        )


loader.command(ai_group)
