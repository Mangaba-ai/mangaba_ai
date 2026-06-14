"""
Planejador de tarefas autônomo para Mangaba AI v3.0

Usa o LLM para decompor uma tarefa complexa em uma lista ordenada de
etapas executáveis.
"""

from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class PlanStep(BaseModel):
    """Uma única etapa em um plano de execução.

    Representa uma etapa acionável em um plano de tarefa decomposto,
    incluindo qual ferramenta usar (se houver) e resultados esperados.

    Attributes:
        step_number: A ordem sequencial desta etapa no plano.
        description: O que esta etapa deve realizar.
        tool: Nome da ferramenta opcional para usar nesta etapa.
        expected_result: Como a saída desta etapa deve parecer.
        dependencies: Lista de números de etapa dos quais esta etapa depende.
    """

    step_number: int
    description: str
    tool: Optional[str] = None
    expected_result: str = ""
    dependencies: List[int] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """Um plano ordenado produzido pelo TaskPlanner.

    Contém o objetivo geral e uma sequência de PlanSteps para alcançá-lo.

    Attributes:
        goal: A tarefa ou objetivo geral a realizar.
        steps: Lista ordenada de etapas para executar.
    """

    goal: str
    steps: List[PlanStep] = Field(default_factory=list)

    @property
    def total_steps(self) -> int:
        """Obtém o número total de etapas no plano.

        Returns:
            O número de etapas no plano.
        """
        return len(self.steps)


class TaskPlanner:
    """Decompõe uma tarefa complexa em uma sequência de PlanSteps usando um LLM.

    Usa o LLM para analisar uma tarefa e dividi-la em etapas
    concretas e sequenciais que podem ser executadas por agentes ou ferramentas.

    Example::

        planner = TaskPlanner(llm=llm_client)
        plan = planner.plan("Construir um relatório de mercado abrangente para Q4")
    """

    PLAN_PROMPT = (
        "You are a task planning assistant.\n"
        "Decompose the following task into concrete, sequential steps.\n"
        "If tools are available, indicate which tool to use for each step.\n\n"
        "Respond ONLY with a JSON array of objects with keys: "
        '"step_number", "description", "tool" (or null), "expected_result", "dependencies" (list of step numbers).\n\n'
        "Available tools: {tools}\n\n"
        "Task: {task}\n\n"
        "JSON plan:"
    )

    def __init__(self, llm: Any, tools: Optional[List[Any]] = None) -> None:
        """Inicializa o planejador de tarefas.

        Args:
            llm: Instância do cliente LLM para gerar planos.
            tools: Lista opcional de ferramentas disponíveis para o plano.
        """
        self.llm = llm
        self.tools = tools or []

    def plan(self, task: str) -> ExecutionPlan:
        """Gera um plano de execução para a tarefa fornecida.

        Args:
            task: A descrição da tarefa para decompor.

        Returns:
            Um ExecutionPlan contendo o objetivo e etapas ordenadas.

        Raises:
            ValueError: Se o plano não puder ser gerado ou analisado.
        """
        tools_str = ", ".join(t.name for t in self.tools) if self.tools else "none"
        prompt = self.PLAN_PROMPT.format(tools=tools_str, task=task)
        raw = self.llm.generate_text(prompt)

        steps = self._parse_steps(raw)
        return ExecutionPlan(goal=task, steps=steps)

    @staticmethod
    def _parse_steps(raw: str) -> List[PlanStep]:
        """Analisa a resposta do LLM em objetos PlanStep.

        Args:
            raw: A resposta de texto bruto do LLM.

        Returns:
            Lista de objetos PlanStep analisados da resposta.

        Raises:
            ValueError: Se o JSON não puder ser analisado.
        """
        # Try to find a JSON array in the response
        try:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            data = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            # Fallback: single step
            return [
                PlanStep(step_number=1, description=raw.strip(), expected_result="")
            ]

        steps = []
        for item in data:
            if isinstance(item, dict):
                steps.append(
                    PlanStep(
                        step_number=item.get("step_number", len(steps) + 1),
                        description=item.get("description", ""),
                        tool=item.get("tool"),
                        expected_result=item.get("expected_result", ""),
                        dependencies=item.get("dependencies", []),
                    )
                )
        return steps
