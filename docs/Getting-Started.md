# 🚀 Getting Started

Guia de instalação e primeiros passos com o Mangaba AI.

---

## Pré-requisitos

- **Python** ≥ 3.10
- **pip** ou **uv** (gerenciador de pacotes)
- **API Key** de um provider LLM (Google, OpenAI, Anthropic, etc.)

---

## Instalação

### Via pip

```bash
# Instalação básica (OpenAI, OpenRouter, Ollama, OpenAI-compatible)
pip install mangaba

# SDK do provedor: google, anthropic, huggingface ou providers (todos)
pip install "mangaba[google]"

# Com suporte a RAG (numpy)
pip install mangaba[rag]

# Com Redis vector store
pip install mangaba[redis]

# Com PostgreSQL vector store (pgvector)
pip install mangaba[postgres]

# Instalação completa
pip install mangaba[all]

# Ferramentas de desenvolvimento
pip install mangaba[dev]
```

### Via uv (recomendado)

```bash
uv pip install mangaba
uv pip install "mangaba[all]"
```

### Instalação para desenvolvimento

```bash
git clone https://github.com/mangaba-ai/mangaba-ai.git
cd mangaba-ai
pip install -e ".[dev]"
```

---

## Configuração de Environment

Crie um arquivo `.env` na raiz do seu projeto:

```env
# LLM Providers
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HUGGINGFACE_API_KEY=your_hf_token_here

# Vector Stores
MANGABA_REDIS_URL=redis://localhost:6379
MANGABA_VECTORSTORE_URL=postgresql://postgres:password@localhost:5432/mangaba

# OpenRouter (opcional)
OPENROUTER_API_KEY=your_openrouter_key
```

---

## Primeiro Projeto

### 1. Agente Simples

```python
from mangaba import Agent
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

# Configurar LLM via LLMConfig
llm_config = LLMConfig(
    provider="google",
    model="gemini-2.5-flash",
    api_key="sua-api-key",
    temperature=0.7,
    max_tokens=4096,
)

llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

# Criar agente
agente = Agent(
    role="Escritor Técnico",
    goal="Escrever explicações claras sobre tecnologia",
    backstory="Você é um escritor técnico experiente com 10 anos de experiência",
    llm=llm,
    verbose=True,
)

# Executar tarefa
resultado = agente.execute_task(
    "Explique o que é RAG (Retrieval-Augmented Generation) em 3 parágrafos"
)
print(resultado)
```

### 2. Crew Multi-Agent

```python
from mangaba import Agent, Task, Crew, Process
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

# Configuração centralizada do LLM
llm_config = LLMConfig(
    provider="google",
    model="gemini-2.5-flash",
    api_key="sua-api-key",
    temperature=0.7,
    max_tokens=4096,
)

llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

# Criar agents
pesquisador = Agent(
    role="Pesquisador Senior",
    goal="Coletar informações detalhadas sobre o tema",
    backstory="Expert em pesquisa com acesso a fontes acadêmicas",
    llm=llm,
)

analista = Agent(
    role="Analista de Dados",
    goal="Analisar e sintetizar os dados coletados",
    backstory="Especialista em análise de dados e padrões",
    llm=llm,
)

escritor = Agent(
    role="Redator Técnico",
    goal="Produzir conteúdo claro e bem estruturado",
    backstory="Redator profissional focado em clareza",
    llm=llm,
)

# Criar tarefas
pesquisa = Task(
    description="Pesquisar tendências de IA em 2026",
    expected_output="Lista de 10 tendências com descrição",
    agent=pesquisador,
)

analise = Task(
    description="Analisar as tendências e identificar padrões",
    expected_output="Análise com insights chave",
    agent=analista,
    context=[pesquisa],
)

relatorio = Task(
    description="Escrever relatório final consolidado",
    expected_output="Relatório completo formatado em markdown",
    agent=escritor,
    context=[analise],
)

# Criar e executar crew
crew = Crew(
    agents=[pesquisador, analista, escritor],
    tasks=[pesquisa, analise, relatorio],
    process=Process.SEQUENTIAL,
    verbose=True,
)

resultado = crew.kickoff()
print(f"\nResultado final:\n{resultado}")
```

### 3. Com Tools

```python
from mangaba import Agent, BaseTool
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client
from mangaba.tools.math_tools import CalculatorTool

# Configuração via LLMConfig
llm_config = LLMConfig(
    provider="google",
    api_key="sua-api-key",
    model="gemini-2.5-flash",
)

llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

class SaudacaoTool(BaseTool):
    name = "saudacao"
    description = "Retorna uma saudação personalizada"

    def _run(self, nome: str) -> str:
        return f"Olá, {nome}! Como posso ajudar?"

agente = Agent(
    role="Assistente Virtual",
    goal="Ajudar usuários com saudações e cálculos",
    backstory="Assistente amigável e prestativo",
    tools=[SaudacaoTool(), CalculatorTool()],
    llm=llm,
)

# O agente pode usar ferramentas automaticamente via ReAct
resultado = agente.execute_task(
    "Cumprite João e calcule quanto é 15% de 250"
)
```

---

## Docker para Vector Stores

Para usar Redis e PostgreSQL como vector stores:

```bash
# Usando docker compose
docker compose -f docker-compose.vectorstores.yml up -d

# Ou individualmente
docker run -d --name mangaba-redis -p 6379:6379 redis/redis-stack:latest
docker run -d --name mangaba-postgres -e POSTGRES_PASSWORD=minhasenha -p 5432:5432 ankane/pgvector:latest
```

---

## Próximos Passos

- [Core Components](Core-Components.md) — Aprenda sobre Agent, Task e Crew
- [LLM Providers](LLM-Providers.md) — Configure diferentes providers
- [Tools](Tools.md) — Crie ferramentas customizadas
- [RAG](RAG.md) — Implemente Retrieval-Augmented Generation
- [Vector Stores](Vector-Stores.md) — Persista vetores em Redis/PostgreSQL
- [Workflows](Workflows.md) — Crie pipelines complexos
