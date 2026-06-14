"""
Provedor de embedding HuggingFace para Mangaba AI v3.0

Suporta modelos locais (via sentence-transformers) e API de Inferência HF.
Otimizado com cache LRU e processamento em lote.
"""

from __future__ import annotations

from typing import List, Optional
import hashlib
from collections import OrderedDict

from mangaba.embeddings.base import BaseEmbedding


class HuggingFaceEmbedding(BaseEmbedding):
    """Embeddings via modelos HuggingFace (locais ou API)."""

    def __init__(
        self,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        api_key: Optional[str] = None,
        use_local: bool = True,
        cache_size: int = 1000,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._use_local = use_local
        self._cache_size = cache_size
        self._dim = None

        # LRU cache using OrderedDict
        self._cache: OrderedDict[str, List[float]] = OrderedDict()

        if use_local:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(model)
                self._dim = self._model.get_sentence_embedding_dimension()
            except ImportError as exc:
                raise ImportError(
                    "pip install mangaba[embeddings] or sentence-transformers"
                ) from exc
        else:
            try:
                from huggingface_hub import InferenceClient
            except ImportError as exc:
                raise ImportError("pip install huggingface-hub") from exc
            self._client = InferenceClient(token=api_key)
            self._dim = self._get_dimension_from_model(model)

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def _cache_get(self, text: str) -> Optional[List[float]]:
        key = self._get_cache_key(text)
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _cache_set(self, text: str, embedding: List[float]) -> None:
        key = self._get_cache_key(text)
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._cache_size:
                # Remove least recently used
                self._cache.popitem(last=False)
            self._cache[key] = embedding

    def _get_dimension_from_model(self, model: str) -> int:
        dim_map = {
            "BAAI/bge-m3": 1024,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "intfloat/multilingual-e5-large-instruct": 1024,
            "sentence-transformers/all-mpnet-base-v2": 768,
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
            "intfloat/e5-large-v2": 1024,
        }
        return dim_map.get(model, 768)

    def embed_text(self, text: str) -> List[float]:
        cached = self._cache_get(text)
        if cached is not None:
            return cached

        if self._use_local:
            embedding = self._model.encode(text, convert_to_list=True)
        else:
            embedding = self._client.feature_extraction(text, model=self.model)
            # Convert numpy arrays to Python lists
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()
            # Handle single text response (list of floats) or batch (list of lists)
            if (
                isinstance(embedding, list)
                and len(embedding) > 0
                and isinstance(embedding[0], list)
            ):
                embedding = embedding[0]  # Take first if batch response

        self._cache_set(text, embedding)
        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        results = []
        to_embed = []
        to_embed_indices = []

        for i, text in enumerate(texts):
            cached = self._cache_get(text)
            if cached is not None:
                results.append((i, cached))
            else:
                to_embed.append(text)
                to_embed_indices.append(i)

        if to_embed:
            if self._use_local:
                embeddings = self._model.encode(to_embed, convert_to_list=True)
            else:
                raw = self._client.feature_extraction(to_embed, model=self.model)
                if hasattr(raw, "tolist"):
                    raw = raw.tolist()
                if isinstance(raw, list) and raw and isinstance(raw[0], float):
                    embeddings = [raw]
                else:
                    embeddings = [
                        list(e) if not isinstance(e, list) else e for e in raw
                    ]

            for idx, emb in zip(to_embed_indices, embeddings):
                self._cache_set(texts[idx], emb)
                results.append((idx, emb))

        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]

    @property
    def dimension(self) -> int:
        if self._dim is None:
            self._dim = self._get_dimension_from_model(self.model)
        return self._dim
