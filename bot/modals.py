import asyncio
import uuid

import hikari
import miru
import lightbulb

class InputModal(miru.Modal):
    def __init__(self, future: asyncio.Future[str]) -> None:
        super().__init__(title="AI Request", custom_id=f"ai-input-{uuid.uuid4()}")
        self.future = future

        self.request_input = miru.TextInput(
            label="Your request",
            style=hikari.TextInputStyle.PARAGRAPH,
            required=True,
            max_length=4000,
            placeholder="Write your request here...",
        )
        self.add_item(self.request_input)

    async def callback(self, ctx: miru.ModalContext) -> None:
        if not self.future.done():
            self.future.set_result(self.request_input.value)

        await ctx.defer()

    async def on_error(self, error: Exception, context: miru.ModalContext | None = None) -> None:
        if not self.future.done():
            self.future.set_exception(error)
        if context is not None:
            await context.respond("There was an internal error handling your request.", flags=64)

async def prompt_with_modal(ctx: lightbulb.Context, inter_client: miru.Client, timeout: float = 300.0) -> str | None:
    loop = asyncio.get_running_loop()
    future: asyncio.Future[str] = loop.create_future()

    modal = InputModal(future)
    await ctx.interaction.create_modal_response(modal)
    inter_client.start_modal(modal)

    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        return None
