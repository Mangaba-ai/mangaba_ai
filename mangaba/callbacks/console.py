"""Callback de console — imprime eventos de agente/tarefa/ferramenta no stdout."""

from __future__ import annotations

import logging
from mangaba.core.events import BaseCallback, Event, EventType

log = logging.getLogger(__name__)

_ICONS = {
    EventType.AGENT_START: "▶",
    EventType.AGENT_END: "✔",
    EventType.AGENT_ERROR: "✖",
    EventType.TASK_START: "📋",
    EventType.TASK_END: "📋",
    EventType.TOOL_START: "🔧",
    EventType.TOOL_END: "🔧",
    EventType.TOOL_ERROR: "🔧✖",
    EventType.LLM_START: "🤖",
    EventType.LLM_END: "🤖",
    EventType.REACT_THOUGHT: "💭",
    EventType.REACT_ACTION: "⚡",
    EventType.REACT_OBSERVATION: "👁",
    EventType.CREW_START: "🚀",
    EventType.CREW_END: "🏁",
}


class ConsoleCallback(BaseCallback):
    """Manipulador de callback que imprime eventos de agente/tarefa/ferramenta no console.

    Este callback fornece visibilidade em tempo real do fluxo de execução
    registrando eventos com ícones e formatação apropriados.

    Attributes:
        level: O nível de logging a ser usado para saída (padrão: INFO).
    """

    def __init__(self, level: int = logging.INFO) -> None:
        """Inicializa o ConsoleCallback.

        Args:
            level: O nível de logging a ser usado para saída (padrão: INFO).
        """
        super().__init__()
        self.level = level

    def on_event(self, event: Event) -> None:
        """Manipula um evento registrando-o no console.

        Args:
            event: O evento a ser registrado.
        """
        icon = _ICONS.get(event.event_type, "•")
        msg = f"{icon} [{event.event_type.value}]"
        if event.source_id:
            msg += f" ({event.source_id})"
        if event.data:
            summary = ", ".join(f"{k}={v!r}" for k, v in list(event.data.items())[:4])
            msg += f" {summary}"
        log.log(self.level, msg)
