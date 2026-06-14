"""
Motor de raciocínio ReAct para Mangaba AI v3.0

Implementa o loop Pensamento → Ação → Observação que permite aos agentes
usar ferramentas de forma inteligente via chamada de função do LLM.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from mangaba.core.types import (
    AgentState,
    AgentStatus,
    FinishReason,
    LLMResponse,
    ReActStep,
    ToolCall,
    ToolResult,
)
from mangaba.core.exceptions import MaxIterationsError
from mangaba.core.events import EventBus, Event, EventType

log = logging.getLogger(__name__)


class ReActEngine:
    """Executor de loop ReAct (Raciocínio + Ação).

    Dado um cliente LLM, um conjunto de ferramentas e um prompt do sistema, o motor
    iterativamente:
      1. Envia a conversa para o LLM (com declarações de ferramenta).
      2. Se o LLM retorna tool_calls → executa-os, anexa resultados.
      3. Se o LLM retorna texto (finish_reason=stop) → retorna a resposta.
      4. Repete até que ``max_iterations`` seja alcançado.

    Example::

        engine = ReActEngine(llm=llm_client, tools=[SearchTool(), CalcTool()])
        result = engine.run(
            system_prompt="Você é um analista de pesquisa.",
            user_prompt="Qual é o PIB do Brasil?"
        )
        print(result.content)
    """

    def __init__(
        self,
        llm: Any,  # LLMClient
        tools: Optional[List[Any]] = None,
        max_iterations: int = 15,
        verbose: bool = False,
    ) -> None:
        self.llm = llm
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.verbose = verbose
        self._tool_map: Dict[str, Any] = {t.name: t for t in self.tools}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        state: Optional[AgentState] = None,
    ) -> LLMResponse:
        """Executa o loop ReAct completo e retorna a resposta final do LLM."""
        messages = self._build_initial_messages(system_prompt, user_prompt, context)
        state = state or AgentState(agent_id="react")
        state.status = AgentStatus.RUNNING

        EventBus.emit(
            Event(
                event_type=EventType.AGENT_START,
                data={
                    "prompt_preview": user_prompt[:200],
                    "tools": list(self._tool_map.keys()),
                },
            )
        )

        for iteration in range(1, self.max_iterations + 1):
            state.iteration_count = iteration

            # Call LLM with tool declarations
            response = self._call_llm(messages)

            step = ReActStep(step_number=iteration)

            if response.has_tool_calls:
                # Agente quer usar ferramentas
                state.status = AgentStatus.WAITING_TOOL
                step.thought = response.text or None
                step.action = response.tool_calls[0]

                EventBus.emit(
                    Event(
                        event_type=EventType.REACT_ACTION,
                        data={
                            "iteration": iteration,
                            "tool_calls": [
                                tc.model_dump() for tc in response.tool_calls
                            ],
                        },
                    )
                )

                # Adicionar mensagem do assistente (com chamadas de ferramentas)
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.text or "",
                        "tool_calls": [tc.model_dump() for tc in response.tool_calls],
                    }
                )

                # Execute each tool and collect results
                tool_results = self._execute_tool_calls(response.tool_calls)

                # Check for return_direct
                for tr in tool_results:
                    tool_obj = self._tool_map.get(tr.tool_name)
                    if (
                        tool_obj
                        and getattr(tool_obj, "return_direct", False)
                        and tr.success
                    ):
                        state.status = AgentStatus.COMPLETED
                        step.observation = str(tr.output)
                        state.steps.append(step)
                        EventBus.emit(
                            Event(
                                event_type=EventType.AGENT_END,
                                data={
                                    "iterations": iteration,
                                    "finish": "return_direct",
                                },
                            )
                        )
                        return LLMResponse(
                            content=str(tr.output),
                            model=response.model,
                            finish_reason=FinishReason.STOP,
                        )

                # Adicionar resultados das ferramentas como mensagem de ferramenta
                observation_parts = []
                for tr in tool_results:
                    if tr.success:
                        observation_parts.append(f"[{tr.tool_name}]: {tr.output}")
                    else:
                        observation_parts.append(f"[{tr.tool_name}] ERROR: {tr.error}")

                observation = "\n".join(observation_parts)
                step.observation = observation
                messages.append({"role": "tool", "content": observation})

                EventBus.emit(
                    Event(
                        event_type=EventType.REACT_OBSERVATION,
                        data={
                            "iteration": iteration,
                            "observation_preview": observation[:300],
                        },
                    )
                )

            else:
                # Agente terminou o raciocínio — resposta final
                state.status = AgentStatus.COMPLETED
                step.thought = response.text
                state.steps.append(step)

                EventBus.emit(
                    Event(
                        event_type=EventType.AGENT_END,
                        data={"iterations": iteration, "finish": "stop"},
                    )
                )
                return response

            state.steps.append(step)
            state.status = AgentStatus.RUNNING

        # Max iterations exceeded
        state.status = AgentStatus.ERROR
        EventBus.emit(
            Event(
                event_type=EventType.AGENT_ERROR,
                data={"error": "max_iterations", "iterations": self.max_iterations},
            )
        )
        raise MaxIterationsError(
            f"ReAct loop exceeded {self.max_iterations} iterations without a final answer."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_initial_messages(
        self, system_prompt: str, user_prompt: str, context: Optional[str]
    ) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})
            messages.append(
                {
                    "role": "assistant",
                    "content": "I've noted the context. What would you like me to do?",
                }
            )
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def _call_llm(self, messages: List[Dict[str, Any]]) -> LLMResponse:
        if self.tools:
            return self.llm.generate_with_tools(messages, tools=self.tools)
        # No tools — plain generation
        user_content = messages[-1].get("content", "")
        return self.llm.generate(user_content)

    def _execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        results: List[ToolResult] = []
        for tc in tool_calls:
            tool = self._tool_map.get(tc.tool_name)
            if tool is None:
                results.append(
                    ToolResult(
                        call_id=tc.id,
                        tool_name=tc.tool_name,
                        error=f"Tool '{tc.tool_name}' not found. Available: {list(self._tool_map.keys())}",
                        success=False,
                    )
                )
                continue
            try:
                output = tool.run(**tc.arguments)
                results.append(
                    ToolResult(
                        call_id=tc.id,
                        tool_name=tc.tool_name,
                        output=output,
                        success=True,
                    )
                )
            except Exception as exc:
                results.append(
                    ToolResult(
                        call_id=tc.id,
                        tool_name=tc.tool_name,
                        error=str(exc),
                        success=False,
                    )
                )
        return results
