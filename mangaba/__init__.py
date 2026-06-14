"""Mangaba AI v3.0 — Framework de orquestração multi-agente profissional."""

from mangaba.core.agent import Agent
from mangaba.core.task import Task
from mangaba.core.crew import Crew, Process
from mangaba.core.workflow import Pipeline, Stage, ParallelStage, ConditionalStage
from mangaba.core.events import EventBus, Event, EventType
from mangaba.core.exceptions import MangabaError
from mangaba.core.reasoning import ReActEngine
from mangaba.core.guardrails import GuardrailChain
from mangaba.core.output_parsers import JSONOutputParser, PydanticOutputParser
from mangaba.core.llm import (
    LLMClient,
    create_llm_client,
    list_huggingface_models,
    hf_model_supports_tools,
    HF_OPEN_MODELS,
)
from mangaba.tools.base import BaseTool
from mangaba.tools.decorator import tool

__version__ = "3.3.0"
__all__ = [
    # Núcleo
    "Agent",
    "Task",
    "Crew",
    "Process",
    # Fluxo de trabalho
    "Pipeline",
    "Stage",
    "ParallelStage",
    "ConditionalStage",
    # LLM
    "LLMClient",
    "create_llm_client",
    "list_huggingface_models",
    "hf_model_supports_tools",
    "HF_OPEN_MODELS",
    # Eventos
    "EventBus",
    "Event",
    "EventType",
    # Raciocínio
    "ReActEngine",
    # Guardrails e Parsers
    "GuardrailChain",
    "JSONOutputParser",
    "PydanticOutputParser",
    # Ferramentas
    "BaseTool",
    "tool",
    # Exceções
    "MangabaError",
]
