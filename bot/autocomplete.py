import difflib
import contextlib

import hikari
import miru
import lightbulb

from internal.config import MODELS, IMAGE_MODELS, PROMPT_PRESETS

loader = lightbulb.Loader()


class AIView(miru.View):
    def __init__(
        self, entries: list[str], interaction: hikari.CommandInteraction
    ) -> None:
        super().__init__(timeout=60)
        self.entries = entries
        self._interaction = interaction
        self.index = 0

        self.previous_page.disabled = True
        self.next_page.disabled = len(entries) <= 1

    @miru.button(
        emoji="<:left:1368155093337243748>", style=hikari.ButtonStyle.SECONDARY
    )
    async def previous_page(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.index -= 1
        self._update_buttons()
        await ctx.edit_response(self.entries[self.index], components=self.build())

    @miru.button(
        emoji="<:right:1368155064925163550>", style=hikari.ButtonStyle.SECONDARY
    )
    async def next_page(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.index += 1
        self._update_buttons()
        await ctx.edit_response(self.entries[self.index], components=self.build())

    def _update_buttons(self) -> None:
        """Helper method to update button states."""
        self.previous_page.disabled = self.index == 0
        self.next_page.disabled = self.index == len(self.entries) - 1

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        """Check if the user interacting is the one who invoked the command."""
        return ctx.user.id == ctx.author.id

    async def on_timeout(self) -> None:
        """Disable all buttons when the view times out."""
        for child in self.children:
            child.disabled = True

        with contextlib.suppress(hikari.ForbiddenError):
            await self._interaction.edit_initial_response(components=self.build())


async def model_autocomplete(ctx: lightbulb.AutocompleteContext) -> None:
    """Provide model autocomplete suggestions"""
    current_value: str = ctx.focused.value or ""

    all_models = [model for category in MODELS.values() for model in category]

    prefix_matches = [
        m for m in all_models if m.lower().startswith(current_value.lower())
    ]
    if prefix_matches:
        return await ctx.respond(prefix_matches[: len(all_models)])

    fuzzy_matches = difflib.get_close_matches(
        current_value, all_models, n=10, cutoff=0.3
    )
    if fuzzy_matches:
        return await ctx.respond(fuzzy_matches)

    suggestions = []
    for category, models in MODELS.items():
        suggestions.extend(models[:3])

    return await ctx.respond(suggestions[: len(all_models)])


async def image_model_autocomplete(ctx: lightbulb.AutocompleteContext) -> None:
    """Provide image model autocomplete suggestions"""
    current_value: str = ctx.focused.value or ""

    all_models = [model for model in IMAGE_MODELS.keys()]

    prefix_matches = [
        m for m in all_models if m.lower().startswith(current_value.lower())
    ]

    if prefix_matches:
        return await ctx.respond(prefix_matches[: len(all_models)])

    fuzzy_matches = difflib.get_close_matches(
        current_value, all_models, n=10, cutoff=0.3
    )

    if fuzzy_matches:
        return await ctx.respond(fuzzy_matches)

    suggestions = []
    for model in all_models:
        suggestions.append(model)

    return await ctx.respond(suggestions[: len(all_models)])


async def prompt_preset_autocomplete(ctx: lightbulb.AutocompleteContext) -> None:
    """Provide prompt preset autocomplete suggestions"""
    current_value: str = ctx.focused.value or ""

    prefix_matches = [
        k for k in PROMPT_PRESETS if k.lower().startswith(current_value.lower())
    ]
    if prefix_matches:
        return await ctx.respond(prefix_matches)

    fuzzy_matches = difflib.get_close_matches(
        current_value, PROMPT_PRESETS.keys(), n=5, cutoff=0.3
    )
    if fuzzy_matches:
        return await ctx.respond(fuzzy_matches)

    return await ctx.respond(list(PROMPT_PRESETS.keys()))
