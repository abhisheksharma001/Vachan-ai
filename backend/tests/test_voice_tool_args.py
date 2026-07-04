"""Tests for the Vapi bridge's tool-argument hardening (app.api.voice).

The model writes its own tool-call arguments; malformed JSON there is routine
LLM nondeterminism, not an exceptional condition — it must never 500 a voice
turn. _parse_tool_args is the guard.
"""
from __future__ import annotations

from app.api.voice import _parse_tool_args


def test_valid_arguments_parse():
    assert _parse_tool_args('{"query": "office address", "top_k": 2}') == {
        "query": "office address",
        "top_k": 2,
    }


def test_empty_and_none_default_to_empty_object():
    assert _parse_tool_args(None) == {}
    assert _parse_tool_args("") == {}


def test_malformed_json_returns_none_not_raise():
    assert _parse_tool_args('{"query": "unterminated') is None
    assert _parse_tool_args("not json at all") is None


def test_non_object_payload_returns_none():
    # A bare list/string is valid JSON but not a tool-arguments object.
    assert _parse_tool_args('["query"]') is None
    assert _parse_tool_args('"query"') is None
