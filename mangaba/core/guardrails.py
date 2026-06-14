"""
Guardrails para validação de entrada/saída em Mangaba AI v3.0
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List, Optional, Type

from pydantic import BaseModel

from mangaba.core.events import EventBus, Event, EventType


class BaseGuardrail(ABC):
    """Guardrail abstrato que valida e opcionalmente transforma texto.

    Guardrails são regras de validação que podem ser aplicadas a entradas
    ou saídas de agentes para garantir que atendam a certos critérios (comprimento,
    filtros de conteúdo, validação de esquema, etc.).

    Subclasses devem implementar o método validate().
    """

    @abstractmethod
    def validate(self, text: str) -> str:
        """Valida texto e opcionalmente o transforma.

        Args:
            text: O texto a ser validado.

        Returns:
            O texto validado (e possivelmente modificado).

        Raises:
            ValueError: Se o texto falhar na validação.
            NotImplementedError: Se não implementado pela subclasse.
        """
        raise NotImplementedError("validate() must be implemented")


class LengthGuardrail(BaseGuardrail):
    """Garante que o comprimento da saída esteja dentro dos limites.

    Valida que o comprimento do texto esteja entre min_length e max_length.
    Se o texto for muito longo, é truncado para max_length.
    """

    def __init__(self, min_length: int = 0, max_length: int = 50_000) -> None:
        """Inicializa o guardrail de comprimento.

        Args:
            min_length: Comprimento mínimo permitido (padrão 0).
            max_length: Comprimento máximo permitido (padrão 50.000).
        """
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, text: str) -> str:
        """Valida o comprimento do texto e trunca se muito longo.

        Args:
            text: O texto a ser validado.

        Returns:
            O texto validado, truncado se muito longo.

        Raises:
            ValueError: Se o texto for mais curto que min_length.
        """
        if len(text) < self.min_length:
            EventBus.emit(
                Event(
                    event_type=EventType.GUARDRAIL_FAIL,
                    data={"guardrail": "length", "reason": "too_short"},
                )
            )
            raise ValueError(f"Output too short ({len(text)} < {self.min_length})")
        if len(text) > self.max_length:
            EventBus.emit(
                Event(
                    event_type=EventType.GUARDRAIL_FAIL,
                    data={"guardrail": "length", "reason": "too_long"},
                )
            )
            text = text[: self.max_length]
        EventBus.emit(
            Event(event_type=EventType.GUARDRAIL_PASS, data={"guardrail": "length"})
        )
        return text


class ContentFilterGuardrail(BaseGuardrail):
    """Bloqueia saída contendo padrões específicos.

    Examina o texto em busca de padrões regex (ex: senhas, chaves de API) e
    redige qualquer correspondência com [REDACTED].
    """

    def __init__(self, blocked_patterns: Optional[List[str]] = None) -> None:
        """Inicializa o guardrail de filtro de conteúdo.

        Args:
            blocked_patterns: Lista opcional de padrões regex para bloquear.
                Padrão para padrões sensíveis comuns (senhas, chaves de API).
        """
        defaults = [
            r"\b(?:password|secret|api[_-]?key)\s*[:=]\s*\S+",
        ]
        self.patterns = [
            re.compile(p, re.IGNORECASE) for p in (blocked_patterns or defaults)
        ]

    def validate(self, text: str) -> str:
        """Valida texto e redige qualquer padrão bloqueado.

        Args:
            text: O texto a ser validado.

        Returns:
            O texto com quaisquer padrões bloqueados redigidos.
        """
        for pattern in self.patterns:
            if pattern.search(text):
                EventBus.emit(
                    Event(
                        event_type=EventType.GUARDRAIL_FAIL,
                        data={"guardrail": "content_filter"},
                    )
                )
                # Redigir correspondências
                text = pattern.sub("[REDACTED]", text)
        EventBus.emit(
            Event(
                event_type=EventType.GUARDRAIL_PASS,
                data={"guardrail": "content_filter"},
            )
        )
        return text


class SchemaGuardrail(BaseGuardrail):
    """Valida que a saída pode ser analisada em um modelo Pydantic.

    Extrai JSON do texto e valida contra o esquema Pydantic fornecido,
    levantando um erro se a validação falhar.
    """

    def __init__(self, schema: Type[BaseModel]) -> None:
        """Inicializa o guardrail de esquema.

        Args:
            schema: A classe de modelo Pydantic para validar contra.
        """
        self.schema = schema

    def validate(self, text: str) -> str:
        """Valida que o texto pode ser analisado no esquema Pydantic.

        Args:
            text: O texto a ser validado.

        Returns:
            O texto original se a validação tiver sucesso.

        Raises:
            ValueError: Se o texto não puder ser analisado ou não corresponder ao esquema.
        """
        import json as _json

        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = _json.loads(text[start:end])
            self.schema(**data)
            EventBus.emit(
                Event(event_type=EventType.GUARDRAIL_PASS, data={"guardrail": "schema"})
            )
            return text
        except Exception as exc:
            EventBus.emit(
                Event(
                    event_type=EventType.GUARDRAIL_FAIL,
                    data={"guardrail": "schema", "error": str(exc)},
                )
            )
            raise ValueError(
                f"Output does not match schema {self.schema.__name__}: {exc}"
            ) from exc


class GuardrailChain(BaseGuardrail):
    """Compõe múltiplos guardrails sequencialmente.

    Aplica uma cadeia de guardrails em ordem, passando a saída de cada
    como entrada para o próximo. Útil para combinar múltiplas regras de validação.
    """

    def __init__(self, guardrails: List[BaseGuardrail]) -> None:
        """Inicializa a cadeia de guardrails.

        Args:
            guardrails: Lista de guardrails para aplicar em sequência.
        """
        self.guardrails = guardrails

    def validate(self, text: str) -> str:
        """Aplica todos os guardrails em sequência.

        Args:
            text: O texto a ser validado.

        Returns:
            O texto após passar por todos os guardrails.

        Raises:
            ValueError: Se qualquer guardrails na cadeia falhar na validação.
        """
        for g in self.guardrails:
            text = g.validate(text)
        return text
