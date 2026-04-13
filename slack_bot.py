import asyncio
import json
import threading
from pathlib import Path

from anthropic import AsyncAnthropic
from decouple import config
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

SERVER_PATH = Path(__file__).parent / "server.py"

anthropic = AsyncAnthropic(api_key=config("ANTHROPIC_API_KEY"))
app = App(token=config("SLACK_BOT_TOKEN"))

SYSTEM_PROMPT = (
    "Format all responses for Slack mrkdwn: "
    "use *bold* not **bold**, _italic_ (underscores) for italics, "
    "`code` for inline code, no ## headers, no markdown tables, "
    "use bullet points instead."
)


class MCPClient:
    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.session: ClientSession | None = None
        self.tools: list[dict] = []
        self._ready = threading.Event()
        threading.Thread(target=lambda: self.loop.run_until_complete(self._start()), daemon=True).start()
        self._ready.wait()

    async def _start(self) -> None:
        server_params = StdioServerParameters(
            command="uv",
            args=["--project", str(SERVER_PATH.parent), "run", "python", str(SERVER_PATH)],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                self.tools = [
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.inputSchema,
                    }
                    for t in tools_result.tools
                ]
                self.session = session
                self._ready.set()
                await asyncio.Event().wait()  # keep server alive for the bot's lifetime

    async def ask(self, query: str) -> str:
        messages: list[dict] = [{"role": "user", "content": query}]

        for _ in range(10):
            response = await anthropic.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                tools=self.tools,
                messages=messages,
                system=SYSTEM_PROMPT,
            )

            if response.stop_reason == "end_turn":
                return next(
                    (block.text for block in response.content if hasattr(block, "text")),
                    "No response.",
                )

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await self.session.call_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps([c.text for c in result.content]),
                    })

            if not tool_results:
                break

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        return "No response after maximum tool-use iterations."


mcp = MCPClient()


@app.command("/tip")
def handle_tip(ack, command, respond):
    ack()
    query = command["text"].strip()
    if not query:
        respond("Usage: `/tip <question>`  e.g. `/tip how do generators work?`")
        return

    respond(f"> `/tip {query}`\n\n_Searching bobcodesit tips..._")

    def process():
        try:
            future = asyncio.run_coroutine_threadsafe(mcp.ask(query), mcp.loop)
            respond(future.result(timeout=60))
        except Exception as e:
            respond(f"Error: {e}")

    threading.Thread(target=process).start()


if __name__ == "__main__":
    SocketModeHandler(app, config("SLACK_APP_TOKEN")).start()
