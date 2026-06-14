"""
Retriever: envolve um embedding + armazenamento vetorial para encontrar documentos relevantes.
"""

from __future__ import annotations

from typing import List

from mangaba.rag.document import Document
from mangaba.embeddings.base import BaseEmbedding
from mangaba.vectorstores.base import BaseVectorStore


class Retriever:
    """Encapsula embedding e armazenamento vetorial para busca de similaridade.

    Esta classe combina um modelo de embedding com um armazenamento vetorial para fornecer
    funcionalidade de recuperação de documentos baseada em similaridade semântica.

    Example::

        retriever = Retriever(embedding=OpenAIEmbedding(key), store=InMemoryVectorStore())
        retriever.add_documents(docs)
        results = retriever.search("What is AI?")

    Attributes:
        embedding: O modelo de embedding para usar na vetorização de texto.
        store: O armazenamento vetorial para usar no armazenamento e busca de documentos.
    """

    def __init__(self, embedding: BaseEmbedding, store: BaseVectorStore) -> None:
        """Inicializa o Retriever.

        Args:
            embedding: O modelo de embedding para usar na vetorização de texto.
            store: O armazenamento vetorial para usar no armazenamento e busca de documentos.
        """
        self.embedding = embedding
        self.store = store

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Adiciona documentos ao armazenamento vetorial.

        Args:
            documents: Uma lista de objetos Document para adicionar.

        Returns:
            Uma lista de IDs para os documentos adicionados.
        """
        texts = [d.content for d in documents]
        embeddings = self.embedding.embed_batch(texts)
        metadatas = [d.metadata for d in documents]
        return self.store.add(texts, embeddings, metadatas)

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """Busca por documentos semelhantes à consulta.

        Args:
            query: A consulta de busca.
            top_k: O número máximo de resultados a retornar (padrão: 5).

        Returns:
            Uma lista de objetos Document ordenados por pontuação de similaridade.
        """
        query_emb = self.embedding.embed_text(query)
        results = self.store.search(query_emb, top_k=top_k)
        return [
            Document(
                content=r["content"],
                metadata={**r.get("metadata", {}), "score": r.get("score", 0)},
            )
            for r in results
        ]

    def clear(self) -> None:
        """Limpa todos os documentos do armazenamento vetorial."""
        self.store.clear()
