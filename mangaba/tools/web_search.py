"""
Ferramenta de busca na web usando múltiplos mecanismos de busca
"""

import os
import requests
from typing import Optional
from mangaba.tools.base import BaseTool


class SerperSearchTool(BaseTool):
    """Ferramenta de busca na web usando API Serper.

    Requer: SERPER_API_KEY como variável de ambiente.

    Exemplo:
        tool = SerperSearchTool()
        results = tool.run("últimas tendências de IA 2024")
    """

    name = "serper_search"
    description = "Busca na web usando API Serper para informações e notícias atuais"

    def __init__(self, api_key: Optional[str] = None):
        """Inicializa a ferramenta de busca Serper.

        Args:
            api_key: Chave de API opcional para Serper. Se não fornecida,
                procura pela variável de ambiente SERPER_API_KEY.

        Raises:
            ValueError: Se nenhuma chave de API for encontrada.
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")

        self.endpoint = "https://google.serper.dev/search"

    def _run(self, query: str, num_results: int = 10) -> str:
        """Realiza uma busca na web e retorna resultados formatados.

        Args:
            query: Consulta de busca.
            num_results: Número de resultados para retornar (padrão: 10).

        Returns:
            String formatada com os resultados da busca.
        """
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

        payload = {"q": query, "num": num_results}

        try:
            response = requests.post(
                self.endpoint, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Formatar resultados
            results = []

            # Resultados orgânicos
            if "organic" in data:
                for i, result in enumerate(data["organic"][:num_results], 1):
                    title = result.get("title", "No title")
                    link = result.get("link", "")
                    snippet = result.get("snippet", "")

                    results.append(f"{i}. {title}\n   {snippet}\n   URL: {link}")

            if not results:
                return "No results found."

            return "\n\n".join(results)

        except requests.exceptions.RequestException as e:
            return f"Error searching web: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"


class DuckDuckGoSearchTool(BaseTool):
    """Ferramenta de busca na web usando DuckDuckGo (não requer chave de API).

    Exemplo:
        tool = DuckDuckGoSearchTool()
        results = tool.run("Dicas de programação Python")
    """

    name = "duckduckgo_search"
    description = "Busca na web usando DuckDuckGo (não requer chave de API)"

    def _run(self, query: str, max_results: int = 5) -> str:
        """Realiza uma busca usando DuckDuckGo.

        Args:
            query: Consulta de busca.
            max_results: Número máximo de resultados para retornar (padrão: 5).

        Returns:
            String formatada com os resultados da busca.
        """
        try:
            # Tentar importar duckduckgo_search
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                return "Error: duckduckgo-search package not installed. Run: pip install duckduckgo-search"

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return "No results found."

            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                body = result.get("body", "")
                link = result.get("href", "")

                formatted.append(f"{i}. {title}\n   {body}\n   URL: {link}")

            return "\n\n".join(formatted)

        except Exception as e:
            return f"Error searching with DuckDuckGo: {str(e)}"
