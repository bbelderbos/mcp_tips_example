from collections import defaultdict
from unittest.mock import patch

import pytest

from pybites_server import clean_summary, get_item, search_content, topic_digest

FAKE_CONTENT = [
    {
        "title": "Decorator Patterns in Python",
        "content_type": "article",
        "link": "https://pybit.es/decorator-patterns",
        "summary": "Learn about decorator patterns &amp; <b>use cases</b>. Continue reading more...",
    },
    {
        "title": "List Comprehensions Bite",
        "content_type": "bite",
        "link": "https://pybitesplatform.com/bites/f-strings-and-a-simple-ifelse/",
        "summary": "Practice list comprehensions in Python.",
    },
    {
        "title": "Playlist Generator",
        "content_type": "article",
        "link": "https://pybit.es/playlist",
        "summary": "Build a playlist generator in Python.",
    },
    {
        "title": "Testing with pytest",
        "content_type": "article",
        "link": "https://pybit.es/pytest-intro",
        "summary": "An intro to testing with pytest and fixtures.",
    },
    {
        "title": "Python Decorators Podcast",
        "content_type": "podcast",
        "link": "https://pybit.es/podcast/decorators",
        "summary": "We discuss decorator use cases with a guest.",
    },
]


@pytest.fixture(autouse=True)
def mock_load_content():
    with patch("pybites_server.load_content", return_value=FAKE_CONTENT):
        yield


class TestCleanSummary:
    def test_unescapes_html_entities(self):
        assert "&" in clean_summary("foo &amp; bar")

    def test_strips_html_tags(self):
        assert "<b>" not in clean_summary("<b>bold</b>")

    def test_removes_continue_reading(self):
        result = clean_summary("Some text. Continue reading more stuff")
        assert "Continue reading" not in result

    def test_strips_trailing_whitespace(self):
        assert clean_summary("  hello  ") == "hello"


class TestSearchContent:
    def test_returns_matching_items(self):
        results = search_content("decorator")
        assert {r["title"] for r in results} == {
            "Decorator Patterns in Python",
            "Python Decorators Podcast",
        }

    def test_word_boundary_no_false_positives(self):
        # "list" should not match "playlist"
        results = search_content("list")
        assert len(results) == 1

    def test_filters_by_content_type(self):
        results = search_content("decorator", content_type="article")
        assert len(results) == 1
        assert results[0]["content_type"] == "article"

    def test_respects_limit(self):
        results = search_content("decorator", limit=1)
        assert len(results) == 1

    def test_result_shape(self):
        results = search_content("decorator")
        assert all(set(r.keys()) == {"title", "content_type", "link"} for r in results)

    def test_no_match_returns_empty(self):
        assert search_content("nonexistent_xyz") == []


class TestGetItem:
    def test_finds_by_partial_title(self):
        result = get_item("decorator patterns")
        assert result["title"] == "Decorator Patterns in Python"

    def test_finds_by_link(self):
        result = get_item(
            "https://pybitesplatform.com/bites/f-strings-and-a-simple-ifelse/"
        )
        assert result["title"] == "List Comprehensions Bite"

    def test_result_shape(self):
        result = get_item("pytest")
        assert set(result.keys()) == {"title", "content_type", "link", "summary"}

    def test_summary_is_cleaned(self):
        result = get_item("decorator patterns")
        assert "<b>" not in result["summary"]
        assert "Continue reading" not in result["summary"]

    def test_not_found_returns_error(self):
        result = get_item("nonexistent_xyz")
        assert "error" in result


class TestTopicDigest:
    def test_groups_by_content_type(self):
        result = topic_digest("decorator")
        assert set(result.keys()) == {"article", "podcast"}

    def test_respects_max_per_type(self):
        result = topic_digest("decorator", max_per_type=1)
        assert all(len(items) <= 1 for items in result.values())

    def test_result_items_have_title_and_link(self):
        result = topic_digest("decorator")
        assert all(
            set(item.keys()) == {"title", "link"}
            for items in result.values()
            for item in items
        )

    def test_no_match_returns_empty(self):
        result = topic_digest("nonexistent_xyz")
        assert result == defaultdict(list)

    def test_returns_defaultdict(self):
        result = topic_digest("decorator")
        assert isinstance(result, defaultdict)
