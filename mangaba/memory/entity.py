"""
Memória de entidades para Mangaba AI v3.0

Extrai e rastreia entidades (pessoas, lugares, conceitos) mencionadas
durante conversas, mantendo um resumo em execução para cada entidade.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from mangaba.memory.base import BaseMemory


class EntityMemory(BaseMemory):
    """Armazenamento de entidades em memória que mantém resumos por entidade.

    Esta implementação de memória extrai e rastreia entidades (pessoas, lugares,
    conceitos) mencionadas durante conversas, mantendo um resumo em execução de
    fatos para cada entidade.

    Attributes:
        _entities: Um dicionário mapeando nomes de entidades (minúsculas) para seus
            dados associados incluindo id, nome, fatos e timestamp last_updated.
    """

    def __init__(self) -> None:
        """Inicializa a EntityMemory."""
        # entity_name (lower) -> {id, name, facts: [str], last_updated}
        self._entities: Dict[str, Dict[str, Any]] = {}

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Extrai entidades do conteúdo e armazena fatos sobre elas.

        Args:
            content: O conteúdo para analisar e armazenar.
            metadata: Metadados opcionais. Pode conter {"entities": ["Alice", "Berlin"]}
                para listar entidades explicitamente. Se ausente, uma heurística simples
                (palavras capitalizadas) é usada.

        Returns:
            Uma string separada por vírgulas de IDs de entidades, ou uma string vazia se
            nenhuma entidade foi encontrada.
        """
        meta = metadata or {}
        entities = meta.get("entities") or self._extract_entities(content)

        ids: List[str] = []
        for name in entities:
            key = name.lower().strip()
            if not key:
                continue
            if key not in self._entities:
                eid = uuid.uuid4().hex[:12]
                self._entities[key] = {
                    "id": eid,
                    "name": name,
                    "facts": [],
                    "last_updated": datetime.now().isoformat(),
                }
            entry = self._entities[key]
            entry["facts"].append(content)
            entry["last_updated"] = datetime.now().isoformat()
            ids.append(entry["id"])

        return ",".join(ids) if ids else ""

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Busca por entidades relevantes para a consulta.

        Args:
            query: A consulta de busca.
            top_k: O número máximo de resultados a retornar (padrão: 5).

        Returns:
            Uma lista de entradas de entidades ordenadas por pontuação de relevância.
        """
        q_lower = query.lower()
        scored = []
        for key, entry in self._entities.items():
            score = 0
            if q_lower in key:
                score += 10
            for w in q_lower.split():
                if w in key:
                    score += 3
                for fact in entry["facts"]:
                    if w in fact.lower():
                        score += 1
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Recupera uma entidade por nome.

        Args:
            name: O nome da entidade para recuperar.

        Returns:
            O dicionário da entidade se encontrado, None caso contrário.
        """
        return self._entities.get(name.lower())

    def get_all(self) -> List[Dict[str, Any]]:
        """Retorna todas as entidades armazenadas.

        Returns:
            Uma lista de todas as entradas de entidades no armazenamento de memória.
        """
        return list(self._entities.values())

    def clear(self) -> None:
        """Limpa todas as entidades armazenadas."""
        self._entities.clear()

    @staticmethod
    def _extract_entities(text: str) -> List[str]:
        """Extrai entidades do texto usando uma heurística simples.

        Este método corresponde a sequências de palavras capitalizadas (2+ caracteres) não no
        início da frase para identificar entidades potenciais.

        Args:
            text: O texto para extrair entidades.

        Returns:
            Uma lista de nomes de entidades extraídas.
        """
        # Matches sequences of capitalised words (2+ chars) not at sentence start
        pattern = r"(?<!\.\s)(?<!\n)\b([A-Z][a-z]{1,}\b(?:\s+[A-Z][a-z]{1,}\b)*)"
        matches = re.findall(pattern, text)
        seen: Dict[str, str] = {}
        for m in matches:
            key = m.lower()
            if key not in seen and len(m) > 2:
                seen[key] = m
        return list(seen.values())
