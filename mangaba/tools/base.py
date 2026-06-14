"""
Sistema de ferramentas para Mangaba AI v3.0

Abstração profissional de ferramentas com validação de entrada baseada em Pydantic,
geração automática de esquema JSON para chamada de função LLM e
suporte para execução síncrona e assíncrona.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from mangaba.core.events import EventBus, Event, EventType


class EmptyInput(BaseModel):
    """Esquema de entrada padrão quando uma ferramenta não aceita entrada estruturada."""

    pass


class BaseTool(ABC):
    """Classe base para todas as ferramentas Mangaba.

    Fornece uma abstração profissional de ferramentas com validação de entrada
    baseada em Pydantic, geração automática de esquema JSON para chamada de
    função LLM e suporte para execução síncrona e assíncrona.

    As subclasses devem:
        - Definir ``name`` e ``description`` como atributos de classe
        - Opcionalmente definir ``args_schema`` para um modelo Pydantic descrevendo entradas
        - Implementar ``_run(**kwargs)``

    Exemplo::

        class SearchTool(BaseTool):
            name = "web_search"
            description = "Busca informações atuais na web"
            args_schema = SearchInput  # modelo Pydantic

            def _run(self, query: str, max_results: int = 5) -> str:
                ...

    Atributos:
        name: O identificador de nome da ferramenta.
        description: Descrição do que a ferramenta faz.
        args_schema: Modelo Pydantic opcional para validação de entrada.
        return_direct: Se deve retornar a saída diretamente ao usuário.
    """

    name: str = "base_tool"
    description: str = "Base tool"
    args_schema: Optional[Type[BaseModel]] = None
    return_direct: bool = False

    # -- public API ----------------------------------------------------------

    def run(self, **kwargs: Any) -> Any:
        """Valida entradas e executa a ferramenta.

        Args:
            **kwargs: Argumentos de entrada para a ferramenta.

        Returns:
            O resultado da execução da ferramenta.

        Raises:
            Exception: Se a execução da ferramenta falhar.
        """
        validated = self._validate_input(kwargs)
        EventBus.emit(
            Event(
                event_type=EventType.TOOL_START,
                data={
                    "tool": self.name,
                    "args": {k: str(v)[:200] for k, v in validated.items()},
                },
            )
        )
        try:
            result = self._run(**validated)
            EventBus.emit(
                Event(
                    event_type=EventType.TOOL_END,
                    data={"tool": self.name, "result_preview": str(result)[:200]},
                )
            )
            return result
        except Exception as exc:
            EventBus.emit(
                Event(
                    event_type=EventType.TOOL_ERROR,
                    data={"tool": self.name, "error": str(exc)},
                )
            )
            raise

    @abstractmethod
    def _run(self, **kwargs: Any) -> Any:
        """Implementação específica da ferramenta. Substituir nas subclasses.

        Args:
            **kwargs: Argumentos de entrada validados.

        Returns:
            O resultado da ferramenta.

        Raises:
            NotImplementedError: Se não implementado pela subclasse.
        """
        ...

    # -- schema / function calling helpers -----------------------------------

    def get_function_schema(self) -> Dict[str, Any]:
        """Retorna uma representação JSON-schema para chamada de função LLM.

        Returns:
            Dicionário contendo o nome da função, descrição e esquema de parâmetros.
        """
        if self.args_schema is not None:
            params = self.args_schema.model_json_schema()
            # Remover o título para manter conciso
            params.pop("title", None)
        else:
            # Detectar automaticamente da assinatura _run
            params = self._schema_from_signature()
        return {
            "name": self.name,
            "description": self.description,
            "parameters": params,
        }

    # -- internal ------------------------------------------------------------

    def _validate_input(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Valida kwargs contra args_schema se definido.

        Args:
            kwargs: Argumentos de entrada brutos.

        Returns:
            Argumentos validados e potencialmente transformados.
        """
        if self.args_schema is not None:
            validated = self.args_schema(**kwargs)
            return validated.model_dump()
        return kwargs

    def _schema_from_signature(self) -> Dict[str, Any]:
        """Infere um esquema JSON a partir da assinatura do método ``_run``.

        Returns:
            Dicionário JSON Schema representando os parâmetros da função.
        """
        sig = inspect.signature(self._run)
        properties: Dict[str, Any] = {}
        required = []

        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "kwargs", "args"):
                continue
            annotation = param.annotation
            json_type = (
                type_map.get(annotation, "string")
                if annotation != inspect.Parameter.empty
                else "string"
            )
            prop: Dict[str, Any] = {"type": json_type}
            if param.default is not inspect.Parameter.empty:
                prop["default"] = param.default
            else:
                required.append(param_name)
            properties[param_name] = prop

        schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    def __repr__(self) -> str:
        """Retorna a representação em string da ferramenta.

        Returns:
            Representação em string mostrando o nome da classe e o nome da ferramenta.
        """
        return f"{self.__class__.__name__}(name='{self.name}')"
