"""Tests for text utilities and LLM JSON tolerance."""

from __future__ import annotations

import pytest

from app.services.knowledge_base import chunk_text, score_chunk, tokenize


class TestChunkText:
    def test_basic_chunking(self):
        text = "a" * 250
        chunks = chunk_text(text, 100, 20)
        assert chunks[0] == "a" * 100
        assert len(chunks) == 3

    def test_whitespace_normalized(self):
        chunks = chunk_text("hello\n\n  world  ", 100, 10)
        assert chunks == ["hello world"]

    def test_empty_text(self):
        assert chunk_text("", 100, 10) == []

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            chunk_text("x", 0, 0)
        with pytest.raises(ValueError):
            chunk_text("x", 10, 10)
        with pytest.raises(ValueError):
            chunk_text("x", 10, -1)

    def test_no_infinite_loop_on_small_overlap(self):
        chunks = chunk_text("abcdef", 3, 2)
        assert "".join(chunks).startswith("abc")


class TestTokenize:
    def test_mixed_language(self):
        tokens = tokenize("Hello 世界 python")
        assert "hello" in tokens
        assert "世" in tokens and "界" in tokens
        assert "python" in tokens

    def test_empty(self):
        assert tokenize("") == []


class TestScoreChunk:
    def test_hits(self):
        score = score_chunk("python 后端 开发", ["python", "后端"])
        assert score > 0

    def test_no_hits(self):
        assert score_chunk("java 开发", ["python"]) == 0.0

    def test_empty_query(self):
        assert score_chunk("anything", []) == 0.0


class TestParseJsonFromLlm:
    def _parse(self):
        from app.services.llm_client import parse_json_from_llm

        return parse_json_from_llm

    def test_clean_json(self):
        assert self._parse()('{"a": 1}') == {"a": 1}

    def test_fenced_json(self):
        text = '```json\n{"name": "张三", "age": 22}\n```'
        assert self._parse()(text) == {"name": "张三", "age": 22}

    def test_prose_wrapped_json(self):
        text = '好的，以下是简历：\n{"summary": "你好"}\n希望有帮助'
        assert self._parse()(text) == {"summary": "你好"}

    def test_braces_inside_strings(self):
        text = '{"text": "包含 } 特殊字符 {", "n": 1}'
        assert self._parse()(text)["n"] == 1

    def test_garbage_raises(self):
        with pytest.raises(ValueError):
            self._parse()("完全没有 JSON")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            self._parse()("")

    def test_array_is_rejected(self):
        with pytest.raises(ValueError):
            self._parse()("[1, 2, 3]")
