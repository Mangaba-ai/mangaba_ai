"""Ferramentas para agentes Mangaba AI v3.0.

Este módulo fornece o sistema de ferramentas para agentes, incluindo:
- BaseTool: Classe base abstrata para criar ferramentas personalizadas
- @tool decorator: Converte funções em ferramentas automaticamente
- BaseToolkit: Coleção de ferramentas relacionadas
- Built-in tools: Calculadora, processamento de texto, E/S de arquivos, busca na web

Exemplo::

    from mangaba.tools import tool

    @tool
    def my_function(x: int) -> str:
        \"\"\"Faz algo com x.\"\"\"
        return str(x)
"""

from mangaba.tools.base import BaseTool
from mangaba.tools.decorator import tool
from mangaba.tools.toolkit import BaseToolkit, FileToolkit, WebToolkit
from mangaba.tools.math_tools import CalculatorTool
from mangaba.tools.text_tools import TextSplitterTool, WordCounterTool

__all__ = [
    "BaseTool",
    "tool",
    "BaseToolkit",
    "FileToolkit",
    "WebToolkit",
    "CalculatorTool",
    "TextSplitterTool",
    "WordCounterTool",
]
