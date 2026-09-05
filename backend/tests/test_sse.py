"""Tests for the SSE parser (no plugin deps — plain asyncio.run)."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from app.routes.chat import parse_upstream_sse


async def _lines(lines: list[str]) -> AsyncIterator[str]:
    for line in lines:
        yield line + "\n"


def _collect(events) -> list[str]:
    async def runner() -> list[str]:
        return [event async for event in events]

    return asyncio.run(runner())


def _chunk(text: str) -> str:
    return json.dumps({"choices": [{"delta": {"content": text}}]}, ensure_ascii=False)


def test_basic_stream():
    raw = [
        f"data: {_chunk('你好')}",
        f"data: {_chunk('，世界')}",
        "data: [DONE]",
    ]
    events = _collect(parse_upstream_sse(_lines(raw)))
    assert events[0] == "data: 你好\n\n"
    assert events[1] == "data: ，世界\n\n"
    assert events[-1] == "data: [DONE]\n\n"


def test_multiline_delta_escaped():
    raw = [f"data: {_chunk('第一行\n第二行')}", "data: [DONE]"]
    events = _collect(parse_upstream_sse(_lines(raw)))
    assert events[0] == "data: 第一行\ndata: 第二行\n\n"


def test_data_without_space():
    raw = [f"data:{_chunk('x')}", "data: [DONE]"]
    events = _collect(parse_upstream_sse(_lines(raw)))
    assert events[0] == "data: x\n\n"


def test_malformed_json_skipped():
    raw = ["data: {broken json", f"data: {_chunk('ok')}", "data: [DONE]"]
    events = _collect(parse_upstream_sse(_lines(raw)))
    assert "data: ok\n\n" in events


def test_empty_choices_guarded():
    raw = ["data: " + json.dumps({"choices": []}), f"data: {_chunk('y')}", "data: [DONE]"]
    events = _collect(parse_upstream_sse(_lines(raw)))
    assert events == ["data: y\n\n", "data: [DONE]\n\n"]


def test_missing_done_terminated():
    raw = [f"data: {_chunk('z')}"]
    events = _collect(parse_upstream_sse(_lines(raw)))
    assert events[-1] == "data: [DONE]\n\n"
