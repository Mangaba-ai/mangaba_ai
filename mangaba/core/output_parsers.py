"""
Analisadores de saída para Mangaba AI v3.0

Analisa a saída de texto bruto do LLM em objetos Python estruturados.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type

from pydantic import BaseModel


class BaseOutputParser(ABC):
    """Analisador abstrato que converte texto bruto em um valor estruturado.

    As subclasses devem implementar o método parse() para converter a saída do LLM
    em tipos de dados específicos (JSON, modelos Pydantic, listas, etc.).
    """

    @abstractmethod
    def parse(self, text: str) -> Any:
        """Analisa texto bruto em um valor estruturado.

        Args:
            text: A saída de texto bruto de um LLM.

        Returns:
            O valor estruturado analisado (dict, list, instância de modelo, etc.).

        Raises:
            ValueError: Se o texto não puder ser analisado no formato esperado.
        """
        ...

    def get_format_instructions(self) -> str:
        """Retorna instruções para incluir no prompt para que o LLM formate
        sua saída corretamente.

        Returns:
            String contendo instruções de formato para o LLM.
        """
        return ""


class JSONOutputParser(BaseOutputParser):
    """Extrai o primeiro objeto ou array JSON do texto.

    Tenta encontrar JSON em blocos de código markdown ou como a primeira
    estrutura semelhante a JSON no texto.
    """

    def parse(self, text: str) -> Any:
        """Extrai e analisa JSON do texto.

        Args:
            text: A saída de texto bruto de um LLM.

        Returns:
            Objeto ou array JSON analisado.

        Raises:
            ValueError: Se nenhum JSON válido for encontrado no texto.
        """
        # Try to find JSON block
        for pattern in [r"```json\s*([\s\S]*?)```", r"```([\s\S]*?)```"]:
            m = re.search(pattern, text)
            if m:
                return json.loads(m.group(1).strip())
        # Fallback: find first { or [
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
        raise ValueError("No JSON found in output")

    def get_format_instructions(self) -> str:
        """Retorna instruções de formato para saída JSON.

        Returns:
            String de instruções solicitando formato JSON.
        """
        return "Responda com um objeto JSON válido."


class PydanticOutputParser(BaseOutputParser):
    """Analisa a saída em uma instância de modelo Pydantic.

    Usa JSONOutputParser internamente para extrair JSON, então valida
    contra o esquema do modelo Pydantic fornecido.
    """

    def __init__(self, model: Type[BaseModel]) -> None:
        """Inicializa o analisador de saída Pydantic.

        Args:
            model: A classe de modelo Pydantic para analisar a saída.
        """
        self.model = model

    def parse(self, text: str) -> BaseModel:
        """Analisa texto em uma instância de modelo Pydantic.

        Args:
            text: A saída de texto bruto de um LLM.

        Returns:
            Uma instância do modelo Pydantic configurado.

        Raises:
            ValueError: Se o JSON analisado não for um dict ou não corresponder ao esquema.
        """
        json_parser = JSONOutputParser()
        data = json_parser.parse(text)
        if isinstance(data, dict):
            return self.model(**data)
        raise ValueError(
            f"Expected a JSON object for {self.model.__name__}, got {type(data).__name__}"
        )

    def get_format_instructions(self) -> str:
        """Retorna instruções de formato com o esquema Pydantic.

        Returns:
            String contendo o esquema JSON para o modelo.
        """
        schema = self.model.model_json_schema()
        return (
            f"Responda com um objeto JSON correspondente a este esquema:\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```"
        )


class ListOutputParser(BaseOutputParser):
    """Extrai uma lista de itens do texto (numerados ou com marcadores).

    Analisa listas numeradas (1., 2., 3.) ou listas com marcadores (-, *, •) do
    texto e as retorna como uma lista de strings.
    """

    def parse(self, text: str) -> List[str]:
        """Extrai itens de lista de texto numerado ou com marcadores.

        Args:
            text: A saída de texto bruto de um LLM.

        Returns:
            Lista de itens extraídos como strings.
        """
        lines = text.strip().splitlines()
        items: List[str] = []
        for line in lines:
            cleaned = re.sub(r"^[\s]*[-*•\d.)\]]+[\s]*", "", line).strip()
            if cleaned:
                items.append(cleaned)
        return items

    def get_format_instructions(self) -> str:
        """Retorna instruções de formato para saída de lista.

        Returns:
            String de instruções solicitando formato de lista numerada.
        """
        return "Responda com uma lista numerada, um item por linha."


class MarkdownOutputParser(BaseOutputParser):
    """Divide o texto markdown em seções por cabeçalhos.

    Analisa o texto markdown e retorna um dicionário mapeando nomes
    de cabeçalhos para suas seções de conteúdo.
    """

    def parse(self, text: str) -> Dict[str, str]:
        """Analisa o texto markdown em seções por cabeçalhos.

        Args:
            text: A saída de texto markdown bruto de um LLM.

        Returns:
            Dicionário mapeando nomes de cabeçalhos para suas seções de conteúdo.
        """
        sections: Dict[str, str] = {}
        current_heading = "intro"
        buffer: List[str] = []

        for line in text.splitlines():
            heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if heading_match:
                # Save previous section
                if buffer:
                    sections[current_heading] = "\n".join(buffer).strip()
                current_heading = heading_match.group(2).strip()
                buffer = []
            else:
                buffer.append(line)

        if buffer:
            sections[current_heading] = "\n".join(buffer).strip()
        return sections

    def get_format_instructions(self) -> str:
        """Retorna instruções de formato para saída markdown.

        Returns:
            String de instruções solicitando formato markdown com cabeçalhos de seção.
        """
        return "Responda em formato Markdown com cabeçalhos de seção claros."
