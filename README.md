<div align="center">
  <img src="assets/mangaba-logo.svg" alt="Mangaba AI" width="140"/>

  [![Mangaba AI](https://img.shields.io/badge/Mangaba-AI-F97518?style=for-the-badge)](https://www.mangaba.ia.br)
  [![Site](https://img.shields.io/badge/mangaba.ia.br-1E0D01?style=for-the-badge)](https://www.mangaba.ia.br)
</div>

# Mangaba AI

[![PyPI version](https://img.shields.io/pypi/v/mangaba.svg)](https://pypi.org/project/mangaba/)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Mangaba-ai/mangaba_ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Mangaba-ai/mangaba_ai/actions/workflows/ci.yml)

Framework profissional de orquestração multi-agente com ReAct reasoning, function calling nativo, RAG, memória persistente, protocolos A2A/MCP, vector stores e suporte resiliente a múltiplos provedores LLM.

<!-- DEMO-GIF: após gerar assets/demo.gif com scripts/record_demo.sh, descomente:
<div align="center">
  <img src="assets/demo.gif" alt="Demo: primeiro crew em 1 comando" width="720"/>
</div>
-->

Execute o exemplo abaixo em 1 comando (veja `examples/quickstart.py`):

```bash
git clone https://github.com/Mangaba-ai/mangaba_ai.git && cd mangaba_ai
pip install -e ".[google]"
export GOOGLE_API_KEY="sua-chave"
python examples/quickstart.py
```

Alternativa leve e completa a CrewAI + LangChain em um único pacote, com interoperabilidade real entre provedores, arquitetura resiliente e comunicação entre agentes via protocolos padrão.

## Destaques da v4.0.0

- **Flows** — Orquestração orientada a eventos com `@start`, `@listen`, `@router`, combinadores `and_`/`or_`, estado tipado em Pydantic, persistência em SQLite (`@persist`, com resume e fork) e gráfico de execução em HTML via `flow.plot()`
- **Knowledge** — Base de conhecimento separada da memória: PDF, DOCX, Excel, JSON, CSV, URL e diretórios inteiros, com `score_threshold` e escopo por agente ou por crew
- **Memória unificada** — Classe `Memory` com recall semântico composto (similaridade + recência + importância), extração automática de fatos, consolidação de duplicatas e gravação assíncrona
- **CLI** — `mangaba create/run/test/train/chat/config/reset-memories/replay/install`, com projetos declarados em `agents.yaml` / `tasks.yaml`
- **Treino e avaliação** — `mangaba train` (loop de feedback humano) e `mangaba test` (nota de qualidade 1–10 por tarefa e por agente)
- **Modelos locais** — Ollama e qualquer servidor OpenAI-compatible (vLLM, LM Studio, llama.cpp, LocalAI), com tool calling nativo e fallback automático
- **MCP (Model Context Protocol)** — Consuma ferramentas de servidores MCP externos como `BaseTool` nativas, via stdio ou HTTP
- **Human-in-the-loop** — `human_input=True` pausa e devolve o trabalho ao agente com as notas do revisor; revisores plugáveis para rodar fora do terminal
- **Reasoning e Planning** — `Agent(reasoning=True)` planeja e critica o próprio plano antes de agir; `Crew(planning=True)` planeja todas as tarefas antes de começar
- **Manager dedicado** — `manager_agent` / `manager_llm` delega dinamicamente ao especialista certo e devolve o trabalho quando reprova
- **Guardrails com juiz LLM** — Critérios em linguagem natural; a rejeição volta como feedback para o agente corrigir, em vez de repetir o mesmo prompt
- **Multimodal** — `Agent(multimodal=True)` aceita imagens junto do texto
- **Observabilidade** — OpenTelemetry, Langfuse, MLflow e Arize Phoenix; um `trace_id` único costura a execução inteira, inclusive entre threads

### Compatibilidade com CrewAI

O Mangaba implementa as principais primitivas do CrewAI OSS, com a mesma nomenclatura quando aplicável:

- **Crew** — `akickoff()`, `kickoff_for_each()`, `replay(task_id)`, `train()`/`test()`, `before/after_kickoff_callbacks`, `output_log_file`, `usage_metrics`/`token_usage`, `CrewOutput(raw, pydantic, json_dict)`, `function_calling_llm`
- **Task** — `output_pydantic`/`output_json`, `guardrail` (singular), `max_retries`, `depends_on`, `condition`
- **Agent** — `max_iter`, `max_retry_limit`, `kickoff()` direto, `step_callback` por etapa
- **Tools** — `arun()` assíncrono, `cache_function`, `max_retries`, `max_usage_count`
- **Memória multiusuário** — `Memory(user_id=..., namespace=...)` com isolamento por usuário, `remember/recall/forget/remember_many`, recall profundo (`depth="deep"`) e provedor externo `Mem0Memory`
- **Enterprise leve** — Redação de PII (`redact_pii`), auditoria em JSONL com RBAC (`AuditLogger`, `Role`) e estimativa de custo/métricas Prometheus (`estimate_cost`, `CrewOutput.cost()`)

### Funcionalidades consolidadas (desde v3.0)

- **OpenRouter Native Support** — Roteamento dinâmico com fallback automático entre modelos
- **Multi-Provider Interoperability** — Misture agentes de diferentes provedores (ex: Gemini + Llama) na mesma Crew
- **ReAct Reasoning** — Loop Thought, Action, Observation com function calling nativo
- **7 Provedores LLM** — Google Gemini, OpenAI GPT, Anthropic Claude, HuggingFace, OpenRouter, Ollama e servidores OpenAI-compatible
- **4 Processos de Crew** — Sequential, Hierarchical, Parallel (asyncio), Consensual
- **Tool System** — Decorator `@tool`, schemas Pydantic, JSON schema automático para LLM
- **RAG Pipeline** — Document loaders, text splitters, embeddings, vector store, retriever
- **Memória** — Curto prazo (sliding window), longo prazo (SQLite), entidades
- **Guardrails** — Validação de tamanho, filtro de conteúdo, schema validation
- **Observabilidade** — EventBus com mais de 20 tipos de evento, callbacks console/arquivo
- **Workflow Engine** — Pipelines com stages sequenciais, paralelos e condicionais
- **Cache e Retry** — Cache LRU + disco (SQLite), retry com backoff exponencial + fallback automático

## Instalação

```bash
# Núcleo: OpenAI, OpenRouter, Ollama e servidores OpenAI-compatible
pip install mangaba

# SDK do provedor que você for usar
pip install "mangaba[google]"        # Gemini
pip install "mangaba[anthropic]"     # Claude
pip install "mangaba[huggingface]"   # HuggingFace Inference
pip install "mangaba[providers]"     # todos os provedores + tiktoken

# Tudo (provedores, RAG, vector stores, documentos)
pip install "mangaba[all]"

# Desenvolvimento
git clone https://github.com/Mangaba-ai/mangaba_ai.git && cd mangaba_ai
pip install -e ".[dev]"
```

Requer Python 3.10 ou mais novo.

## Quick Start

### Agente simples com ferramenta

```python
from mangaba.core import Agent, Task, Crew, Process, tool
from mangaba.core.types import LLMConfig

@tool
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

researcher = Agent(
    role="Research Analyst",
    goal="Find accurate information",
    backstory="Expert researcher with 10 years of experience",
    tools=[search],
    llm_config=LLMConfig(provider="google", model="gemini-2.5-flash", api_key="sua-chave"),
)

task = Task(
    description="Research the latest AI trends in 2026",
    expected_output="A list of the top 5 trends with explanations",
    agent=researcher,
)

crew = Crew(
    agents=[researcher],
    tasks=[task],
    process=Process.SEQUENTIAL,
)

result = crew.kickoff()
print(result.final_output)
```

### Multi-Provider Crew com fallback

```python
from mangaba.core import Agent, Task, Crew
from mangaba.core.crew import Process
from mangaba.core.types import OpenRouterConfig, LLMConfig

pesquisador = Agent(
    role="Pesquisador",
    goal="Analisar vulnerabilidades",
    llm_config=OpenRouterConfig(
        provider="openrouter",
        model=[
            "google/gemini-2.5-flash",
            "anthropic/claude-3.5-sonnet"
        ],
        api_key="SUA_KEY"
    )
)

revisor = Agent(
    role="Revisor",
    goal="Revisar análise técnica",
    llm_config=LLMConfig(
        provider="hf",
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        api_key="SUA_KEY"
    )
)

task = Task(
    description="Explique buffer overflow",
    expected_output="Análise técnica detalhada",
    agent=pesquisador,
)

review = Task(
    description="Revise a análise",
    expected_output="Pontos fortes e fracos",
    agent=revisor,
)

crew = Crew(
    agents=[pesquisador, revisor],
    tasks=[task, review],
    process=Process.SEQUENTIAL,
)

result = crew.kickoff()
print(result.final_output)
```

### Pipeline com stages

```python
from mangaba import Pipeline, Stage, ParallelStage

pipeline = Pipeline(stages=[
    Stage("research", [research_task]),
    ParallelStage("analysis", [task_a, task_b]),
    Stage("report", [write_task]),
])

result = pipeline.run({"topic": "AI"})
```

### RAG (Retrieval-Augmented Generation)

```python
from mangaba.rag import TextLoader, RecursiveTextSplitter, RAGChain, Retriever
from mangaba.embeddings import OpenAIEmbedding
from mangaba.vectorstores import InMemoryVectorStore

docs = TextLoader("data.txt").load()
chunks = RecursiveTextSplitter(chunk_size=500).split_documents(docs)

embedding = OpenAIEmbedding(api_key="YOUR_KEY")
store = InMemoryVectorStore(embedding)
store.add(chunks)
retriever = Retriever(embedding=embedding, vector_store=store)

from mangaba.core.llm import create_llm_client
llm = create_llm_client(provider="google", api_key="YOUR_KEY")
chain = RAGChain(llm=llm, retriever=retriever)
answer = chain.query("What are the main topics?")
```

### Memória persistente

```python
from mangaba.memory import ShortTermMemory, LongTermMemory

short = ShortTermMemory(max_items=50)
short.add("User asked about Python")

long_mem = LongTermMemory(storage_path="memory.db")
long_mem.add("User prefers concise answers")
results = long_mem.search("preferences")
```

### Guardrails e Output Parsers

```python
from mangaba import Agent, Task
from mangaba.core.guardrails import LengthGuardrail, GuardrailChain
from mangaba.core.output_parsers import JSONOutputParser

task = Task(
    description="List the top 3 programming languages",
    expected_output="JSON with name and reason",
    agent=agent,
    guardrails=[LengthGuardrail(max_length=2000)],
    output_parser=JSONOutputParser(),
)
```

### Comunicação entre agentes (protocolo A2A interno)

```python
from protocols.a2a import A2AProtocol, A2AMessage

protocolo = A2AProtocol()

# Enviar mensagem de um agente para outro
msg = A2AMessage(
    sender="pesquisador",
    recipient="revisor",
    content="Análise de vulnerabilidade concluída",
    msg_type="request"
)
protocolo.send(msg)

# Broadcast para todos os agentes
protocolo.broadcast(A2AMessage(
    sender="manager",
    recipient="*",
    content="Iniciando nova tarefa",
    msg_type="broadcast"
))
```

### Vector store com ChromaDB

```python
from mangaba.vectorstores import ChromaVectorStore, create_vectorstore
from mangaba.embeddings import OpenAIEmbedding

embedding = OpenAIEmbedding(api_key="KEY")

# Via factory
store = create_vectorstore("chroma", embedding=embedding, persist_directory="./chroma_db")

# Adicionar e buscar
store.add(chunks)
results = store.similarity_search("machine learning", k=5)
```

## Flows — orquestração orientada a eventos

Crews coordenam agentes; Flows coordenam tudo o mais. Cada método reage ao
resultado de outro, o estado é tipado, e o progresso pode ser persistido para
retomar de onde parou.

```python
from pydantic import BaseModel
from mangaba import Flow, start, listen, router, persist, and_

class Estado(BaseModel):
    texto: str = ""
    risco: str = ""

@persist                              # checkpoint a cada passo
class Triagem(Flow):
    state_model = Estado

    @start()
    def coletar(self):
        self.state.texto = "contrato para revisar"
        return self.state.texto

    @listen(coletar)
    def analisar(self, texto):
        return "alto" if "contrato" in texto else "baixo"

    @router(analisar)
    def rotear(self, risco):
        self.state.risco = risco
        return "juridico" if risco == "alto" else "arquivo"

    @listen("juridico")
    def escalar(self):
        return "enviado ao jurídico"

    @listen("arquivo")
    def arquivar(self):
        return "arquivado"

flow = Triagem()
print(flow.kickoff())        # "enviado ao jurídico"
print(flow.usage_metrics)    # tokens somados de tudo que rodou dentro
flow.plot("triagem.html")    # gráfico de execução, HTML autocontido
```

`and_(a, b)` dispara só quando ambos terminam, `or_(a, b)` quando qualquer um
terminar. Métodos podem ser `async def`. Para retomar após uma queda:

```python
resultado = Triagem().resume("6f1c...")   # pula os passos já concluídos
ramo = Triagem().fork("6f1c...")          # ramifica a partir do checkpoint
```

## Knowledge — fundamentar respostas em documentos

Diferente da memória (o que o agente viveu), a Knowledge é o que ele pode
consultar. Aceita PDF, DOCX, Excel, JSON, CSV, URL e diretórios inteiros.

```python
from mangaba import Agent, Knowledge, PDFKnowledgeSource, DirectoryKnowledgeSource
from mangaba.embeddings import OpenAIEmbedding

conhecimento = Knowledge(
    embedding=OpenAIEmbedding(api_key="..."),
    sources=[
        PDFKnowledgeSource(file_path="normas/nr12.pdf"),
        DirectoryKnowledgeSource(path="politicas/", recursive=True),
    ],
    results_limit=3,
    score_threshold=0.35,
)

agente = Agent(role="Auditor", goal="Verificar conformidade",
               backstory="Especialista em segurança do trabalho",
               knowledge=conhecimento)
```

Passe `knowledge=` para a `Crew` e todos os agentes que não têm base própria
recebem a mesma.

## Memória com recall semântico

A classe `Memory` pontua cada lembrança por similaridade, recência e
importância — não só por parecido.

```python
from mangaba import Memory, MemoryScope

memoria = Memory(embedding=embedding, db_path=".mangaba/memoria.db")
memoria.add("O cliente prefere respostas curtas", metadata={"importance": 0.9})
memoria.add_interaction("Qual meu plano?", "Você está no plano Pro anual.")

memoria.consolidate()                    # funde duplicatas
memoria.search("preferências", scope=MemoryScope.AGENT)

agente = Agent(role="Suporte", goal="Atender bem", backstory="...", memory=memoria)
```

As classes antigas (`ShortTermMemory`, `LongTermMemory`, `EntityMemory`)
continuam funcionando sem mudanças.

Para produção multiusuário, isole por usuário e use recall profundo:

```python
from mangaba.memory import Memory
from mangaba.memory.external import Mem0Memory

memoria = Memory(embedding=embedding, user_id="cliente-123", namespace="suporte")
memoria.remember("O cliente prefere respostas curtas")
memoria.recall("preferências do cliente", depth="deep")

# Memória externa (requer: pip install mem0ai)
externa = Mem0Memory(config={"user_id": "cliente-123"})
crew = Crew(agents=[...], tasks=[...], memory=externa)
```

## Human-in-the-loop

`human_input=True` pausa de verdade: o revisor aprova, reescreve, ou devolve
com notas — e as notas voltam para o agente corrigir.

```python
from mangaba import Task, CallbackHumanInput, HumanFeedback

def revisar_no_slack(descricao, saida, papel):
    resposta = slack.perguntar(f"{papel} respondeu:\n{saida}")
    return HumanFeedback(approved=resposta == "ok", feedback=resposta)

task = Task(
    description="Redigir a resposta ao cliente",
    expected_output="Um e-mail pronto para enviar",
    agent=redator,
    human_input=True,
    human_input_handler=CallbackHumanInput(revisar_no_slack),
    max_human_iterations=3,
)
```

Sem handler, usa o terminal — e aprova sozinho quando não há terminal, para
não travar execuções automatizadas.

## Reasoning, Planning e manager dedicado

```python
# O agente planeja e critica o próprio plano antes de agir
agente = Agent(role="Analista", goal="...", backstory="...",
               reasoning=True, max_reasoning_attempts=3)

# A crew planeja todas as tarefas antes de começar, e um manager
# dedicado escolhe quem faz o quê — e reprova o que não serve
crew = Crew(
    agents=[pesquisador, analista, redator],
    tasks=[t1, t2, t3],
    process=Process.HIERARCHICAL,
    planning=True,
    manager_llm=create_llm_client(provider="openai", api_key="..."),
)
```

## Guardrails com juiz LLM

```python
from mangaba import LLMGuardrail, FunctionGuardrail

task = Task(
    description="Resumir o relatório",
    expected_output="Um resumo com fontes",
    agent=agente,
    guardrails=[LLMGuardrail("Deve citar ao menos duas fontes com URL", llm=llm)],
    guardrail_max_retries=3,   # a rejeição volta como feedback, não como repetição
)
```

## CLI

```bash
mangaba create crew pesquisa   # esqueleto com agents.yaml e tasks.yaml
cd pesquisa && cp .env.example .env
mangaba run --input topic="energia solar em Alagoas"

mangaba test -n 3              # nota de qualidade por tarefa e por agente
mangaba train -n 5             # loop de feedback humano, salvo em pickle
mangaba chat                   # REPL contra um agente
mangaba config                 # mostra provedor/modelo (nunca a chave)
mangaba reset-memories --all
mangaba replay -t <task_id>    # re-executa a partir de uma tarefa
mangaba install                # instala as dependências do projeto
```

## MCP — ferramentas de servidores externos

```python
from mangaba import Agent, MCPClient

with MCPClient(command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/dados"]) as mcp:
    agente = Agent(role="Analista", goal="...", backstory="...",
                   tools=mcp.get_tools())
```

Funciona por stdio ou HTTP, com o SDK oficial `mcp` quando disponível e um
transporte próprio sem dependências como fallback.

## A2A — interoperar com agentes de outros frameworks

O protocolo aberto Agent2Agent. Não confundir com `protocols/a2a.py`, que é o
barramento interno de mensagens entre agentes do próprio processo.

```python
from mangaba import A2AServer, A2AClient, agent_card_for

# Expor um agente (ou uma Crew) para o mundo
servidor = A2AServer(agente, host="127.0.0.1", port=0)
servidor.start()
print(agent_card_for(agente).model_dump_json(by_alias=True, indent=2))

# Consumir um agente remoto — de qualquer framework — como ferramenta local
cliente = A2AClient("https://parceiro.exemplo/agent")
meu_agente = Agent(role="Coordenador", goal="...", backstory="...",
                   tools=[cliente.as_tool()])
```

O card é servido em `/.well-known/agent.json`; as tarefas transitam por
`submitted`, `working`, `completed` ou `failed`.

## Ferramentas incluídas

| Ferramenta | O que faz |
|---|---|
| `ScrapeWebsiteTool` | Baixa uma página e extrai o texto legível |
| `HTTPRequestTool` | Chamada REST genérica |
| `DocumentSearchTool` | Busca semântica dentro de um arquivo (PDF, DOCX, Excel) |
| `FileSearchTool` | Busca literal ou regex numa árvore de diretórios |
| `SQLQueryTool` | SQL somente leitura em SQLite ou PostgreSQL |
| `CodeInterpreterTool` | Executa Python — desligado por padrão |
| `MCPClient.get_tools()` | Ferramentas vindas de servidores MCP externos |
| `A2AClient.as_tool()` | Um agente remoto como ferramenta local |

Resolva qualquer uma pelo nome curto no YAML (`http_request`, `sql_query`, …)
ou via `ToolRegistry`.

### Antes de usar em produção

- **`CodeInterpreterTool` executa código escrito pelo modelo.** Exige
  `enabled=True`; usa Docker isolado quando disponível. `unsafe_mode=True`
  roda direto no host, com todos os privilégios do processo — inclusive acesso
  a arquivos e variáveis de ambiente com credenciais.
- **`A2AServer` não tem TLS nem autenticação.** O padrão é escutar em
  `127.0.0.1`. Quem alcançar a porta faz seu agente trabalhar e gasta seu
  orçamento de LLM. Coloque atrás de um proxy autenticado antes de expor.
- **`A2AClient.as_tool()` traz a resposta de um agente de terceiros para
  dentro do seu contexto** — é um canal de prompt injection. Aponte só para
  agentes em que você confia.
- **`HTTPRequestTool` / `ScrapeWebsiteTool`** recusam esquemas que não sejam
  `http(s)`, mas não bloqueiam endereços privados por padrão. Use
  `block_private_hosts=True` contra SSRF e `allowed_domains=[...]` para fixar
  os destinos.
- **`SQLQueryTool`** valida a instrução, abre a conexão em modo somente
  leitura e sempre usa parâmetros — ainda assim, dê a ele um usuário de banco
  com privilégio mínimo.
- **`FileSearchTool`** sem `root_dir` lê qualquer coisa que o processo possa
  ler. Sempre passe `root_dir` quando o caminho puder vir do modelo.

## Observabilidade

```python
from mangaba import auto_configure_from_env, OpenTelemetryCallback, configure_observability

auto_configure_from_env()                          # liga o que estiver no ambiente
configure_observability(OpenTelemetryCallback())   # ou explicitamente
```

Integra com OpenTelemetry (OTLP), Langfuse, MLflow e Arize Phoenix. Cada
execução recebe um `trace_id` que sobrevive inclusive às threads de tarefas
paralelas, então a crew inteira aparece como um trace só.

Recursos adicionais para produção:

```python
from mangaba import redact_pii, AuditLogger, AuditCallback, estimate_cost

limpo = redact_pii("contato joao@empresa.com, CPF 123.456.789-00")

logger = AuditLogger(path=".mangaba/audit.jsonl", actor="api")
configure_observability(AuditCallback(logger))

custo_usd = estimate_cost(result.token_usage, model="gpt-4o-mini")
print(result.cost("gpt-4o-mini"))   # estimativa direto no CrewOutput
print(result.prometheus())          # métricas em formato Prometheus
```

## Vector Stores

| Store | Persistência | Ideal para |
|---|---|---|
| `InMemoryVectorStore` | Volátil (RAM) | Testes e protótipos |
| `ChromaVectorStore` | Disco (ChromaDB) | Aplicações standalone |
| `PostgresVectorStore` | PostgreSQL + pgvector | Produção, dados relacionais |
| `RedisVectorStore` | Redis + RediSearch | Alta performance, caching |
| `SQLiteVectorStore` | SQLite local | Embeddings simples, sem infra |

Todas implementam `BaseVectorStore` e são intercambiáveis via `create_vectorstore()`.

## Protocolos de Comunicação

### A2A (Agent-to-Agent)

Mensageria direta entre agentes com suporte a request/response e broadcast:

```python
from protocols.a2a import A2AProtocol, A2AMessage

protocol = A2AProtocol()
protocol.send(A2AMessage(sender="agent_a", recipient="agent_b", content="..."))
```

### MCP (Multi-Context Protocol)

Compartilhamento de contexto hierárquico entre agentes com prioridade, tags e busca por relevância:

```python
from protocols.mcp import MCPProtocol, MCPContext

mcp = MCPProtocol()
ctx = MCPContext(content="Dados da análise", priority=8, tags=["analise", "vulnerabilidade"])
mcp.share_context("sessao_1", ctx)
resultados = mcp.query_context("sessao_1", "vulnerabilidade")
```

## Prompt Templates

```python
from mangaba.core.llm.prompt_templates import PromptTemplate, ChatPromptTemplate, SystemPromptBuilder

# Template simples
template = PromptTemplate("Responda em {idioma}: {pergunta}")
result = template.format(idioma="português", pergunta="o que é IA?")

# Template de chat
chat = ChatPromptTemplate([
    ("system", "Você é um especialista em {topico}"),
    ("user", "{pergunta}"),
])
messages = chat.format_messages(topico="segurança", pergunta="O que é XSS?")

# Builder pattern
builder = SystemPromptBuilder()
builder.add_role("Analista de Segurança")
builder.add_context("Você trabalha com pentest há 10 anos")
builder.add_instruction("Responda em markdown")
prompt = builder.build()
```

## Padrões de Projeto

O Mangaba aplica padrões GoF de forma consistente em toda a base de código:

| Padrão | Onde é usado |
|---|---|
| Factory | `create_llm_client()` / `create_vectorstore()` — instancia provedores por nome |
| Abstract Factory | `BaseLLMProvider` / `BaseVectorStore` — interface comum; cada provider é uma família concreta |
| Facade | `LLMClient` — esconde a complexidade dos provedores atrás de uma API uniforme |
| Decorator | `@tool` — converte funções Python em `BaseTool` com schema automático |
| Composite | `Crew` / `Toolkit` — agrega múltiplos agentes/tarefas/ferramentas como unidade |
| Strategy | `Process` (sequential/hierarchical/parallel/consensual); providers como strategies |
| Observer | `EventBus` + callbacks (`ConsoleCallback`, `FileCallback`) |
| Template Method | `BaseLLMProvider.generate/stream/generate_with_tools` — subclasses implementam os passos |
| Chain of Responsibility | `GuardrailChain` — passa o output por validadores em sequência |
| Command | `Task` — encapsula instrução, agente e ferramentas |
| Iterator | `stream()` — retorna `Iterator[str]` token a token |
| Pipes e Filters | `Pipeline` com `Stage`, `ParallelStage` e `ConditionalStage` |
| Builder | `SystemPromptBuilder` — constrói system prompts passo a passo |
| Singleton | `EventBus` — instância única de barramento de eventos |

## Arquitetura

```
mangaba/
├── core/                   # Núcleo do framework
│   ├── agent.py                # Agent com ReAct reasoning
│   ├── task.py                 # Tasks com guardrails e retry
│   ├── crew.py                 # Orquestração (4 processos)
│   ├── workflow.py             # Pipeline engine
│   ├── reasoning.py            # ReAct loop (Think, Act, Observe)
│   ├── planner.py              # Decomposição automática de tarefas
│   ├── guardrails.py           # LengthGuardrail, ContentFilter, Schema
│   ├── output_parsers.py       # JSON, Pydantic, List, Markdown
│   ├── types.py                # Tipos Pydantic v2 (LLMConfig, AgentState...)
│   ├── exceptions.py           # Hierarquia de exceções
│   ├── events.py               # EventBus (tipos de evento)
│   └── llm/                    # Engine LLM multi-provider
│       ├── client.py               # Providers + OpenRouter + fallback
│       ├── retry.py                # Retry com backoff exponencial
│       ├── cache.py                # LRU (memória) + SQLite (disco)
│       ├── token_counter.py        # TokenCounter + UsageTracker
│       └── prompt_templates.py     # PromptTemplate, ChatPromptTemplate, SystemPromptBuilder
├── tools/                  # Sistema de ferramentas
│   ├── base.py                 # BaseTool + JSON schema automático
│   ├── decorator.py            # @tool decorator
│   ├── toolkit.py              # BaseToolkit, FileToolkit, WebToolkit
│   ├── file_tools.py           # FileReader, FileWriter, DirectoryList
│   ├── web_search.py           # Serper, DuckDuckGo
│   ├── math_tools.py           # Calculadora segura (AST)
│   └── text_tools.py           # TextSplitter, WordCounter
├── memory/                 # Sistema de memória
│   ├── base.py                 # BaseMemory ABC
│   ├── short_term.py           # Sliding window (deque)
│   ├── long_term.py            # SQLite + embeddings opcionais
│   ├── entity.py               # Memória de entidades
│   ├── unified.py              # Memory: recall composto + consolidação
│   └── external.py             # Mem0Memory: provedor externo de memória
├── embeddings/             # Provedores de embedding
│   ├── base.py                 # BaseEmbedding ABC
│   ├── openai_embed.py         # text-embedding-3-small
│   ├── google_embed.py         # text-embedding-004
│   └── huggingface_embed.py    # Sentence-transformers
├── vectorstores/           # Armazenamento vetorial
│   ├── base.py                 # BaseVectorStore ABC
│   ├── factory.py              # create_vectorstore() + register_store()
│   ├── in_memory.py            # Cosine similarity (numpy)
│   ├── chroma_db.py            # ChromaDB
│   ├── postgres.py             # PostgreSQL + pgvector
│   ├── redis.py                # Redis + RediSearch
│   └── sqlite.py               # SQLite vector store
├── rag/                    # Pipeline RAG
│   ├── document.py             # Modelo de documento
│   ├── loaders.py              # Text, CSV
│   ├── splitters.py            # RecursiveTextSplitter
│   ├── retriever.py            # Embedding + vector store
│   └── chain.py                # RAGChain com fontes
├── flows/                  # Orquestração orientada a eventos
│   ├── flow.py                 # Flow, @start/@listen/@router/@persist, and_/or_
│   ├── state.py                # Estado livre (dict) ou tipado (Pydantic)
│   ├── persistence.py          # Checkpoints em SQLite, resume e fork
│   └── visualization.py        # plot(): grafo de execução em HTML
├── knowledge/              # Base de conhecimento (RAG de documentos)
│   ├── knowledge.py            # Knowledge: ingestão, query, threshold
│   └── sources.py              # PDF, DOCX, Excel, JSON, CSV, URL, diretório
├── observability/          # Tracing externo e governança
│   ├── otel.py                 # OpenTelemetry (OTLP)
│   ├── langfuse.py             # Langfuse
│   ├── mlflow.py               # MLflow
│   ├── phoenix.py              # Arize Phoenix
│   ├── pii.py                  # Redação de PII
│   ├── audit.py                # Auditoria JSONL + RBAC
│   └── metrics.py              # Custo estimado + Prometheus
├── training/               # Treino e avaliação
│   ├── trainer.py              # mangaba train — feedback humano iterativo
│   └── evaluator.py            # mangaba test — nota 1–10 por tarefa
├── cli/                    # Interface de linha de comando
│   ├── main.py                 # create/run/test/train/chat/config/reset/replay/install
│   └── templates/              # Esqueletos de projeto gerados
├── callbacks/              # Observabilidade local
│   ├── console.py              # Print formatado de eventos
│   └── file.py                 # Log JSONL
├── __init__.py              # API pública do pacote
├── config.py                # Config system (leitura .env)
├── config_loader.py         # agents.yaml / tasks.yaml → Agent/Task/Crew
└── exceptions.py            # (legado)

protocols/                 # Protocolos de comunicação entre agentes
├── a2a.py                     # Agent-to-Agent protocol
└── mcp.py                     # Multi-Context Protocol

utils/                     # Utilitários
└── logger.py                  # Logger colorido (Loguru)

docs/                       # Documentação completa
├── API-Reference.md
├── CHANGELOG.md
├── Core-Components.md
├── Events.md
├── Guardrails.md
├── LLM-Providers.md
├── Memory.md
├── RAG.md
├── Tools.md
├── Vector-Stores.md
├── Workflows.md
├── Getting-Started.md
├── CURSO_BASICO.md
├── Examples.md
├── FAQ.md
└── ...

examples/                  # Exemplos práticos
├── basic_example.py
├── crew_example.py
├── finance_example.py
├── legal_example.py
├── medical_example.py
├── marketing_example.py
├── text_analysis_example.py
├── translation_example.py
├── document_analysis_example.py
├── vectorstores_example.py
└── ...
```

## Processos de Crew

| Processo | Descrição | Uso |
|---|---|---|
| `SEQUENTIAL` | Tarefas executadas em ordem, uma após a outra | Workflows lineares |
| `HIERARCHICAL` | Manager delega e revisa cada entrega | Equipes com líder |
| `PARALLEL` | Tarefas executadas concorrentemente (asyncio) | Tarefas independentes |
| `CONSENSUAL` | Todos os agentes executam cada tarefa, resultado sintetizado | Decisões críticas |

## Provedores LLM

| Provedor | Function Calling | Streaming | Modelo padrão |
|---|---|---|---|
| OpenRouter | Nativo + fallback | Sim | Roteamento multi-modelo |
| Google Gemini | Nativo | Sim | `gemini-2.5-flash` |
| OpenAI | Nativo | Sim | `gpt-4o-mini` |
| Anthropic | Nativo (tool_use) | Sim | `claude-haiku-4-5-20251001` |
| HuggingFace | Nativo (11 modelos) / via prompt (14 modelos) | Sim, via `chat_completion` | `mistralai/Mistral-7B-Instruct-v0.3` |
| Ollama | Nativo + fallback por prompt | Sim | Roda 100% local, sem API key |
| OpenAI-compatible | Nativo | Sim | vLLM, LM Studio, llama.cpp, LocalAI |

### Modelos locais

Nem Ollama nem os servidores OpenAI-compatible exigem API key:

```python
from mangaba import create_llm_client, list_ollama_models

print(list_ollama_models())          # o que já está instalado localmente

llm = create_llm_client(provider="ollama", model="qwen2.5:7b")
llm = create_llm_client(provider="vllm", model="meta-llama/Llama-3.1-8B-Instruct",
                        base_url="http://localhost:8000/v1")
```

Configure via variáveis de ambiente:

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=sua_chave
# ou OPENAI_API_KEY, ANTHROPIC_API_KEY, HUGGINGFACE_API_KEY, OPENROUTER_API_KEY
```

### Modelos open-source (HuggingFace)

O provider HuggingFace usa `chat_completion` (OpenAI-compatible) com detecção automática de tool calling: modelos com function calling nativo recebem `tools=[...]` direto na API; os demais usam prompt injection como fallback. Use `hf_model_supports_tools(model_id)` para verificar.

O Mangaba inclui um catálogo de 28 modelos open-source disponíveis via HuggingFace Inference API, organizados por categoria:

```python
from mangaba import list_huggingface_models, HF_OPEN_MODELS

# Listar todos os modelos
todos = list_huggingface_models()

# Filtrar por categoria: general, code, reasoning, embedding
modelos_codigo  = list_huggingface_models(category="code")
modelos_reason  = list_huggingface_models(category="reasoning")
modelos_embed   = list_huggingface_models(category="embedding")

# Via classe do provider
from mangaba.core.llm.client import HuggingFaceLLMProvider
HuggingFaceLLMProvider.list_models(category="general")
```

| Categoria | Modelos incluídos |
|---|---|
| general (19) | Mistral 7B/Mixtral 8x7B/8x22B, Llama 3/3.1/3.2, Qwen 2.5, Phi-3/3.5, Gemma 2 |
| code (4) | StarCoder2 15B, Qwen 2.5 Coder 7B/32B, DeepSeek Coder 33B |
| reasoning (2) | DeepSeek R1 Distill Qwen 7B, DeepSeek R1 Distill Llama 70B |
| embedding (3) | BGE-M3, all-MiniLM-L6-v2, Multilingual E5 Large |

```python
from mangaba import hf_model_supports_tools

hf_model_supports_tools("mistralai/Mistral-7B-Instruct-v0.3")  # True  — nativo
hf_model_supports_tools("google/gemma-2-9b-it")                # False — prompt injection
```

## Dependências

Núcleo:

- `pydantic>=2.0.0` — Validação de tipos
- `openai>=1.6.0` — OpenAI, OpenRouter, Ollama e servidores OpenAI-compatible
- `requests>=2.25.0` — HTTP client
- `python-dotenv>=0.19.0` — Leitura de `.env`

Opcionais:

- `google-generativeai>=0.3.0` — Google Gemini (`pip install mangaba[google]`)
- `anthropic>=0.20.0` — Anthropic Claude (`pip install mangaba[anthropic]`)
- `huggingface-hub>=0.20.0` — HuggingFace (`pip install mangaba[huggingface]`)
- `tiktoken>=0.5.0` — Contagem exata de tokens OpenAI (`pip install mangaba[tokenizer]`)

- `numpy>=1.24.0` — RAG e embeddings (`pip install mangaba[rag]`)
- `sentence-transformers>=2.2.0` — Embeddings HF (`pip install mangaba[embeddings]`)
- `duckduckgo-search>=3.9.0` — Busca web (`pip install mangaba[tools]`)
- `redis>=5.0.0` — Redis vector store (`pip install mangaba[redis]`)
- `psycopg[binary]>=3.1.0` — Postgres vector store (`pip install mangaba[postgres]`)
- `chromadb>=0.4.0` — ChromaDB vector store (`pip install mangaba[chroma]`)
- `pypdf`, `python-docx`, `openpyxl`, `beautifulsoup4` — Loaders de documentos (`pip install mangaba[documents]`)
- `pyyaml>=6.0` — Projetos declarativos da CLI (`pip install mangaba[yaml]`)
- `mcp>=1.0.0` — SDK oficial do MCP; há fallback sem dependência (`pip install mangaba[mcp]`)
- OpenTelemetry / Langfuse / MLflow / Phoenix — Tracing (`pip install mangaba[otel]`, `[langfuse]`, `[mlflow]`, `[phoenix]`, ou `[observability]`)
- **Tudo:** `pip install mangaba[all]`

Modelos locais (Ollama, vLLM, LM Studio, llama.cpp, LocalAI) não precisam de
nenhum extra — usam o cliente `openai`, que já é dependência do núcleo.

## Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Só os que não tocam a rede
python -m pytest -m "not network"

# Com cobertura (opt-in)
python -m pytest tests/ --cov=mangaba --cov-report=term-missing
```

### Testes contra modelo real

`tests/test_gateway_integration.py` aponta o framework para o
Mangaba Gateway — modelos GGUF locais de verdade — em vez de stubs. Cobre
agente, crew, knowledge com embeddings reais, memória, guardrail com juiz LLM,
revisão humana e propagação de trace.

```bash
python -m pytest tests/test_gateway_integration.py -v
```

O arquivo inteiro é pulado automaticamente quando o gateway está fora do ar,
então rodar offline continua verde.

## Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Add nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

MIT License
