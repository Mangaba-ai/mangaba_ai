"""
Agente v3.0 — Raciocínio ReAct, memória, planejamento, guardrails.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from mangaba.core.types import AgentState, LLMConfig, MemoryConfig, OpenRouterConfig
from mangaba.core.exceptions import AgentError
from mangaba.core.events import EventBus, Event, EventType
from mangaba.core.reasoning import ReActEngine
from mangaba.core.llm import LLMClient

if TYPE_CHECKING:
    from mangaba.tools.base import BaseTool
    from mangaba.core.guardrails import BaseGuardrail
    from mangaba.core.output_parsers import BaseOutputParser
    from mangaba.memory.base import BaseMemory

log = logging.getLogger(__name__)


class Agent:
    """Agente inteligente com raciocínio ReAct, memória e uso de ferramentas.

    Example::

        agent = Agent(
            role="Senior Data Analyst",
            goal="Analyze market trends and provide insights",
            backstory="Expert in financial markets with 15 years of experience",
            tools=[SearchTool(), CalculatorTool()],
            verbose=True,
        )
        result = agent.execute_task("Analyze Q4 revenue trends")
    """

    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[BaseTool]] = None,
        llm: Optional[LLMClient | str | None] = None,  # LLMClient ou string do provedor
        llm_config: Optional[LLMConfig | None] = None,
        api_key: Optional[str | None] = None,
        verbose: bool = False,
        memory: Optional[BaseMemory | None] = None,
        memory_config: Optional[MemoryConfig | None] = None,
        max_iterations: int = 15,
        max_retry_on_error: int = 3,
        allow_delegation: bool = True,
        step_callback: Optional[Callable | None] = None,
        guardrails: Optional[List[BaseGuardrail] | None] = None,
        output_parser: Optional[BaseOutputParser | None] = None,
        agent_id: Optional[str | None] = None,
    ) -> None:
        if not role or not role.strip():
            raise ValueError("Role cannot be empty")
        if not goal or not goal.strip():
            raise ValueError("Goal cannot be empty")
        if not backstory or not backstory.strip():
            raise ValueError("Backstory cannot be empty")

        self.role = role.strip()
        self.goal = goal.strip()
        self.backstory = backstory.strip()
        self.tools: List[BaseTool] = list(tools or [])
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.max_retry_on_error = max_retry_on_error
        self.allow_delegation = allow_delegation
        self.step_callback = step_callback
        self.guardrails = guardrails or []
        self.output_parser = output_parser
        self.memory = memory
        self.memory_config = memory_config or MemoryConfig()

        self.agent_id = (
            agent_id or f"agent_{role.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        )

        # ── Configuração LLM ────────────────────────────────────────────
        if llm is not None and not isinstance(llm, str):
            # Já é uma instância de LLMClient
            self.llm = llm
        else:
            self.llm = self._create_llm(llm, llm_config, api_key)

        # ── Memória (criar short-term automaticamente se nada fornecido) ──────
        if self.memory is None and self.memory_config.short_term:
            from mangaba.memory.short_term import ShortTermMemory

            self.memory = ShortTermMemory(
                max_items=self.memory_config.max_short_term_items
            )

        # ── Motor ReAct ─────────────────────────────────────────────
        self._react = ReActEngine(
            llm=self.llm,
            tools=self.tools,
            max_iterations=self.max_iterations,
            verbose=self.verbose,
        )

        # ── Estado ────────────────────────────────────────────────────
        self.state = AgentState(agent_id=self.agent_id)

        # ── Agentes conectados (para delegação) ────────────────────────
        self._peers: Dict[str, Agent] = {}

        if self.verbose:
            log.info("Agent initialized — role=%s tools=%d", self.role, len(self.tools))

    # ── API pública ─────────────────────────────────────────────────────

    def execute_task(self, task_description: str, context: Optional[str] = None) -> str:
        """Executa uma tarefa usando o loop ReAct com chamada de ferramentas/funções."""
        EventBus.emit(
            Event(
                event_type=EventType.AGENT_START,
                source_id=self.agent_id,
                data={"role": self.role, "task": task_description[:200]},
            )
        )

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task_description, context)

        # Injetar memórias relevantes
        memory_context = self._get_memory_context(task_description)

        last_error: Optional[Exception | None] = None
        for attempt in range(1, self.max_retry_on_error + 1):
            try:
                response = self._react.run(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    context=memory_context or None,
                    state=self.state,
                )

                result_text = response.text

                # Guardrails
                result_text = self._apply_guardrails(result_text)

                # Parser de saída
                if self.output_parser:
                    result_text = self.output_parser.parse(result_text)

                # Armazenar na memória
                if self.memory:
                    self.memory.add(
                        f"Task: {task_description}\nResult: {result_text[:500]}",
                        metadata={"agent": self.role, "type": "task_result"},
                    )

                EventBus.emit(
                    Event(
                        event_type=EventType.AGENT_END,
                        source_id=self.agent_id,
                        data={"result_preview": str(result_text)[:200]},
                    )
                )
                return str(result_text)

            except Exception as exc:
                last_error = exc
                if attempt < self.max_retry_on_error:
                    log.warning(
                        "Agent retry %d/%d: %s", attempt, self.max_retry_on_error, exc
                    )
                    continue
                break

        EventBus.emit(
            Event(
                event_type=EventType.AGENT_ERROR,
                source_id=self.agent_id,
                data={"error": str(last_error)},
            )
        )
        raise AgentError(
            f"Task failed after {self.max_retry_on_error} attempts: {last_error}",
            cause=last_error,
        )

    def connect_to(self, other: Agent) -> None:
        """Registra outro agente como par para delegação."""
        self._peers[other.agent_id] = other
        other._peers[self.agent_id] = self

    def delegate(
        self, peer_id: str, task_description: str, context: Optional[str] = None
    ) -> str:
        """Delega uma tarefa para um agente par conectado."""
        peer = self._peers.get(peer_id)
        if peer is None:
            raise AgentError(f"No peer agent with id '{peer_id}'")
        return peer.execute_task(task_description, context)

    # ── Construção de prompt ────────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        parts = [
            f"You are: {self.role}",
            f"Your goal is: {self.goal}",
            f"Background: {self.backstory}",
        ]
        if self.allow_delegation and self._peers:
            peers_desc = ", ".join(f"{p.role}" for p in self._peers.values())
            parts.append(f"\nYou can delegate to these agents: {peers_desc}")
        return "\n\n".join(parts)

    def _build_user_prompt(self, task_description: str, context: Optional[str]) -> str:
        parts = []
        if context:
            parts.append(f"Context:\n{context}")
        parts.append(f"Task:\n{task_description}")
        parts.append("Complete this task according to your role and goal.")
        return "\n\n".join(parts)

    def _get_memory_context(self, query: str) -> str:
        if self.memory is None:
            return ""
        return self.memory.get_relevant(query, max_results=5)

    def _apply_guardrails(self, text: str) -> str:
        for g in self.guardrails:
            text = g.validate(text)
        return text

    # ── Fábrica LLM ────────────────────────────────────────────────────
    @staticmethod
    def _create_llm(
        provider_str: Optional[str],
        llm_config: Optional[LLMConfig],
        api_key: Optional[str],
    ) -> Any:
        from mangaba.core.llm import create_llm_client

        # Usar a configuração fornecida ou criar uma padrão
        cfg = llm_config or LLMConfig()

        # Parâmetros básicos
        prov = provider_str or cfg.provider
        key = api_key or cfg.api_key
        model = cfg.model

        # Inicializar dicionário de opções
        options = {
            "temperature": cfg.temperature,
            "max_output_tokens": cfg.max_tokens,
        }

        # Se for um OpenRouterConfig, extraímos os campos extras
        if isinstance(cfg, OpenRouterConfig):
            options["site_name"] = cfg.site_name
            options["site_url"] = cfg.site_url
            if cfg.route:
                options["route"] = cfg.route

        return create_llm_client(
            provider=prov, api_key=key or "", model=model, **options
        )
