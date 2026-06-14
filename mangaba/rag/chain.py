"""
RAGChain: geração aumentada por recuperação de ponta a ponta.
"""

from __future__ import annotations

from typing import Any, List, Optional

from mangaba.rag.document import Document
from mangaba.rag.retriever import Retriever


class RAGChain:
    """Combina um Retriever com um LLM para responder perguntas usando contexto recuperado.

    Esta classe implementa geração aumentada por recuperação (RAG), que recupera
    documentos relevantes de uma base de conhecimento e os usa como contexto para um LLM
    gerar respostas para perguntas.

    Example::

        chain = RAGChain(retriever=retriever, llm=llm_client)
        answer = chain.query("What is the capital of France?")

    Attributes:
        retriever: O recuperador para usar na busca de documentos.
        llm: O cliente LLM para usar na geração de respostas.
        template: O modelo de prompt para usar na geração de respostas.
        top_k: O número de documentos para recuperar para cada consulta.
    """

    DEFAULT_TEMPLATE = (
        "Answer the question based on the context below.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    )

    def __init__(
        self,
        retriever: Retriever,
        llm: Any,  # LLMClient
        prompt_template: Optional[str] = None,
        top_k: int = 5,
    ) -> None:
        """Inicializa a RAGChain.

        Args:
            retriever: O recuperador para usar na busca de documentos.
            llm: O cliente LLM para usar na geração de respostas.
            prompt_template: Modelo de prompt personalizado opcional. Se não fornecido,
                usa o modelo padrão.
            top_k: O número de documentos para recuperar para cada consulta (padrão: 5).
        """
        self.retriever = retriever
        self.llm = llm
        self.template = prompt_template or self.DEFAULT_TEMPLATE
        self.top_k = top_k

    def query(self, question: str) -> str:
        """Recupera documentos relevantes e gera uma resposta.

        Args:
            question: A pergunta para responder.

        Returns:
            A resposta gerada como uma string.
        """
        docs = self.retriever.search(question, top_k=self.top_k)
        context = self._format_context(docs)
        prompt = self.template.format(context=context, question=question)
        return self.llm.generate_text(prompt)

    def query_with_sources(self, question: str) -> dict:
        """Retorna a resposta mais os documentos de origem.

        Args:
            question: A pergunta para responder.

        Returns:
            Um dicionário com chaves "answer" (a resposta gerada) e "sources"
            (a lista de documentos recuperados).
        """
        docs = self.retriever.search(question, top_k=self.top_k)
        context = self._format_context(docs)
        prompt = self.template.format(context=context, question=question)
        answer = self.llm.generate_text(prompt)
        return {"answer": answer, "sources": docs}

    @staticmethod
    def _format_context(docs: List[Document]) -> str:
        """Formata uma lista de documentos em uma string de contexto.

        Args:
            docs: Os documentos para formatar.

        Returns:
            Uma string com conteúdos de documentos separados por "---".
        """
        return "\n---\n".join(d.content for d in docs)
