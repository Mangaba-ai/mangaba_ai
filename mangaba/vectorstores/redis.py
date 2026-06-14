"""
Armazenamento de vetores Redis usando RediSearch com índice HNSW para busca de similaridade de vetores.

Requer servidor Redis Stack com módulos RediSearch e RedisJSON habilitados.
Instale com: pip install mangaba[redis]
"""

from __future__ import annotations

import json
import os
import struct
import time
import uuid
from typing import Any, Dict, List, Optional

from mangaba.vectorstores.base import BaseVectorStore

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore[assignment]
    REDIS_AVAILABLE = False


def _get_search_classes():
    """Importação preguiçosa de classes RediSearch para suportar mock em testes.

    Returns:
        Uma tupla de classes RediSearch.
    """
    from redis.commands.search.field import TextField, VectorField, TagField
    from redis.commands.search.index_definition import IndexDefinition, IndexType
    from redis.commands.search.query import Query
    from redis.commands.json.path import Path

    return TextField, VectorField, TagField, IndexDefinition, IndexType, Query, Path


class RedisVectorStore(BaseVectorStore):
    """Armazenamento de vetores apoiado por Redis Stack com índice RediSearch HNSW.

    Esta implementação usa o módulo RediSearch do Redis Stack com índices HNSW
    para busca eficiente de similaridade de vetores.

    Attributes:
        _index_name: O nome do índice RediSearch.
        _vector_dimensions: A dimensionalidade dos vetores.
        _distance_metric: A métrica de distância para usar (COSINE, L2 ou IP).
        _key_prefix: O prefixo para chaves Redis.
        _client: A conexão do cliente Redis.
    """

    def __init__(
        self,
        url: str | None = None,
        index_name: str = "mangaba_vectors",
        vector_dimensions: int | None = None,
        embedding_dimensions: int | None = None,
        distance_metric: str = "COSINE",
        hnsw_m: int = 16,
        hnsw_ef_construction: int = 200,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Inicializa o RedisVectorStore.

        Args:
            url: URL de conexão Redis. Se não fornecido, tentará construir a partir de
                host/port/db ou ler das variáveis de ambiente MANGABA_REDIS_URL/REDIS_URL.
            index_name: O nome do índice RediSearch (padrão: "mangaba_vectors").
            vector_dimensions: A dimensionalidade dos vetores (obsoleto, use
                embedding_dimensions). Padrão: 1536.
            embedding_dimensions: A dimensionalidade dos vetores. Padrão: 1536.
            distance_metric: A métrica de distância para usar (padrão: "COSINE").
            hnsw_m: O parâmetro HNSW M (padrão: 16).
            hnsw_ef_construction: O parâmetro HNSW EF_CONSTRUCTION (padrão: 200).
            host: Host Redis (se url não fornecido). Padrão: localhost.
            port: Porta Redis (se url não fornecido). Padrão: 6379.
            db: Número do banco de dados Redis (se url não fornecido). Padrão: 0.
            **kwargs: Argumentos adicionais passados para redis.Redis.from_url.

        Raises:
            ImportError: Se o pacote redis não estiver instalado.
            redis.ConnectionError: Se a conexão com Redis falhar.
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package is required. Install with: pip install mangaba[redis]"
            )

        # Support both vector_dimensions and embedding_dimensions parameter names
        dimensions = vector_dimensions or embedding_dimensions or 1536

        # Build URL from host/port/db if provided, otherwise use url parameter or default
        if url is None:
            if host or port or db is not None:
                host = host or "localhost"
                port = port or 6379
                db = db if db is not None else 0
                resolved_url = f"redis://{host}:{port}/{db}"
            else:
                resolved_url = (
                    os.getenv("MANGABA_REDIS_URL")
                    or os.getenv("REDIS_URL")
                    or "redis://localhost:6379"
                )
        else:
            resolved_url = url

        self._index_name = index_name
        self._vector_dimensions = dimensions
        self._distance_metric = distance_metric.upper()
        self._key_prefix = f"mangaba:{index_name}:"

        # Connect with retry logic to handle Redis startup delays
        self._client: redis.Redis = self._connect_with_retry(resolved_url, **kwargs)

        self._create_index(
            index_name=index_name,
            vector_dimensions=self._vector_dimensions,
            distance_metric=self._distance_metric,
            hnsw_m=hnsw_m,
            hnsw_ef_construction=hnsw_ef_construction,
        )

    def _connect_with_retry(
        self,
        url: str,
        max_retries: int = 15,
        retry_delay: float = 2.0,
        **kwargs: Any,
    ) -> redis.Redis:
        """Conecta ao Redis com repetição automática em falhas de conexão.

        Args:
            url: A URL de conexão Redis.
            max_retries: Número máximo de tentativas de conexão (padrão: 15).
            retry_delay: Atraso entre repetições em segundos (padrão: 2.0).
            **kwargs: Argumentos adicionais passados para redis.Redis.from_url.

        Returns:
            Um cliente Redis conectado.

        Raises:
            redis.ConnectionError: Se a conexão falhar após todas as repetições.
        """
        import sys

        last_error = None
        for attempt in range(max_retries):
            try:
                print(
                    f"[Redis] Attempt {attempt + 1}/{max_retries} to connect to {url.split('@')[-1]}",
                    file=sys.stderr,
                )
                client: redis.Redis = redis.Redis.from_url(
                    url, decode_responses=True, **kwargs
                )
                client.ping()
                print(
                    f"[Redis] ✓ Connected successfully on attempt {attempt + 1}!",
                    file=sys.stderr,
                )
                return client
            except (redis.ConnectionError, ConnectionRefusedError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(
                        f"[Redis] ✗ Connection failed: {e}. Retrying in {retry_delay}s...",
                        file=sys.stderr,
                    )
                    time.sleep(retry_delay)
                    continue

        error_msg = f"Failed to connect to Redis after {max_retries} attempts (waited {max_retries * retry_delay}s total)"
        print(f"[Redis] ✗ {error_msg}", file=sys.stderr)
        raise last_error or redis.ConnectionError(error_msg)

    def _create_index(
        self,
        index_name: str,
        vector_dimensions: int,
        distance_metric: str,
        hnsw_m: int,
        hnsw_ef_construction: int,
    ) -> None:
        """Cria o índice RediSearch se ele não existir.

        Args:
            index_name: O nome do índice.
            vector_dimensions: A dimensionalidade dos vetores.
            distance_metric: A métrica de distância para usar.
            hnsw_m: O parâmetro HNSW M.
            hnsw_ef_construction: O parâmetro HNSW EF_CONSTRUCTION.
        """
        TextField, VectorField, TagField, IndexDefinition, IndexType, Query, Path = (
            _get_search_classes()
        )

        try:
            self._client.ft(index_name).info()
            return
        except Exception:
            pass

        schema = (
            TagField("$.id", as_name="id"),
            TextField("$.text", as_name="text", weight=1.0),
            VectorField(
                "$.embedding",
                "HNSW",
                {
                    "TYPE": "FLOAT32",
                    "DIM": vector_dimensions,
                    "DISTANCE_METRIC": distance_metric,
                    "M": hnsw_m,
                    "EF_CONSTRUCTION": hnsw_ef_construction,
                },
                as_name="embedding",
            ),
            TextField("$.metadata", as_name="metadata"),
        )
        definition = IndexDefinition(
            prefix=[self._key_prefix], index_type=IndexType.JSON
        )
        self._client.ft(index_name).create_index(fields=schema, definition=definition)

    def _pack_vector(self, embedding: List[float]) -> bytes:
        """Empacota uma lista de floats em bytes para Redis.

        Args:
            embedding: O vetor de embedding para empacotar.

        Returns:
            A representação em bytes empacotada do vetor.
        """
        return struct.pack(f"{len(embedding)}f", *embedding)

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Armazena textos com seus embeddings no Redis.

        Args:
            texts: Uma lista de strings de texto para armazenar.
            embeddings: Uma lista de vetores de embedding correspondentes aos textos.
            metadatas: Lista opcional de dicionários de metadados para cada texto.

        Returns:
            Uma lista de IDs para as entradas armazenadas.
        """
        ids: List[str] = []
        pipe = self._client.pipeline(transaction=False)

        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            eid = uuid.uuid4().hex[:12]
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}

            key = f"{self._key_prefix}{eid}"
            doc = {
                "id": eid,
                "text": text,
                "embedding": [float(x) for x in emb],
                "metadata": json.dumps(metadata),
            }
            pipe.json().set(key, "$", doc)
            ids.append(eid)

        pipe.execute()
        return ids

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca entradas similares usando similaridade de vetores.

        Args:
            query_embedding: O vetor de embedding de consulta.
            top_k: O número máximo de resultados para retornar (padrão: 5).

        Returns:
            Uma lista de dicionários contendo id, content, score e metadata
            para cada resultado, ordenados por pontuação de similaridade.
        """
        _, _, _, _, _, Query, _ = _get_search_classes()

        query_vector = self._pack_vector(query_embedding)

        base_query = "*=>[KNN $k @embedding $vector AS score]"
        q = (
            Query(base_query)
            .sort_by("score")
            .return_fields("id", "text", "metadata", "score")
            .dialect(2)
            .paging(0, top_k)
        )

        params = {"k": str(top_k), "vector": query_vector}
        results = self._client.ft(self._index_name).search(q, params)

        output = []
        for doc in results.docs:
            raw_score = (
                float(doc.score)
                if hasattr(doc, "score") and doc.score is not None
                else 0.0
            )

            if self._distance_metric == "COSINE":
                similarity = 1.0 - (raw_score / 2.0)
            elif self._distance_metric == "L2":
                similarity = 1.0 / (1.0 + raw_score) if raw_score > 0 else 1.0
            else:
                similarity = 1.0 - raw_score

            metadata = {}
            if hasattr(doc, "metadata") and doc.metadata:
                try:
                    metadata = json.loads(doc.metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}

            output.append(
                {
                    "id": doc.id if hasattr(doc, "id") else "",
                    "content": doc.text if hasattr(doc, "text") else "",
                    "score": similarity,
                    "metadata": metadata,
                }
            )

        return output

    def delete(self, ids: List[str]) -> None:
        """Exclui entradas por ID.

        Args:
            ids: Uma lista de IDs para excluir.
        """
        pipe = self._client.pipeline(transaction=False)
        for eid in ids:
            key = f"{self._key_prefix}{eid}"
            pipe.delete(key)
        pipe.execute()

    def clear(self) -> None:
        """Remove todas as entradas do armazenamento."""
        cursor = 0
        while True:
            cursor, keys = self._client.scan(
                cursor, match=f"{self._key_prefix}*", count=100
            )
            if keys:
                self._client.delete(*keys)
            if cursor == 0:
                break

    @property
    def count(self) -> int:
        """Retorna o número de entradas armazenadas.

        Returns:
            O número de entradas no armazenamento.
        """
        cursor = 0
        total = 0
        while True:
            cursor, keys = self._client.scan(
                cursor, match=f"{self._key_prefix}*", count=100
            )
            total += len(keys)
            if cursor == 0:
                break
        return total

    def close(self) -> None:
        """Fecha a conexão Redis."""
        self._client.close()

    def __del__(self) -> None:
        """Limpeza quando o objeto é excluído."""
        try:
            self.close()
        except Exception:
            pass
