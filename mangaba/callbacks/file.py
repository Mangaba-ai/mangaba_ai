"""Callback de arquivo — persiste eventos como JSONL."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mangaba.core.events import BaseCallback, Event

log = logging.getLogger(__name__)


class FileCallback(BaseCallback):
    """Manipulador de callback que persiste eventos em um arquivo de log JSONL.

    Este callback escreve cada evento como uma linha JSON em um arquivo de log
    para armazenamento persistente e análise posterior.

    Attributes:
        path: O caminho do arquivo onde os eventos serão escritos.
    """

    def __init__(self, path: str | Path = "mangaba_events.jsonl") -> None:
        """Inicializa o FileCallback.

        Args:
            path: O caminho do arquivo onde os eventos serão escritos
                (padrão: "mangaba_events.jsonl").
        """
        super().__init__()
        self.path = Path(path)

    def on_event(self, event: Event) -> None:
        """Manipula um evento anexando-o ao arquivo de log.

        Args:
            event: O evento a ser registrado.
        """
        record = {
            "event_type": event.event_type.value,
            "source_id": event.source_id,
            "source_type": event.source_type,
            "timestamp": event.timestamp,
            "data": event.data,
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except OSError:
            log.warning("FileCallback: could not write to %s", self.path)
