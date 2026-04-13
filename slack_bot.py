import asyncio
import json
import threading
from pathlib import Path

from anthropic import Anthropic
from decouple import config
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

SERVER_PATH = Path(__file__).parent / "server.py"

anthropic = Anthropic(api_key=config("ANTHROPIC_API_KEY"))
app = App(token=config("SLACK_BOT_TOKEN"))


async def ask_claude(query: str) -> str:
    server_params = StdioServerParameters(
        command="uv",
        args=["--project", str(SERVER_PATH.parent), "run", "python", str(SERVER_PATH)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in tools_result.tools
            ]

            messages = [{"role": "user", "content": query}]

            while True:
                response = anthropic.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    tools=tools,
                    messages=messages,
                    system=(
                        "Format all responses for Slack mrkdwn: "
                        "use *bold* not **bold**, _italic_ not _italic_ with underscores, "
                        "`code` for inline code, no ## headers, no markdown tables, "
                        "use bullet points instead."
                    ),
                )

                if response.stop_reason == "end_turn":
                    return next(
                        (
                            block.text
                            for block in response.content
                            if hasattr(block, "text")
                        ),
                        "No response.",
                    )

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await session.call_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps([c.text for c in result.content]),
                            }
                        )

                if not tool_results:
                    break

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})


@app.command("/tip")
def handle_tip(ack, command, respond):
    ack()
    query = command["text"].strip()
    if not query:
        respond("Usage: `/tip <question>`  e.g. `/tip how do generators work?`")
        return

    respond(f"> `/tip {query}`\n\n_Searching bobcodesit tips..._")

    def process():
        respond(asyncio.run(ask_claude(query)))

    threading.Thread(target=process).start()


if __name__ == "__main__":
    SocketModeHandler(app, config("SLACK_APP_TOKEN")).start()
