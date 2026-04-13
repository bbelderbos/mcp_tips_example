import json
import random
import re
from functools import cache
from pathlib import Path

from mcp.server.fastmcp import FastMCP

NOTES_DIR = Path.home() / "code/bobcodesit/notes"

mcp = FastMCP("code-tips")


@cache
def load_notes() -> list[dict]:
    notes = []
    for path in sorted(NOTES_DIR.glob("*.md")):
        lines = path.read_text().strip().splitlines()
        title = lines[0].lstrip("# ").strip()
        tag_line = lines[-1] if lines[-1].startswith("#") else ""
        tags = [t.lstrip("#") for t in tag_line.split() if t.startswith("#")]
        content_lines = lines[1:-1] if tag_line else lines[1:]
        body = "\n".join(content_lines).strip()
        notes.append({"id": path.stem, "title": title, "tags": tags, "body": body})
    return notes


@mcp.tool()
def search_tips(query: str, limit: int = 10) -> list[dict]:
    """Search code tips by keyword. Pass a single short keyword (e.g. 'generator', 'decorator', 'contextmanager'), not a full sentence. Returns up to `limit` matching tips with id, title, and tags. Use get_tip to fetch the full body of a specific tip."""
    pattern = re.compile(rf"\b{re.escape(query.lower())}\b")
    results = [
        {"id": n["id"], "title": n["title"], "tags": n["tags"]}
        for n in load_notes()
        if pattern.search(n["title"].lower())
        or pattern.search(n["body"].lower())
        or any(pattern.search(t) for t in n["tags"])
    ]
    return results[:limit]


@mcp.tool()
def random_tip(tag: str = "") -> dict:
    """Return a random tip, optionally filtered by tag (e.g. 'built-ins', 'generators', 'decorators')."""
    notes = load_notes()
    if tag:
        t = tag.lower().lstrip("#")
        notes = [n for n in notes if any(t in note_tag for note_tag in n["tags"])]
    if not notes:
        return {"error": f"No tips found for tag: {tag}"}
    return random.choice(notes)


@mcp.tool()
def get_tip(tip_id: str) -> dict:
    """Get the full content of a single tip by its filename (without .md)."""
    path = NOTES_DIR / f"{tip_id}.md"
    if not path.exists():
        return {"error": f"Tip not found: {tip_id}"}
    lines = path.read_text().strip().splitlines()
    return {
        "id": tip_id,
        "title": lines[0].lstrip("# ").strip(),
        "body": "\n".join(lines[1:]).strip(),
    }


@mcp.resource("tips://all")
def all_tips() -> str:
    """Browse all tips: IDs, titles, and tags."""
    return json.dumps(
        [{"id": n["id"], "title": n["title"], "tags": n["tags"]} for n in load_notes()],
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
