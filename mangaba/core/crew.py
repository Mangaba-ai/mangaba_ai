"""
Crew v3.0 — orquestração multi-agente com todos os tipos de processo.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from mangaba.core.agent import Agent
from mangaba.core.task import Task, TaskOutput
from mangaba.core.events import EventBus, Event, EventType
from mangaba.core.exceptions import CrewError

log = logging.getLogger(__name__)


class Process(Enum):
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
    PARALLEL = "parallel"
    CONSENSUAL = "consensual"


class CrewOutput:
    """Resultado de uma execução de crew, incluindo métricas."""

    def __init__(
        self,
        tasks_outputs: List[TaskOutput],
        process: Process,
        duration: float,
        crew_id: str,
    ) -> None:
        self.tasks_outputs = tasks_outputs
        self.process = process
        self.duration = duration
        self.crew_id = crew_id
        from datetime import datetime

        self.timestamp = datetime.now().isoformat()

    @property
    def final_output(self) -> str:
        if self.tasks_outputs:
            return self.tasks_outputs[-1].result
        return ""

    def __str__(self) -> str:
        return self.final_output


class Crew:
    """Orquestra múltiplos agentes trabalhando em múltiplas tarefas.

    Example::

        crew = Crew(
            agents=[researcher, analyst, writer],
            tasks=[research_task, analyze_task, write_task],
            process=Process.SEQUENTIAL,
            verbose=True,
        )
        result = crew.kickoff(inputs={"topic": "AI trends"})
    """

    def __init__(
        self,
        agents: List[Agent],
        tasks: List[Task],
        process: Process = Process.SEQUENTIAL,
        verbose: bool = False,
        max_rpm: Optional[int] = None,
        memory: Optional[Any] = None,
        crew_id: Optional[str] = None,
    ) -> None:
        if not agents:
            raise CrewError("Crew must have at least one agent")
        if not tasks:
            raise CrewError("Crew must have at least one task")

        self.crew_id = crew_id or f"crew_{uuid.uuid4().hex[:8]}"
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose
        self.max_rpm = max_rpm
        self.memory = memory

        self._validate_setup()
        self._connect_agents()

        if self.verbose:
            log.info(
                "Crew %s: %d agents, %d tasks, process=%s",
                self.crew_id,
                len(agents),
                len(tasks),
                process.value,
            )

    # ── public API ─────────────────────────────────────────────────────

    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> CrewOutput:
        """Inicia a execução da crew."""
        start = time.monotonic()

        EventBus.emit(
            Event(
                event_type=EventType.CREW_START,
                source_id=self.crew_id,
                data={
                    "process": self.process.value,
                    "agents": len(self.agents),
                    "tasks": len(self.tasks),
                },
            )
        )

        try:
            if self.process == Process.SEQUENTIAL:
                outputs = self._run_sequential(inputs or {})
            elif self.process == Process.HIERARCHICAL:
                outputs = self._run_hierarchical(inputs or {})
            elif self.process == Process.PARALLEL:
                outputs = self._run_parallel(inputs or {})
            elif self.process == Process.CONSENSUAL:
                outputs = self._run_consensual(inputs or {})
            else:
                raise CrewError(f"Unknown process: {self.process}")

            duration = time.monotonic() - start
            result = CrewOutput(
                tasks_outputs=outputs,
                process=self.process,
                duration=duration,
                crew_id=self.crew_id,
            )

            EventBus.emit(
                Event(
                    event_type=EventType.CREW_END,
                    source_id=self.crew_id,
                    data={"duration": duration, "tasks_completed": len(outputs)},
                )
            )
            return result

        except Exception as exc:
            EventBus.emit(
                Event(
                    event_type=EventType.CREW_ERROR,
                    source_id=self.crew_id,
                    data={"error": str(exc)},
                )
            )
            raise

    # ── process implementations ────────────────────────────────────────

    def _run_sequential(self, inputs: Dict[str, Any]) -> List[TaskOutput]:
        outputs: List[TaskOutput] = []
        for i, task in enumerate(self.tasks, 1):
            if self.verbose:
                log.info(
                    "[%d/%d] %s → %s",
                    i,
                    len(self.tasks),
                    task.agent.role,
                    task.description[:60],
                )
            output = task.execute(inputs)
            outputs.append(output)
        return outputs

    def _run_hierarchical(self, inputs: Dict[str, Any]) -> List[TaskOutput]:
        if len(self.agents) < 2:
            raise CrewError(
                "Hierarchical process needs >= 2 agents (1 manager + workers)"
            )

        manager = self.agents[0]
        outputs: List[TaskOutput] = []

        for i, task in enumerate(self.tasks, 1):
            if self.verbose:
                log.info(
                    "[%d/%d] Manager %s delegates to %s",
                    i,
                    len(self.tasks),
                    manager.role,
                    task.agent.role,
                )

            # Gerente refina instruções
            delegation_prompt = (
                f"You are the manager. Refine these instructions for your worker.\n"
                f"Worker role: {task.agent.role}\n"
                f"Task: {task.description}\nExpected output: {task.expected_output}\n"
                f"Provide clear, actionable instructions."
            )
            refined = manager.execute_task(delegation_prompt)

            # Worker executa com instruções refinadas
            original_desc = task.description
            task.description = f"{refined}\n\nOriginal task: {original_desc}"
            try:
                output = task.execute(inputs)
            finally:
                task.description = original_desc

            # Gerente revisa
            review_prompt = (
                f"Review this worker output.\nTask: {original_desc}\n"
                f"Output: {output.result[:2000]}\n"
                f"Provide approval or revision notes."
            )
            manager.execute_task(review_prompt)

            outputs.append(output)
        return outputs

    def _run_parallel(self, inputs: Dict[str, Any]) -> List[TaskOutput]:
        """Executa tarefas independentes concorrentemente usando asyncio."""

        async def _run() -> List[TaskOutput]:
            coros = [task.aexecute(inputs) for task in self.tasks]
            return list(await asyncio.gather(*coros))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Já em um event loop — voltar para execução sequencial
            return self._run_sequential(inputs)

        return asyncio.run(_run())

    def _run_consensual(self, inputs: Dict[str, Any]) -> List[TaskOutput]:
        """Todos os agentes executam independentemente cada tarefa; resultados são mesclados."""
        outputs: List[TaskOutput] = []

        for task in self.tasks:
            agent_results: List[str] = []
            for agent in self.agents:
                original_agent = task.agent
                task.agent = agent
                try:
                    out = task.execute(inputs)
                    agent_results.append(f"[{agent.role}]: {out.result}")
                finally:
                    task.agent = original_agent

            # Usar primeiro agente para sintetizar consenso
            synthesis_prompt = (
                "Multiple experts provided their analysis. Synthesise a consensus.\n\n"
                + "\n---\n".join(agent_results)
            )
            consensus = self.agents[0].execute_task(synthesis_prompt)
            outputs.append(
                TaskOutput(
                    description=task.description,
                    result=consensus,
                    agent="consensus",
                    success=True,
                )
            )
        return outputs

    # ── internal ───────────────────────────────────────────────────────

    def _validate_setup(self) -> None:
        for task in self.tasks:
            if not task.agent:
                raise CrewError(
                    f"Task '{task.description[:50]}...' has no agent assigned"
                )
            if task.agent not in self.agents:
                raise CrewError(
                    f"Task agent '{task.agent.role}' not in crew's agent list"
                )
            for dep in task.context:
                if dep not in self.tasks:
                    raise CrewError(
                        "Task has a dependency on a task that is not in this crew"
                    )

    def _connect_agents(self) -> None:
        for i, a1 in enumerate(self.agents):
            for a2 in self.agents[i + 1 :]:
                a1.connect_to(a2)

    def __repr__(self) -> str:
        return f"Crew(agents={len(self.agents)}, tasks={len(self.tasks)}, process={self.process.value})"
