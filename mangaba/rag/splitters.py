"""
Divisores de texto para pipeline RAG do Mangaba AI.
"""

from __future__ import annotations

from typing import List

from mangaba.rag.document import Document


class RecursiveTextSplitter:
    """Divide texto recursivamente usando uma hierarquia de separadores.

    Este divisor tenta o primeiro separador; se qualquer pedaço ainda for muito grande,
    retorna para separadores subsequentes na hierarquia. Esta abordagem
    ajuda a manter a coerência semântica nos pedaços resultantes.

    Attributes:
        chunk_size: O tamanho máximo de cada pedaço.
        chunk_overlap: O número de caracteres para sobrepor entre pedaços.
        separators: Uma lista de separadores para tentar em ordem, de grosso a fino.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] | None = None,
    ) -> None:
        """Inicializa o RecursiveTextSplitter.

        Args:
            chunk_size: O tamanho máximo de cada pedaço em caracteres (padrão: 1000).
            chunk_overlap: O número de caracteres para sobrepor entre pedaços
                (padrão: 200).
            separators: Uma lista de separadores para tentar em ordem. Se não fornecido,
                usa ["\n\n", "\n", ". ", " ", ""].
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Divide uma lista de documentos em pedaços menores.

        Args:
            documents: Uma lista de objetos Document para dividir.

        Returns:
            Uma lista de pedaços de Document com metadados atualizados incluindo chunk_index
            e total_chunks.
        """
        result: List[Document] = []
        for doc in documents:
            chunks = self._split(doc.content, self.separators)
            for i, chunk in enumerate(chunks):
                meta = {**doc.metadata, "chunk_index": i, "total_chunks": len(chunks)}
                result.append(Document(content=chunk, metadata=meta))
        return result

    def split_text(self, text: str) -> List[str]:
        """Divide texto em pedaços menores.

        Args:
            text: O texto para dividir.

        Returns:
            Uma lista de pedaços de texto.
        """
        return self._split(text, self.separators)

    def _split(self, text: str, separators: List[str]) -> List[str]:
        """Divide texto recursivamente usando os separadores dados.

        Args:
            text: O texto para dividir.
            separators: Uma lista de separadores para tentar em ordem.

        Returns:
            Uma lista de pedaços de texto.
        """
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        sep = separators[0] if separators else ""
        remaining = separators[1:] if len(separators) > 1 else [""]

        parts = text.split(sep) if sep else list(text)

        chunks: List[str] = []
        current = ""
        for part in parts:
            joiner = sep if current else ""
            candidate = current + joiner + part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current.strip():
                    if len(current) > self.chunk_size:
                        chunks.extend(self._split(current, remaining))
                    else:
                        chunks.append(current.strip())
                current = part

        if current.strip():
            if len(current) > self.chunk_size:
                chunks.extend(self._split(current, remaining))
            else:
                chunks.append(current.strip())

        # Aplicar sobreposição
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped: List[str] = [chunks[0]]
            for i in range(1, len(chunks)):
                prev = chunks[i - 1]
                overlap_text = (
                    prev[-self.chunk_overlap :]
                    if len(prev) > self.chunk_overlap
                    else prev
                )
                combined = overlap_text + chunks[i]
                overlapped.append(combined)
            return overlapped

        return chunks
