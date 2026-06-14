"""
Ferramentas de processamento de texto para Mangaba AI v3.0
"""

from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, Field

from mangaba.tools.base import BaseTool


# ── Text Splitter ──────────────────────────────────────────────────────────


class TextSplitInput(BaseModel):
    """Esquema de entrada para a ferramenta de divisão de texto."""

    text: str = Field(..., description="O texto para dividir em partes")
    chunk_size: int = Field(default=1000, description="Máximo de caracteres por parte")
    chunk_overlap: int = Field(
        default=200, description="Sobreposição entre partes consecutivas"
    )


class TextSplitterTool(BaseTool):
    """Divide texto em partes menores com sobreposição.

    Usa uma estratégia de divisão recursiva que tenta quebrar o texto em
    limites naturais (parágrafos, sentenças, palavras) antes de recorrer à
    divisão por caracteres. A sobreposição entre as partes ajuda a manter o contexto.
    """

    name = "text_splitter"
    description = "Divide texto longo em partes menores com sobreposição opcional"
    args_schema = TextSplitInput

    _SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def _run(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> str:
        """Divide o texto em partes.

        Args:
            text: O texto para dividir.
            chunk_size: Máximo de caracteres por parte (padrão: 1000).
            chunk_overlap: Sobreposição entre partes consecutivas (padrão: 200).

        Returns:
            String formatada com partes numeradas.
        """
        chunks = self._recursive_split(
            text, chunk_size, chunk_overlap, self._SEPARATORS
        )
        result_lines = [
            f"--- Chunk {i + 1}/{len(chunks)} ---\n{c}" for i, c in enumerate(chunks)
        ]
        return "\n\n".join(result_lines)

    def _recursive_split(
        self, text: str, chunk_size: int, overlap: int, separators: List[str]
    ) -> List[str]:
        """Divide recursivamente o texto em partes usando separadores especificados.

        Args:
            text: O texto para dividir.
            chunk_size: Máximo de caracteres por parte.
            overlap: Sobreposição entre partes consecutivas.
            separators: Lista de separadores para tentar, em ordem de preferência.

        Returns:
            Lista de partes de texto.
        """
        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else [""]
        parts = text.split(sep) if sep else list(text)

        chunks: List[str] = []
        current = ""
        for part in parts:
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    if len(current) <= chunk_size:
                        chunks.append(current.strip())
                    else:
                        chunks.extend(
                            self._recursive_split(
                                current, chunk_size, overlap, remaining_seps
                            )
                        )
                current = part

        if current.strip():
            if len(current) <= chunk_size:
                chunks.append(current.strip())
            else:
                chunks.extend(
                    self._recursive_split(current, chunk_size, overlap, remaining_seps)
                )

        # Aplicar sobreposição
        if overlap > 0 and len(chunks) > 1:
            overlapped: List[str] = [chunks[0]]
            for i in range(1, len(chunks)):
                prev = chunks[i - 1]
                overlap_text = prev[-overlap:] if len(prev) > overlap else prev
                overlapped.append(overlap_text + chunks[i])
            return overlapped
        return chunks


# ── Word Counter ───────────────────────────────────────────────────────────


class WordCountInput(BaseModel):
    """Esquema de entrada para a ferramenta de contador de palavras."""

    text: str = Field(..., description="Texto para contar palavras")


class WordCounterTool(BaseTool):
    """Conta palavras, sentenças e caracteres no texto.

    Fornece estatísticas incluindo contagem de palavras, contagem de caracteres,
    contagem de sentenças e contagem de parágrafos para o texto fornecido.
    """

    name = "word_counter"
    description = "Conta palavras, sentenças e caracteres no texto"
    args_schema = WordCountInput

    def _run(self, text: str) -> str:
        """Conta palavras, sentenças, caracteres e parágrafos no texto.

        Args:
            text: O texto para analisar.

        Returns:
            String formatada com contagem de palavras, contagem de caracteres,
            contagem de sentenças e contagem de parágrafos.
        """
        words = len(text.split())
        chars = len(text)
        sentences = len(re.split(r"[.!?]+", text.strip())) - 1 if text.strip() else 0
        paragraphs = len([p for p in text.split("\n\n") if p.strip()])
        return (
            f"Words: {words}\n"
            f"Characters: {chars}\n"
            f"Sentences: {max(sentences, 0)}\n"
            f"Paragraphs: {paragraphs}"
        )
