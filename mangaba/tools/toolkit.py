"""
Agrupamento de Toolkit para Mangaba AI v3.0

Um Toolkit agrupa ferramentas relacionadas para que possam ser anexadas a um
agente como uma única unidade.

Exemplo::

    kit = FileToolkit()
    agent = Agent(role="...", tools=kit.get_tools(), ...)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from mangaba.tools.base import BaseTool
from mangaba.tools.file_tools import FileReaderTool, FileWriterTool, DirectoryListTool
from mangaba.tools.web_search import DuckDuckGoSearchTool


class BaseToolkit(ABC):
    """Classe base abstrata para agrupar ferramentas relacionadas.

    Um Toolkit agrupa ferramentas relacionadas para que possam ser anexadas
    a um agente como uma única unidade.
    """

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """Retorna a lista de ferramentas neste toolkit.

        Returns:
            Lista de instâncias BaseTool.
        """


class FileToolkit(BaseToolkit):
    """Toolkit contendo ferramentas de E/S de arquivos.

    Inclui ferramentas para ler arquivos, escrever arquivos e listar diretórios.
    """

    def get_tools(self) -> List[BaseTool]:
        """Retorna a lista de ferramentas de E/S de arquivos.

        Returns:
            Lista contendo FileReaderTool, FileWriterTool e DirectoryListTool.
        """
        return [FileReaderTool(), FileWriterTool(), DirectoryListTool()]


class WebToolkit(BaseToolkit):
    """Toolkit contendo ferramentas de busca na web.

    Inclui ferramentas para buscar na web usando DuckDuckGo.
    """

    def get_tools(self) -> List[BaseTool]:
        """Retorna a lista de ferramentas de busca na web.

        Returns:
            Lista contendo DuckDuckGoSearchTool.
        """
        return [DuckDuckGoSearchTool()]
