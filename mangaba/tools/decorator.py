"""
Decorador @tool para Mangaba AI v3.0

Transforma uma função simples em uma instância BaseTool, inferindo automaticamente
nome, descrição (a partir do docstring) e args_schema (a partir de type hints).

Exemplo::

    @tool
    def search_web(query: str, max_results: int = 5) -> str:
        \"\"\"Busca informações atuais na web.\"\"\"
        ...

    @tool(name="calculator", description="Avalia expressões matemáticas")
    def calc(expression: str) -> str:
        ...
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, Optional, Type, get_type_hints

from pydantic import BaseModel, Field, create_model

from mangaba.tools.base import BaseTool


def tool(
    fn: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    return_direct: bool = False,
) -> Any:
    """Decorador que converte uma função em uma BaseTool.

    Infere automaticamente o nome da ferramenta, descrição (a partir do docstring)
    e esquema de argumentos (a partir de type hints e padrões).

    Pode ser usado com ou sem argumentos::

        @tool
        def my_tool(x: int) -> str: ...

        @tool(name="custom_name", description="Descrição personalizada")
        def my_tool(x: int) -> str: ...

    Args:
        fn: A função a converter. Se None, retorna um decorador.
        name: Nome personalizado opcional para a ferramenta. O padrão é o nome da função.
        description: Descrição personalizada opcional. O padrão é o docstring da função.
        return_direct: Se deve retornar a saída da ferramenta diretamente ao usuário.

    Returns:
        Uma função decoradora ou uma instância BaseTool.
    """

    def _wrap(func: Callable[..., Any]) -> BaseTool:
        tool_name = name or func.__name__
        tool_desc = description or (inspect.getdoc(func) or func.__name__)
        schema = _build_pydantic_model(func, tool_name)

        # Build a concrete BaseTool subclass dynamically
        cls_attrs: Dict[str, Any] = {
            "name": tool_name,
            "description": tool_desc,
            "args_schema": schema,
            "return_direct": return_direct,
            "_fn": staticmethod(func),
        }

        def _run_impl(self: Any, **kwargs: Any) -> Any:
            return self._fn(**kwargs)

        cls_attrs["_run"] = _run_impl

        tool_cls = type(
            f"Tool_{tool_name}",
            (BaseTool,),
            cls_attrs,
        )
        return tool_cls()

    if fn is not None:
        # @tool without parentheses
        return _wrap(fn)
    # @tool(...) with parentheses
    return _wrap


def _build_pydantic_model(func: Callable[..., Any], tool_name: str) -> Type[BaseModel]:
    """Cria um modelo Pydantic a partir da assinatura da função.

    Analisa a assinatura da função e type hints para construir um BaseModel
    Pydantic que representa o esquema de entrada da ferramenta.

    Args:
        func: A função a analisar.
        tool_name: Nome da ferramenta (usado para nomeação do modelo).

    Returns:
        Uma classe BaseModel Pydantic representando o esquema de entrada da função.
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    fields: Dict[str, Any] = {}

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        annotation = hints.get(param_name, str)
        if param.default is not inspect.Parameter.empty:
            fields[param_name] = (annotation, Field(default=param.default))
        else:
            fields[param_name] = (annotation, Field(...))

    model_name = f"{tool_name.title().replace('_', '')}Input"
    return create_model(model_name, **fields)
