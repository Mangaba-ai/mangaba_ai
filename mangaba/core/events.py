"""
Sistema de eventos e infraestrutura de callback para Mangaba AI v3.0

Fornece um EventBus que desacopla produtores (agentes, tarefas, crews) de
consumidores (loggers, tracers, UI), e uma ABC BaseCallback para construir
manipuladores personalizados.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos de eventos
# ---------------------------------------------------------------------------


class EventType(str, Enum):
    # Agente
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"

    # LLM
    LLM_START = "llm_start"
    LLM_END = "llm_end"
    LLM_ERROR = "llm_error"
    LLM_RETRY = "llm_retry"
    LLM_STREAM_CHUNK = "llm_stream_chunk"

    # Ferramentas
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_ERROR = "tool_error"

    # ReAct
    REACT_STEP = "react_step"
    REACT_THOUGHT = "react_thought"
    REACT_ACTION = "react_action"
    REACT_OBSERVATION = "react_observation"

    # Task
    TASK_START = "task_start"
    TASK_END = "task_end"
    TASK_ERROR = "task_error"

    # Crew
    CREW_START = "crew_start"
    CREW_END = "crew_end"
    CREW_ERROR = "crew_error"

    # Memory
    MEMORY_ADD = "memory_add"
    MEMORY_SEARCH = "memory_search"

    # Guardrails
    GUARDRAIL_PASS = "guardrail_pass"
    GUARDRAIL_FAIL = "guardrail_fail"

    # Genérico
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Modelo de evento
# ---------------------------------------------------------------------------


class Event(BaseModel):
    """Evento imutável emitido pelos componentes do framework."""

    event_type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    source_id: str = ""
    source_type: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    parent_event_id: Optional[str] = None
    trace_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Classe base abstrata de Callback
# ---------------------------------------------------------------------------


class BaseCallback(ABC):
    """Base abstrata para manipuladores de eventos."""

    event_filter: Optional[Set[EventType]] = None

    def should_handle(self, event: Event) -> bool:
        if self.event_filter is None:
            return True
        return event.event_type in self.event_filter

    @abstractmethod
    def on_event(self, event: Event) -> None:
        raise NotImplementedError("on_event() must be implemented")


# ---------------------------------------------------------------------------
# Gerenciador de callbacks
# ---------------------------------------------------------------------------


class CallbackManager:
    """Gerencia uma coleção de callbacks e despacha eventos para eles."""

    def __init__(self, callbacks: Optional[List[BaseCallback]] = None) -> None:
        self._callbacks: List[BaseCallback] = list(callbacks or [])

    def add(self, callback: BaseCallback) -> None:
        self._callbacks.append(callback)

    def remove(self, callback: BaseCallback) -> None:
        self._callbacks = [cb for cb in self._callbacks if cb is not callback]

    def emit(self, event: Event) -> None:
        for cb in self._callbacks:
            try:
                if cb.should_handle(event):
                    cb.on_event(event)
            except Exception:
                logger.exception(
                    "Callback %s raised an error for event %s",
                    type(cb).__name__,
                    event.event_type,
                )

    @property
    def callbacks(self) -> List[BaseCallback]:
        return list(self._callbacks)


# ---------------------------------------------------------------------------
# Global EventBus singleton
# ---------------------------------------------------------------------------


class EventBus:
    """Singleton EventBus em todo o processo.

    Componentes podem publicar eventos via ``EventBus.emit(event)`` e registrar
    manipuladores via ``EventBus.register(callback_or_fn, event_types)``.
    """

    _manager = CallbackManager()

    @classmethod
    def register(
        cls,
        handler: BaseCallback | Callable[[Event], None],
        event_types: Optional[Set[EventType]] = None,
    ) -> None:
        if isinstance(handler, BaseCallback):
            cls._manager.add(handler)
        else:
            cls._manager.add(_FunctionCallback(handler, event_types))

    @classmethod
    def unregister(cls, handler: BaseCallback) -> None:
        cls._manager.remove(handler)

    @classmethod
    def emit(cls, event: Event) -> None:
        cls._manager.emit(event)

    @classmethod
    def reset(cls) -> None:
        cls._manager = CallbackManager()

    @classmethod
    def manager(cls) -> CallbackManager:
        return cls._manager


class _FunctionCallback(BaseCallback):
    """Envolve uma função simples como um BaseCallback."""

    def __init__(
        self, fn: Callable[[Event], None], event_filter: Optional[Set[EventType]] = None
    ) -> None:
        self._fn = fn
        self.event_filter = event_filter

    def on_event(self, event: Event) -> None:
        self._fn(event)
