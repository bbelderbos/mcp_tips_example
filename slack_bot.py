from decouple import config
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from server import load_notes

app = App(token=config("SLACK_BOT_TOKEN"))


def search(query: str, limit: int = 3) -> list[dict]:
    q = query.lower()
    return [
        n
        for n in load_notes()
        if q in n["title"].lower()
        or q in n["body"].lower()
        or any(q in t for t in n["tags"])
    ][:limit]


@app.command("/tip")
def handle_tip(ack, command, say):
    ack()
    query = command["text"].strip()
    if not query:
        say("Usage: `/tip <keyword>`  e.g. `/tip generators`")
        return

    results = search(query)
    if not results:
        say(f"No tips found for *{query}*")
        return

    blocks = []
    for tip in results:
        preview = tip["body"][:280].rstrip()
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{tip['title']}*\n{preview}"},
            }
        )
        blocks.append({"type": "divider"})

    say(blocks=blocks)


if __name__ == "__main__":
    SocketModeHandler(app, config("SLACK_APP_TOKEN")).start()
