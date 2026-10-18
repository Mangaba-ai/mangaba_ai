"""Offline tests for the core: Agent, Task, Crew and Flow.

A scripted provider is registered in the real provider registry, so every call
goes through ``LLMClient`` (events, usage tracking) exactly as in production —
only the network is replaced.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import pytest
from pydantic import BaseModel

from mangaba import Agent, Crew, Process, Task, tool
from mangaba.core.exceptions import AgentError, CrewError
from mangaba.core.llm import client as llm_client
from mangaba.core.llm.client import BaseLLMProvider, LLMClient
from mangaba.core.types import LLMResponse, TokenUsage, ToolCall
from mangaba.core.guardrails import FunctionGuardrail
from mangaba.flows import Flow, and_, listen, or_, persist, router, start
from mangaba.flows.persistence import SQLiteFlowStore


# ── Scripted provider ──────────────────────────────────────────────────


class ScriptedProvider(BaseLLMProvider):
    """Replays a queue of responses and records every prompt it receives.

    Each queued item is a string (final answer), an ``LLMResponse`` (e.g. one
    carrying tool calls), an exception instance (raised) or a callable taking
    the prompt text and returning one of those.
    """

    name = "scripted"
    requires_api_key = False

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        super().__init__(api_key, model, **options)
        self.script: List[Any] = list(options.get("script", []))
        self.default: Optional[str] = options.get("default")
        self.prompts: List[str] = []
        self.message_log: List[List[Dict[str, Any]]] = []

    def _next(self, prompt: str) -> LLMResponse:
        self.prompts.append(prompt)
        if self.script:
            item = self.script.pop(0)
        elif self.default is not None:
            item = self.default
        else:
            raise AssertionError(f"ScriptedProvider ran out of responses; prompt was:\n{prompt[:500]}")
        if callable(item) and not isinstance(item, LLMResponse):
            item = item(prompt)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, LLMResponse):
            return item
        return LLMResponse(
            content=str(item),
            model=self.model,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return self._next(prompt)

    def generate_with_tools(self, messages, tools=None, **kwargs: Any) -> LLMResponse:
        self.message_log.append([dict(m) for m in messages])
        return self._next("\n".join(str(m.get("content", "")) for m in messages))


@pytest.fixture(autouse=True)
def _register_scripted(monkeypatch):
    monkeypatch.setitem(llm_client.PROVIDERS, ScriptedProvider.name, ScriptedProvider)


def scripted_llm(*script: Any, default: Optional[str] = None) -> LLMClient:
    return LLMClient(provider="scripted", api_key="", model="fake-1", script=list(script), default=default)


def provider_of(llm: LLMClient) -> ScriptedProvider:
    return llm._provider  # type: ignore[return-value]


def make_agent(llm: LLMClient, role: str = "Analyst", **kwargs: Any) -> Agent:
    return Agent(role=role, goal=f"{role} goal", backstory=f"{role} backstory", llm=llm, **kwargs)


def call(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(content="", tool_calls=[ToolCall(tool_name=name, arguments=arguments)], model="fake-1")


# ── Agent ──────────────────────────────────────────────────────────────


class TestAgent:
    def test_kickoff_returns_llm_answer_and_sends_role(self):
        llm = scripted_llm("Resposta final")
        agent = make_agent(llm, role="Pesquisador")

        assert agent.kickoff("Qual a capital de Alagoas?") == "Resposta final"
        prompt = provider_of(llm).prompts[0]
        assert "Pesquisador" in prompt
        assert "Qual a capital de Alagoas?" in prompt

    def test_tool_call_is_executed_and_observation_fed_back(self):
        calls: List[tuple] = []

        @tool
        def soma(a: int, b: int) -> int:
            """Soma dois inteiros."""
            calls.append((a, b))
            return a + b

        llm = scripted_llm(call("soma", a=2, b=3), "O resultado é 5")
        agent = make_agent(llm, tools=[soma])

        assert agent.kickoff("Quanto é 2+3?") == "O resultado é 5"
        assert calls == [(2, 3)]
        second_turn = provider_of(llm).message_log[1]
        tool_msgs = [m for m in second_turn if m["role"] == "tool"]
        assert tool_msgs and "[soma]: 5" in tool_msgs[-1]["content"]

    def test_tool_error_is_reported_to_llm_instead_of_crashing(self):
        @tool
        def quebra(x: str) -> str:
            """Sempre falha."""
            raise RuntimeError("boom")

        llm = scripted_llm(call("quebra", x="a"), "Contornei o erro")
        agent = make_agent(llm, tools=[quebra])

        assert agent.kickoff("tente") == "Contornei o erro"
        tool_msg = [m for m in provider_of(llm).message_log[1] if m["role"] == "tool"][-1]
        assert "ERROR" in tool_msg["content"] and "boom" in tool_msg["content"]

    def test_max_iterations_without_final_answer_raises(self):
        @tool
        def eco(x: str) -> str:
            """Ecoa."""
            return x

        llm = scripted_llm(default=None)
        provider_of(llm).script = [call("eco", x="1") for _ in range(10)]
        agent = make_agent(llm, tools=[eco], max_iter=2, max_retry_limit=1)

        with pytest.raises(AgentError):
            agent.kickoff("loop")

    def test_transient_llm_error_is_retried(self):
        llm = scripted_llm(RuntimeError("503"), "Recuperado")
        agent = make_agent(llm, max_retry_limit=2)

        assert agent.kickoff("oi") == "Recuperado"
        assert len(provider_of(llm).prompts) == 2

    def test_context_reaches_the_prompt(self):
        llm = scripted_llm("ok")
        make_agent(llm).kickoff("resuma", context="contrato nº 4471")
        assert "contrato nº 4471" in provider_of(llm).prompts[0]

    def test_step_callback_receives_output(self):
        seen: List[Dict[str, Any]] = []
        llm = scripted_llm("feito")
        make_agent(llm, step_callback=seen.append).kickoff("tarefa")
        assert seen and seen[0]["output"] == "feito"

    def test_empty_role_is_rejected(self):
        with pytest.raises(ValueError):
            Agent(role=" ", goal="g", backstory="b", llm=scripted_llm("x"))


# ── Task ───────────────────────────────────────────────────────────────


class Relatorio(BaseModel):
    titulo: str
    nota: int


class TestTask:
    def test_inputs_are_interpolated(self):
        llm = scripted_llm("ok")
        task = Task(description="Analise {tema}", expected_output="Resumo de {tema}", agent=make_agent(llm))
        Crew(agents=[task.agent], tasks=[task]).kickoff(inputs={"tema": "fibra óptica"})
        assert "fibra óptica" in provider_of(llm).prompts[0]

    def test_output_pydantic_is_parsed(self):
        llm = scripted_llm('```json\n{"titulo": "Q4", "nota": 9}\n```')
        task = Task(
            description="Avalie o trimestre",
            expected_output="JSON com titulo e nota",
            agent=make_agent(llm),
            output_pydantic=Relatorio,
        )
        out = Crew(agents=[task.agent], tasks=[task]).kickoff()
        parsed = out.tasks_outputs[0].pydantic
        assert isinstance(parsed, Relatorio)
        assert parsed.nota == 9

    def test_condition_false_skips_llm(self):
        llm = scripted_llm(default="nunca")
        agent = make_agent(llm)
        task = Task(description="Só se urgente", expected_output="x", agent=agent, condition=lambda i: i.get("urgente", False))
        Crew(agents=[agent], tasks=[task]).kickoff(inputs={"urgente": False})
        assert provider_of(llm).prompts == []

    def test_guardrail_rejection_is_fed_back_and_retried(self):
        llm = scripted_llm("curto", "uma resposta longa o bastante")
        agent = make_agent(llm)
        guard = FunctionGuardrail(lambda t: (True, t) if len(t) > 10 else (False, "resposta curta demais"))
        task = Task(description="Explique", expected_output="x", agent=agent, guardrail=guard)

        out = Crew(agents=[agent], tasks=[task]).kickoff()

        assert out.final_output == "uma resposta longa o bastante"
        assert "resposta curta demais" in provider_of(llm).prompts[1]

    def test_empty_description_is_rejected(self):
        with pytest.raises(ValueError):
            Task(description="", expected_output="x")


# ── Crew ───────────────────────────────────────────────────────────────


class TestCrew:
    def test_sequential_passes_previous_output_as_context(self):
        llm_a = scripted_llm("FATO-123")
        llm_b = scripted_llm("Relatório baseado em FATO-123")
        pesquisador = make_agent(llm_a, role="Pesquisador")
        redator = make_agent(llm_b, role="Redator")
        t1 = Task(description="Pesquise", expected_output="Fatos", agent=pesquisador)
        t2 = Task(description="Escreva", expected_output="Texto", agent=redator, context=[t1])

        out = Crew(agents=[pesquisador, redator], tasks=[t1, t2], process=Process.SEQUENTIAL).kickoff()

        assert out.final_output == "Relatório baseado em FATO-123"
        assert out.raw == out.final_output
        assert [o.result for o in out.tasks_outputs] == ["FATO-123", "Relatório baseado em FATO-123"]
        assert "FATO-123" in provider_of(llm_b).prompts[0]

    def test_usage_metrics_are_aggregated(self):
        llm = scripted_llm("a", "b")
        agent = make_agent(llm)
        tasks = [Task(description=f"t{i}", expected_output="x", agent=agent) for i in range(2)]
        out = Crew(agents=[agent], tasks=tasks).kickoff()
        assert out.token_usage["total_tokens"] >= 30

    def test_parallel_runs_every_task(self):
        llm = scripted_llm(default="ok")
        agent = make_agent(llm)
        tasks = [Task(description=f"tarefa {i}", expected_output="x", agent=agent) for i in range(3)]
        out = Crew(agents=[agent], tasks=tasks, process=Process.PARALLEL).kickoff()
        assert len(out.tasks_outputs) == 3
        assert all(o.result == "ok" for o in out.tasks_outputs)

    def test_kickoff_for_each(self):
        llm = scripted_llm(default="ok")
        agent = make_agent(llm)
        task = Task(description="Resuma {cidade}", expected_output="x", agent=agent)
        outs = Crew(agents=[agent], tasks=[task]).kickoff_for_each([{"cidade": "Maceió"}, {"cidade": "Recife"}])
        assert len(outs) == 2
        joined = "\n".join(provider_of(llm).prompts)
        assert "Maceió" in joined and "Recife" in joined

    def test_akickoff(self):
        llm = scripted_llm("assíncrono")
        agent = make_agent(llm)
        task = Task(description="t", expected_output="x", agent=agent)
        out = asyncio.run(Crew(agents=[agent], tasks=[task]).akickoff())
        assert out.final_output == "assíncrono"

    def test_before_and_after_callbacks(self):
        llm = scripted_llm("ok")
        agent = make_agent(llm)
        task = Task(description="Fale de {x}", expected_output="y", agent=agent)
        seen: List[Any] = []

        def before(inputs):
            return {**inputs, "x": "injetado"}

        def after(output):
            seen.append(output.final_output)
            return output

        Crew(agents=[agent], tasks=[task], before_kickoff_callbacks=[before], after_kickoff_callbacks=[after]).kickoff({"x": "orig"})
        assert "injetado" in provider_of(llm).prompts[0]
        assert seen == ["ok"]

    def test_hierarchical_manager_refines_delegates_and_reviews(self):
        manager_llm = scripted_llm("Instruções refinadas", "APPROVED")
        worker_llm = scripted_llm("Entrega do especialista")
        worker = make_agent(worker_llm, role="Especialista")
        task = Task(description="Analise o churn", expected_output="Diagnóstico")

        out = Crew(agents=[worker], tasks=[task], process=Process.HIERARCHICAL, manager_llm=manager_llm).kickoff()

        assert out.final_output == "Entrega do especialista"
        assert "Instruções refinadas" in provider_of(worker_llm).prompts[0]
        assert task.agent is None  # assignment restored after the run

    def test_hierarchical_revise_sends_work_back_once(self):
        manager_llm = scripted_llm("Instruções", "REVISE: faltou o número")
        worker_llm = scripted_llm("v1", "v2 com número")
        worker = make_agent(worker_llm, role="Especialista")
        task = Task(description="Calcule", expected_output="Número")

        out = Crew(agents=[worker], tasks=[task], process=Process.HIERARCHICAL, manager_llm=manager_llm).kickoff()

        assert out.final_output == "v2 com número"
        assert "faltou o número" in provider_of(worker_llm).prompts[1]

    def test_hierarchical_without_manager_needs_two_agents(self):
        agent = make_agent(scripted_llm(default="x"))
        task = Task(description="t", expected_output="x", agent=agent)
        with pytest.raises(CrewError):
            Crew(agents=[agent], tasks=[task], process=Process.HIERARCHICAL).kickoff()

    def test_consensual_merges_every_agent(self):
        llm_a = scripted_llm("opinião A", "consenso final")
        llm_b = scripted_llm("opinião B")
        a, b = make_agent(llm_a, role="Jurista"), make_agent(llm_b, role="Economista")
        task = Task(description="Avalie a lei", expected_output="Parecer", agent=a)

        out = Crew(agents=[a, b], tasks=[task], process=Process.CONSENSUAL).kickoff()

        assert out.final_output == "consenso final"
        synthesis = provider_of(llm_a).prompts[-1]
        assert "opinião A" in synthesis and "opinião B" in synthesis

    def test_output_log_file_is_written(self, tmp_path):
        llm = scripted_llm("registrado")
        agent = make_agent(llm)
        task = Task(description="t", expected_output="x", agent=agent)
        log_file = tmp_path / "crew.log"
        Crew(agents=[agent], tasks=[task], output_log_file=str(log_file)).kickoff()
        assert "registrado" in log_file.read_text(encoding="utf-8")

    def test_empty_crew_is_rejected(self):
        with pytest.raises(CrewError):
            Crew(agents=[], tasks=[])


# ── Flow ───────────────────────────────────────────────────────────────


class Estado(BaseModel):
    visitas: List[str] = []
    total: int = 0


class TestFlow:
    def test_router_picks_branch(self):
        class Triagem(Flow):
            @start()
            def medir(self):
                return 7

            @router(medir)
            def decidir(self, valor):
                return "alto" if valor > 5 else "baixo"

            @listen("alto")
            def escalar(self):
                return "escalado"

            @listen("baixo")
            def arquivar(self):
                return "arquivado"

        flow = Triagem()
        assert flow.kickoff() == "escalado"
        assert "arquivar" not in flow.executed_methods

    def test_and_waits_for_both_branches(self):
        class Junta(Flow[Estado]):
            @start()
            def a(self):
                self.state.visitas.append("a")

            @start()
            def b(self):
                self.state.visitas.append("b")

            @listen(and_(a, b))
            def fim(self):
                self.state.visitas.append("fim")
                return len(self.state.visitas)

        flow = Junta()
        assert flow.kickoff() == 3
        assert flow.state.visitas[-1] == "fim"
        assert set(flow.state.visitas[:2]) == {"a", "b"}

    def test_or_fires_on_whichever_branch_ran(self):
        class Qualquer(Flow[Estado]):
            @start()
            def origem(self):
                return "cache"

            @router(origem)
            def escolher(self, fonte):
                return fonte

            @listen("cache")
            def do_cache(self):
                return "dado do cache"

            @listen("api")
            def da_api(self):
                return "dado da api"

            @listen(or_(do_cache, da_api))
            def renderizar(self, payload):
                self.state.total += 1
                return payload.upper()

        flow = Qualquer()
        assert flow.kickoff() == "DADO DO CACHE"
        assert flow.state.total == 1
        assert "da_api" not in flow.executed_methods

    def test_inputs_seed_typed_state(self):
        class Soma(Flow[Estado]):
            @start()
            def somar(self):
                self.state.total += 10
                return self.state.total

        assert Soma().kickoff(inputs={"total": 5}) == 15

    def test_flow_drives_a_crew(self):
        llm = scripted_llm("texto do crew")

        class ComCrew(Flow):
            @start()
            def rodar(self):
                agent = make_agent(llm)
                task = Task(description="escreva", expected_output="x", agent=agent)
                return Crew(agents=[agent], tasks=[task]).kickoff().final_output

            @listen(rodar)
            def publicar(self, texto):
                return texto.upper()

        assert ComCrew().kickoff() == "TEXTO DO CREW"

    def test_persist_and_resume_skip_completed_steps(self, tmp_path):
        store = SQLiteFlowStore(str(tmp_path / "flows.db"))
        runs: List[str] = []

        @persist
        class Pedido(Flow[Estado]):
            @start()
            def cobrar(self):
                runs.append("cobrar")
                self.state.total = 100

            @listen(cobrar)
            def enviar(self):
                runs.append("enviar")
                if self.state.visitas == []:
                    self.state.visitas.append("tentou")
                    raise RuntimeError("transportadora fora do ar")
                return "enviado"

        first = Pedido(persistence=store)
        with pytest.raises(Exception):
            first.kickoff()
        assert runs == ["cobrar", "enviar"]

        second = Pedido(persistence=store)
        second.load_state(first.flow_id)
        assert second.state.total == 100
        second.state.visitas.append("retomada")
        assert second.resume(first.flow_id, inputs={"visitas": ["retomada"]}) == "enviado"
        assert runs.count("cobrar") == 1  # completed step was not charged twice
