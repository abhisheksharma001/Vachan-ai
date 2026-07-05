"""
Unit tests for the semantic embedder — model is mocked so these run everywhere.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.memory import embedder


class _FakeModel:
    def __init__(self, dim: int = 1024):
        self.dim = dim

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        # Deterministic pseudo-random vectors seeded by text hash.
        return np.array(
            [
                self._vec(t)
                for t in texts
            ],
            dtype=np.float32,
        )

    def _vec(self, text: str):
        rng = np.random.default_rng(hash(text) & 0xFFFFFFFF)
        return rng.standard_normal(self.dim).astype(np.float32)


@pytest.fixture(autouse=True)
def _reset_model(monkeypatch):
    embedder._model = None
    embedder._load_failed = False
    yield
    embedder._model = None
    embedder._load_failed = False


def test_encode_fragments_returns_normalized_vectors(monkeypatch):
    monkeypatch.setattr(embedder, "_model", _FakeModel())
    vectors = embedder.encode_fragments(["hello", "world"])
    assert vectors is not None
    assert len(vectors) == 2
    assert len(vectors[0]) == 1024
    # L2-normalized.
    assert abs(np.linalg.norm(vectors[0]) - 1.0) < 1e-5
    assert abs(np.linalg.norm(vectors[1]) - 1.0) < 1e-5


def test_encode_query_prefixes_text(monkeypatch):
    captured: list[str] = []

    class _SpyModel:
        def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
            captured.extend(texts)
            return np.ones((len(texts), 1024), dtype=np.float32)

    monkeypatch.setattr(embedder, "_model", _SpyModel())
    result = embedder.encode_query("where did we go?")
    assert result is not None
    assert len(captured) == 1
    assert captured[0].startswith("Instruct:")
    assert "where did we go?" in captured[0]


def test_encode_returns_none_when_model_unavailable():
    embedder._load_failed = True
    assert embedder.encode_fragments(["hello"]) is None
    assert embedder.encode_query("hello") is None
    assert embedder.available() is False
