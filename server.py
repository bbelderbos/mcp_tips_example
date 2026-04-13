import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

NOTES_DIR = Path.home() / "code/bobcodesit/notes"

mcp = FastMCP("code-tips")


_cache: list[dict] = []


def load_notes() -> list[dict]:
    global _cache
    if _cache:
        return _cache
    for path in sorted(NOTES_DIR.glob("*.md")):
        lines = path.read_text().strip().splitlines()
        title = lines[0].lstrip("# ").strip()
        tag_line = lines[-1] if lines[-1].startswith("#") else ""
        tags = [t.lstrip("#") for t in tag_line.split() if t.startswith("#")]
        body = "\n".join(lines[1:]).strip()
        _cache.append({"id": path.stem, "title": title, "tags": tags, "body": body})
    return _cache


@mcp.tool()
def search_tips(query: str) -> list[dict]:
    """Search code tips by keyword. Pass a single short keyword (e.g. 'generator', 'decorator', 'contextmanager'), not a full sentence. Returns matching tips with title, tags, and body."""
    q = query.lower()
    return [
        {"id": n["id"], "title": n["title"], "tags": n["tags"], "body": n["body"]}
        for n in load_notes()
        if q in n["title"].lower()
        or q in n["body"].lower()
        or any(q in t for t in n["tags"])
    ]


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
