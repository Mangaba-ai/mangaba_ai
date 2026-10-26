# 🤖 LLM Providers

O Mangaba AI suporta 5 providers de LLM com interface unificada, function calling, streaming, caching e retry.

---

## Providers Suportados

| Provider | Alias(es) | Model Default | Function Calling | Streaming |
|---|---|---|---|---|
| **Google Gemini** | `google`, `gemini` | `gemini-2.5-flash` | ✅ Nativo | ✅ |
| **OpenAI** | `openai` | `gpt-4o-mini` | ✅ Nativo | ✅ |
| **Anthropic** | `anthropic`, `claude` | `claude-sonnet-5-5` | ✅ Tool Use | ✅ |
| **HuggingFace** | `huggingface`, `hf` | `meta-llama/Llama-3.1-8B-Instruct` | ⚠️ Prompt-based | ✅ |
| **OpenRouter** | `openrouter` | Varia | ✅ Via proxy | ✅ |

---

## Factory: `create_llm_client`

```python
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

# Configuração via LLMConfig
llm_config = LLMConfig(
    provider="google",
    model="gemini-2.5-flash",
    api_key="YOUR_API_KEY",
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
```

### LLMConfig

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `provider` | `str` | `"google"` | Nome do provider (normaliza aliases automaticamente) |
| `model` | `str | List[str]` | `"gemini-2.5-flash"` | Nome do modelo ou lista (OpenRouter) |
| `api_key` | `str` | `None` | API key |
| `temperature` | `float` | `0.7` | Criatividade (0-2) |
| `max_tokens` | `int` | `1024` | Máximo tokens de output |
| `top_p` | `float` | `1.0` | Top-p sampling (0-1) |
| `stop_sequences` | `List[str]` | `None` | Sequências de parada |
| `timeout` | `int` | `60` | Timeout em segundos |
| `base_url` | `str` | `None` | URL customizada |

### OpenRouterConfig

```python
from mangaba.core.types import OpenRouterConfig

config = OpenRouterConfig(
    api_key="OPENROUTER_API_KEY",
    model=["google/gemini-2.5-flash", "anthropic/claude-3.5-sonnet"],  # Fallback
    site_name="My App",
    site_url="https://myapp.com",
    route="fallback",
)
```

### Parâmetros (herdados de LLMConfig)

### Listar providers

```python
from mangaba.core.llm import get_supported_providers
print(get_supported_providers())
# ('anthropic', 'claude', 'gemini', 'google', 'hf', 'huggingface', 'openai', 'openrouter')
```

---

## LLMClient

O `LLMClient` é a interface unificada para todos os providers:

```python
from mangaba.core.llm import LLMClient

client = LLMClient(
    provider="google",
    api_key="KEY",
    model="gemini-2.5-flash",
)

# Geração simples
response = client.generate("What is AI?")
print(response.text)

# Com ferramentas
response = client.generate_with_tools(
    messages=[{"role": "user", "content": "Calculate 15% of 250"}],
    tools=[calculator_tool],
)

# Streaming
for chunk in client.stream("Write a poem"):
    print(chunk, end="")
```

### LLMResponse

```python
response.text            # Texto da resposta
response.tool_calls      # List[ToolCall] — chamadas de ferramentas
response.has_tool_calls  # bool — há tool calls?
response.finish_reason   # FinishReason enum
response.usage           # TokenUsage — contagem de tokens
response.model           # Nome do modelo usado
```

---

## Google Gemini

```python
from mangaba.core.llm import create_llm_client

llm = create_llm_client(
    provider="google",
    api_key="GOOGLE_API_KEY",
    model="gemini-2.5-flash",
    temperature=0.7,
    max_output_tokens=8192,
)
```

### Models Disponíveis

| Model | Context | Uso |
|---|---|---|
| `gemini-2.5-flash` | 1M tokens | Geral, rápido |
| `gemini-2.5-pro` | 1M tokens | Raciocínio complexo |
| `gemini-1.5-flash` | 1M tokens | Custo-eficiente |

---

## OpenAI

```python
llm = create_llm_client(
    provider="openai",
    api_key="OPENAI_API_KEY",
    model="gpt-4o-mini",
    temperature=0.7,
    max_output_tokens=4096,
)
```

### Models Disponíveis

| Model | Context | Uso |
|---|---|---|
| `gpt-4o-mini` | 128K | Geral, rápido |
| `gpt-4o` | 128K | Raciocínio avançado |
| `gpt-4-turbo` | 128K | Alta qualidade |

---

## Anthropic Claude

```python
llm = create_llm_client(
    provider="anthropic",
    api_key="ANTHROPIC_API_KEY",
    model="claude-sonnet-5-5",
    temperature=0.7,
    max_output_tokens=8192,
)
```

### Models Disponíveis

| Model | Context | Uso |
|---|---|---|
| `claude-sonnet-5-5` | 200K | Equilíbrio custo/performance |
| `claude-opus-4-8` | 200K | Máxima qualidade |
| `claude-haiku-3-5` | 200K | Rápido, eficiente |

---

## HuggingFace

```python
llm = create_llm_client(
    provider="huggingface",
    api_key="HF_TOKEN",
    model="meta-llama/Llama-3.1-8B-Instruct",
)
```

> ⚠️ **Nota:** Function calling em HuggingFace é emulado via prompt engineering, não nativo.

### Listar modelos HuggingFace

```python
from mangaba.core.llm import list_huggingface_models, hf_model_supports_tools

models = list_huggingface_models()
print(f"Modelo suporta tools: {hf_model_supports_tools('meta-llama/Llama-3.1-8B-Instruct')}")
```

---

## OpenRouter

OpenRouter permite acessar múltiplos modelos via uma única API:

```python
from mangaba.core.types import OpenRouterConfig
from mangaba.core.llm import create_llm_client

llm = create_llm_client(
    provider="openrouter",
    api_key="OPENROUTER_API_KEY",
    model="openai/gpt-4o-mini",
    site_name="My App",
    site_url="https://myapp.com",
    route="fallback",  # Fallback entre providers
)
```

---

## Caching

Cache de respostas LLM para evitar chamadas redundantes:

```python
from mangaba.core.llm import LLMCache, InMemoryCache, DiskCache

# Cache em memória
cache = InMemoryCache(ttl=3600)  # 1 hora

# Cache em disco
cache = DiskCache(cache_dir="./llm_cache", ttl=86400)  # 24 horas

# Usar com client
client = LLMClient(
    provider="google",
    api_key="KEY",
    model="gemini-2.5-flash",
    cache=cache,
)
```

---

## Retry

Retry automático com backoff exponencial:

```python
from mangaba.core.llm import with_retry

# Aplicar retry a uma função
@with_retry(max_retries=3, backoff_factor=2)
def my_llm_call():
    return client.generate("Query")
```

---

## Token Tracking

```python
from mangaba.core.llm import TokenCounter, UsageTracker

tracker = UsageTracker()

client = LLMClient(
    provider="google",
    api_key="KEY",
    model="gemini-2.5-flash",
    usage_tracker=tracker,
)

# Após chamadas
print(f"Total tokens: {tracker.total_tokens}")
print(f"Total custo: ${tracker.estimated_cost():.4f}")
print(f"Chamadas: {len(tracker.history)}")
```

---

## Prompt Templates

```python
from mangaba.core.llm import PromptTemplate, ChatPromptTemplate, SystemPromptBuilder

# Template simples
template = PromptTemplate(
    template="Answer this question about {topic}: {question}",
    input_variables=["topic", "question"],
)
prompt = template.format(topic="AI", question="What is machine learning?")

# Chat template
chat = ChatPromptTemplate()
chat.add_system("You are a helpful assistant")
chat.add_user("Explain {concept}")
messages = chat.format_messages(concept="RAG")

# System prompt builder
builder = SystemPromptBuilder()
builder.set_role("Expert Data Scientist")
builder.set_goal("Analyze data and provide insights")
builder.add_instruction("Always cite sources")
prompt = builder.build()
```
