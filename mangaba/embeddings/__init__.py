"""Provedores de embedding para Mangaba AI v3.0.

Este módulo fornece funcionalidade de embedding de texto para busca semântica
e aplicações RAG, com suporte para múltiplos provedores:

- OpenAIEmbedding: Modelos de text-embedding da OpenAI
- GoogleEmbedding: API de embedding do Google
- HuggingFaceEmbedding: Modelos de código aberto via HuggingFace

Todos os provedores implementam a interface BaseEmbedding para consistência.
"""

from mangaba.embeddings.base import BaseEmbedding
from mangaba.embeddings.openai_embed import OpenAIEmbedding
from mangaba.embeddings.google_embed import GoogleEmbedding
from mangaba.embeddings.huggingface_embed import HuggingFaceEmbedding

__all__ = [
    "BaseEmbedding",
    "OpenAIEmbedding",
    "GoogleEmbedding",
    "HuggingFaceEmbedding",
]
