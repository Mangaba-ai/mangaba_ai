"""
Provedor de embedding OpenAI para Mangaba AI v3.0
"""

from __future__ import annotations

from typing import List

from mangaba.embeddings.base import BaseEmbedding


class OpenAIEmbedding(BaseEmbedding):
    """Embeddings via modelos de text-embedding da OpenAI."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise ImportError("pip install openai") from exc
        self._client = OpenAI(api_key=api_key)
        self.model = model
        self._dim = 1536 if "small" in model else 3072

    def embed_text(self, text: str) -> List[float]:
        resp = self._client.embeddings.create(input=[text], model=self.model)
        return resp.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        resp = self._client.embeddings.create(input=texts, model=self.model)
        return [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]

    @property
    def dimension(self) -> int:
        return self._dim
