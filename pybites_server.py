# PyBites content MCP server — 3 tools:
#
# search_content  – "Find PyBites articles on decorators" / "Any bites on list comprehensions?"
# get_item        – "Get the full summary for the decorator use cases article"
# topic_digest    – "What does PyBites have on generators across all content types?"
#
# Chained: "Find a PyBites article on decorators, get the full summary, write me a LinkedIn post"

import html
import json
import re
import urllib.request
from functools import cache

from mcp.server.fastmcp import FastMCP

CONTENT_URL = "https://raw.githubusercontent.com/bbelderbos/pybites-search/refs/heads/main/data/content.json"

mcp = FastMCP("pybites-search")


@cache
def load_content() -> list[dict]:
    with urllib.request.urlopen(CONTENT_URL) as resp:
        return json.loads(resp.read())


def clean_summary(raw: str) -> str:
    text = html.unescape(raw)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"Continue reading\s*.*", "", text, flags=re.IGNORECASE).strip()
    return text


@mcp.tool()
def search_content(query: str, content_type: str = "", limit: int = 10) -> list[dict]:
    """Search PyBites content by keyword. Optionally filter by content_type: article, bite, podcast, video, tip. Returns a list of matching titles, content types, and links."""
    pattern = re.compile(rf"\b{re.escape(query.lower())}\b")
    ct = content_type.lower() if content_type else ""
    results = [
        {
            "title": item["title"],
            "content_type": item["content_type"],
            "link": item["link"],
        }
        for item in load_content()
        if (not ct or item["content_type"] == ct)
        and (
            pattern.search(item["title"].lower())
            or pattern.search(item["summary"].lower())
        )
    ]
    return results[:limit]


@mcp.tool()
def get_item(title_or_link: str) -> dict:
    """Get full details for one PyBites item by its title (partial match) or exact link. Returns title, content_type, link, and a clean summary."""
    needle = title_or_link.lower()
    for item in load_content():
        if needle in item["link"].lower() or needle in item["title"].lower():
            return {
                "title": item["title"],
                "content_type": item["content_type"],
                "link": item["link"],
                "summary": clean_summary(item["summary"]),
            }
    return {"error": f"No item found for: {title_or_link}"}


@mcp.tool()
def topic_digest(topic: str, max_per_type: int = 2) -> dict[str, list[dict]]:
    """Search a topic across all content types and return the top results grouped by type. Good for 'what does PyBites have on X?'"""
    pattern = re.compile(rf"\b{re.escape(topic.lower())}\b")
    digest: dict[str, list[dict]] = {}
    for item in load_content():
        if pattern.search(item["title"].lower()) or pattern.search(
            item["summary"].lower()
        ):
            ct = item["content_type"]
            bucket = digest.setdefault(ct, [])
            if len(bucket) < max_per_type:
                bucket.append({"title": item["title"], "link": item["link"]})
    return digest


# To register with Claude Code CLI:
#   claude mcp add pybites-search -- uv run --directory /Users/pybob/code/tips-mcp python pybites_server.py
if __name__ == "__main__":
    mcp.run()
