"""Implementação de armazenamento de vetores ChromaDB para Mangaba AI."""

from typing import List, Dict, Any, Optional
import uuid

from mangaba.vectorstores import BaseVectorStore

try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False


class ChromaVectorStore(BaseVectorStore):
    """Implementação de armazenamento de vetores usando ChromaDB.

    Esta implementação usa o cliente persistente do ChromaDB para armazenar e
    buscar embeddings de vetores.

    Attributes:
        client: O cliente persistente do ChromaDB.
        collection: A coleção do ChromaDB para armazenar embeddings.
    """

    def __init__(
        self, path: str = "./chroma_db", collection_name: str = "mangaba_collection"
    ):
        """Inicializa o ChromaVectorStore.

        Args:
            path: O caminho para o banco de dados ChromaDB (padrão: "./chroma_db").
            collection_name: O nome da coleção (padrão: "mangaba_collection").

        Raises:
            ImportError: Se o pacote chromadb não estiver instalado.
        """
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb package is required. Install with: pip install mangaba[chroma]"
            )
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Armazena textos com seus embeddings no ChromaDB.

        Args:
            texts: Uma lista de strings de texto para armazenar.
            embeddings: Uma lista de vetores de embedding correspondentes aos textos.
            metadatas: Lista opcional de dicionários de metadados para cada texto.

        Returns:
            Uma lista de IDs para as entradas armazenadas.
        """
        ids = [uuid.uuid4().hex for _ in texts]
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )
        return ids

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca entradas similares no ChromaDB.

        Args:
            query_embedding: O vetor de embedding de consulta.
            top_k: O número máximo de resultados para retornar (padrão: 5).

        Returns:
            Uma lista de dicionários contendo id, content, score e metadata
            para cada resultado.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=top_k
        )

        final = []
        for i in range(len(results["ids"][0])):
            final.append(
                {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "score": 1
                    - results["distances"][0][
                        i
                    ],  # Chroma uses L2 distance by default, score varies
                    "metadata": results["metadatas"][0][i],
                }
            )
        return final

    def delete(self, ids: List[str]) -> None:
        """Exclui entradas por ID.

        Args:
            ids: Uma lista de IDs para excluir.
        """
        self.collection.delete(ids=ids)

    def clear(self) -> None:
        """Remove todas as entradas da coleção."""
        all_ids = self.collection.get()["ids"]
        if all_ids:
            self.collection.delete(ids=all_ids)

    @property
    def count(self) -> int:
        """Retorna o número de entradas armazenadas.

        Returns:
            O número de entradas na coleção.
        """
        return self.collection.count()
