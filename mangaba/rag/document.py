"""
Modelo de Documento para pipeline RAG do Mangaba AI.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Um pedaço de conteúdo com metadados associados.

    Esta classe representa um documento ou pedaço de documento no pipeline RAG,
    contendo o conteúdo de texto, metadados opcionais e vetor de embedding opcional.

    Attributes:
        content: O conteúdo de texto do documento.
        metadata: Dicionário de metadados opcional associado ao documento.
        embedding: Vetor de embedding opcional para o conteúdo do documento.
    """

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = Field(default=None, exclude=True)

    @property
    def page_content(self) -> str:
        """Alias para content, mantido para compatibilidade com estilo LangChain.

        Returns:
            O conteúdo do documento.
        """
        return self.content

    def __str__(self) -> str:
        """Retorna uma representação em string do documento.

        Returns:
            Os primeiros 120 caracteres do conteúdo do documento.
        """
        return self.content[:120]
