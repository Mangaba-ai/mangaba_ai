"""
Motor de fluxo de trabalho — compõe tarefas em pipelines, ramificações condicionais e estágios paralelos.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from mangaba.core.task import Task, TaskOutput
from mangaba.core.events import EventBus, Event, EventType

log = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Saída produzida por um estágio de pipeline.

    Attributes:
        stage_name: Nome do estágio que produziu este resultado.
        outputs: Lista de saídas de tarefas do estágio.
        duration: Tempo para executar o estágio em segundos.
    """

    stage_name: str
    outputs: List[TaskOutput]
    duration: float = 0.0


class Stage:
    """Um grupo nomeado de tarefas dentro de um pipeline.

    Executa tarefas sequencialmente na ordem em que são fornecidas.
    """

    def __init__(self, name: str, tasks: List[Task]) -> None:
        """Inicializa o estágio.

        Args:
            name: Nome do estágio.
            tasks: Lista de tarefas para executar neste estágio.
        """
        self.name = name
        self.tasks = tasks

    def run(self, inputs: Dict[str, Any]) -> StageResult:
        """Executa todas as tarefas neste estágio sequencialmente.

        Args:
            inputs: Dados de entrada para passar a cada tarefa.

        Returns:
            StageResult contendo saídas de todas as tarefas.
        """
        start = time.monotonic()
        outputs = [t.execute(inputs) for t in self.tasks]
        return StageResult(
            stage_name=self.name, outputs=outputs, duration=time.monotonic() - start
        )


class ParallelStage(Stage):
    """Executa tarefas simultaneamente.

    Executa todas as tarefas em paralelo usando asyncio para melhor desempenho
    quando as tarefas são independentes.
    """

    def run(self, inputs: Dict[str, Any]) -> StageResult:
        """Executa todas as tarefas neste estágio simultaneamente.

        Args:
            inputs: Dados de entrada para passar a cada tarefa.

        Returns:
            StageResult contendo saídas de todas as tarefas.
        """
        start = time.monotonic()

        async def _go():
            return list(await asyncio.gather(*(t.aexecute(inputs) for t in self.tasks)))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            outputs = [t.execute(inputs) for t in self.tasks]
        else:
            outputs = asyncio.run(_go())

        return StageResult(
            stage_name=self.name, outputs=outputs, duration=time.monotonic() - start
        )


class ConditionalStage:
    """Escolhe um de dois estágios com base em uma condição avaliada em tempo de execução.

    Avalia uma função de condição com as entradas e executa uma de
    duas ramificações (if_true ou if_false) com base no resultado.
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        if_true: Stage,
        if_false: Optional[Stage] = None,
    ) -> None:
        """Inicializa o estágio condicional.

        Args:
            name: Nome do estágio condicional.
            condition: Função que recebe entradas e retorna True/False.
            if_true: Estágio para executar se a condição for True.
            if_false: Estágio opcional para executar se a condição for False.
        """
        self.name = name
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    def run(self, inputs: Dict[str, Any]) -> StageResult:
        """Executa a ramificação apropriada com base na condição.

        Args:
            inputs: Dados de entrada para avaliar a condição e passar à ramificação.

        Returns:
            StageResult da ramificação executada, ou resultado vazio se não houver ramificação.
        """
        branch = self.if_true if self.condition(inputs) else self.if_false
        if branch is None:
            return StageResult(stage_name=self.name, outputs=[])
        return branch.run(inputs)


@dataclass
class PipelineResult:
    """Saída agregada de uma execução completa de pipeline.

    Attributes:
        stages: Lista de resultados de estágios em ordem de execução.
        duration: Tempo total para executar o pipeline em segundos.
    """

    stages: List[StageResult] = field(default_factory=list)
    duration: float = 0.0

    @property
    def final_output(self) -> str:
        """Obtém a saída final do pipeline.

        Retorna o resultado da última tarefa do último estágio,
        ou string vazia se não houver saídas.

        Returns:
            A string de saída final do pipeline.
        """
        for sr in reversed(self.stages):
            if sr.outputs:
                return sr.outputs[-1].result
        return ""


class Pipeline:
    """Executa uma sequência de estágios, alimentando o contexto para frente.

    Um pipeline compõe múltiplos estágios (sequencial, paralelo ou condicional)
    em um fluxo de trabalho que pode ser executado com contexto compartilhado.

    Example::

        pipeline = Pipeline(stages=[
            Stage("pesquisa", [task1]),
            ParallelStage("analise", [task2a, task2b]),
            ConditionalStage("expandir", cond, Stage("profundo", [task3])),
            Stage("relatorio", [task4]),
        ])
        result = pipeline.run({"topic": "IA"})
    """

    def __init__(self, stages: list, name: str = "pipeline") -> None:
        """Inicializa o pipeline.

        Args:
            stages: Lista de estágios para executar em ordem.
            name: Nome do pipeline (padrão "pipeline").
        """
        self.name = name
        self.stages = stages

    def run(self, inputs: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """Executa todos os estágios no pipeline.

        Args:
            inputs: Dados de entrada opcionais para passar ao primeiro estágio.

        Returns:
            PipelineResult contendo saídas de todos os estágios.
        """
        inputs = dict(inputs or {})
        start = time.monotonic()
        result = PipelineResult()

        EventBus.emit(
            Event(
                event_type=EventType.CREW_START,
                source_id=self.name,
                data={"type": "pipeline"},
            )
        )

        for stage in self.stages:
            sr = stage.run(inputs)
            result.stages.append(sr)

        result.duration = time.monotonic() - start
        EventBus.emit(
            Event(
                event_type=EventType.CREW_END,
                source_id=self.name,
                data={"duration": result.duration},
            )
        )
        return result
