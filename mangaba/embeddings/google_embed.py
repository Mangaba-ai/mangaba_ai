"""
Provedor de embedding Google para Mangaba AI v3.0
"""

from __future__ import annotations

from typing import List

from mangaba.embeddings.base import BaseEmbedding


class GoogleEmbedding(BaseEmbedding):
    """Embeddings através do Google Generative AI."""

    def __init__(self, api_key: str, model: str = "models/text-embedding-004") -> None:
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise ImportError("pip install google-generativeai") from exc
        genai.configure(api_key=api_key)
        self._genai = genai
        self.model = model
        self._dim = 768

    def embed_text(self, text: str) -> List[float]:
        result = self._genai.embed_content(model=self.model, content=text)
        return result["embedding"]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

    @property
    def dimension(self) -> int:
        return self._dim
