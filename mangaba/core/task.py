"""
Task v3.0 — unidade de fluxo de trabalho estruturada com guardrails e análise de saída.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from mangaba.core.events import EventBus, Event, EventType
from mangaba.core.exceptions import TaskError

if TYPE_CHECKING:
    from mangaba.core.agent import Agent
    from mangaba.tools.base import BaseTool
    from mangaba.core.guardrails import BaseGuardrail
    from mangaba.core.output_parsers import BaseOutputParser

log = logging.getLogger(__name__)


class TaskOutput:
    """Resultado de uma execução de tarefa."""

    def __init__(
        self,
        description: str,
        result: str,
        agent: str,
        success: bool = True,
    ) -> None:
        self.description = description
        self.result = result
        self.agent = agent
        self.success = success
        from datetime import datetime

        self.timestamp = datetime.now().isoformat()

    def __str__(self) -> str:
        return self.result


class Task:
    """Uma tarefa estruturada atribuída a um Agente.

    Example::

        task = Task(
            description="Pesquisar {topic} para nosso relatório",
            expected_output="Um relatório detalhado com 10 principais descobertas",
            agent=researcher,
            context=[previous_task],
            output_file="report.md",
        )
    """

    def __init__(
        self,
        description: str,
        expected_output: str,
        agent: Optional[Agent] = None,
        context: Optional[List[Task]] = None,
        tools: Optional[List[BaseTool]] = None,
        output_file: Optional[str] = None,
        callback: Optional[Callable] = None,
        async_execution: bool = False,
        human_input: bool = False,
        guardrails: Optional[List[BaseGuardrail]] = None,
        output_parser: Optional[BaseOutputParser] = None,
        retry_on_failure: int = 0,
        task_id: Optional[str] = None,
    ) -> None:
        if not description or not description.strip():
            raise ValueError("Task description cannot be empty")
        if not expected_output or not expected_output.strip():
            raise ValueError("Expected output cannot be empty")

        self.task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        self.description = description.strip()
        self.expected_output = expected_output.strip()
        self.agent = agent
        self.context: List[Task] = context or []
        self.tools: List[BaseTool] = tools or []
        self.output_file = output_file
        self.callback = callback
        self.async_execution = async_execution
        self.human_input = human_input
        self.guardrails: List[BaseGuardrail] = guardrails or []
        self.output_parser = output_parser
        self.retry_on_failure = retry_on_failure

        # Runtime state
        self.status = "pending"
        self.output: Optional[TaskOutput] = None
        self.error: Optional[str] = None

    # ── sync execution ─────────────────────────────────────────────────

    def execute(self, inputs: Optional[Dict[str, Any]] = None) -> TaskOutput:
        """Executa a tarefa de forma síncrona."""
        if not self.agent:
            raise TaskError("No agent assigned to this task")

        self.status = "running"
        EventBus.emit(
            Event(
                event_type=EventType.TASK_START,
                source_id=self.task_id,
                data={"description": self.description[:200], "agent": self.agent.role},
            )
        )

        attempts = max(1, self.retry_on_failure + 1)
        last_err: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                task_desc = self._process_template(self.description, inputs or {})
                context_str = self._build_context()

                # Build full prompt with expected output
                full_desc = f"{task_desc}\n\nExpected output: {self.expected_output}"

                result = self.agent.execute_task(full_desc, context_str or None)

                # Guardrails
                for g in self.guardrails:
                    result = g.validate(result)

                # Output parser
                if self.output_parser:
                    result = str(self.output_parser.parse(result))

                self.output = TaskOutput(
                    description=task_desc,
                    result=result,
                    agent=self.agent.role,
                    success=True,
                )

                if self.output_file:
                    self._save_to_file(result)
                if self.callback:
                    self.callback(self.output)

                self.status = "completed"
                EventBus.emit(
                    Event(
                        event_type=EventType.TASK_END,
                        source_id=self.task_id,
                        data={"status": "completed"},
                    )
                )
                return self.output

            except Exception as exc:
                last_err = exc
                if attempt < attempts:
                    log.warning("Task retry %d/%d: %s", attempt, attempts, exc)
                    continue

        self.status = "failed"
        self.error = str(last_err)
        self.output = TaskOutput(
            description=self.description,
            result=f"Error: {last_err}",
            agent=self.agent.role if self.agent else "unknown",
            success=False,
        )
        EventBus.emit(
            Event(
                event_type=EventType.TASK_ERROR,
                source_id=self.task_id,
                data={"error": str(last_err)},
            )
        )
        raise TaskError(f"Task failed: {last_err}", cause=last_err)

    # ── async execution ────────────────────────────────────────────────

    async def aexecute(self, inputs: Optional[Dict[str, Any]] = None) -> TaskOutput:
        """Executa a tarefa de forma assíncrona (executa em um executor de thread)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, inputs)

    # ── helpers ────────────────────────────────────────────────────────

    def _process_template(self, text: str, inputs: Dict[str, Any]) -> str:
        result = text
        for key, value in inputs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def _build_context(self) -> str:
        if not self.context:
            return ""
        parts = []
        for task in self.context:
            if task.output:
                parts.append(f"Previous task: {task.description}")
                parts.append(f"Result: {task.output.result}")
                parts.append("---")
        return "\n".join(parts)

    def _save_to_file(self, content: str) -> None:
        try:
            import os

            directory = os.path.dirname(self.output_file)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as exc:
            log.error("Failed to save task output: %s", exc)

    def __repr__(self) -> str:
        agent_name = self.agent.role if self.agent else "unassigned"
        return f"Task(desc='{self.description[:40]}...', agent='{agent_name}', status='{self.status}')"
