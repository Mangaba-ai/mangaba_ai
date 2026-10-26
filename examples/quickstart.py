#!/usr/bin/env python3
"""Quickstart do Mangaba AI — do zero ao primeiro crew em 1 comando.

Uso:
    pip install -e ".[google]"          # na raiz do repositório
    export GOOGLE_API_KEY="sua-chave"   # ou OPENAI_API_KEY / ANTHROPIC_API_KEY
    python examples/quickstart.py

Sem chave de API? Rode um modelo local e ajuste o provider:
    ollama pull qwen2.5:7b
    LLM_PROVIDER=ollama LLM_MODEL=qwen2.5:7b python examples/quickstart.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba import Agent, Crew, Process, Task, tool
from mangaba.core.types import LLMConfig


@tool
def get_today(topic: str) -> str:
    """Return a one-line fun fact hook for the given topic (demo tool)."""
    return f"Curiosidade sobre {topic}: a Mangaba e fruto tipica do Nordeste do Brasil."


def build_llm_config() -> LLMConfig:
    provider = os.getenv("LLM_PROVIDER", "google").lower()
    defaults = {
        "google": "gemini-2.5-flash",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-haiku-4-5-20251001",
        "ollama": "qwen2.5:7b",
    }
    return LLMConfig(
        provider=provider,
        model=os.getenv("LLM_MODEL", defaults.get(provider, "gemini-2.5-flash")),
        api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or "",
    )


def main() -> int:
    llm_config = build_llm_config()

    pesquisador = Agent(
        role="Pesquisador",
        goal="Levantar 3 fatos objetivos sobre o tema",
        backstory="Jornalista cientifico, direto e preciso.",
        tools=[get_today],
        llm_config=llm_config,
    )
    redator = Agent(
        role="Redator",
        goal="Transformar os fatos em um paragrafo claro",
        backstory="Redator experiente em textos curtos.",
        llm_config=llm_config,
    )

    pesquisa = Task(
        description="Levante 3 fatos objetivos sobre {topic}",
        expected_output="Lista com 3 fatos, um por linha",
        agent=pesquisador,
    )
    texto = Task(
        description="Escreva um paragrafo claro a partir dos fatos levantados",
        expected_output="Um paragrafo de ate 5 linhas",
        agent=redator,
        context=[pesquisa],
    )

    crew = Crew(agents=[pesquisador, redator], tasks=[pesquisa, texto])
    result = crew.kickoff(inputs={"topic": "mangaba"})

    print()
    print("===== Resultado =====")
    print(result.final_output)
    print()
    print(f"Tarefas: {len(result.tasks_outputs)} | Tokens: {result.token_usage.get('total_tokens', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
