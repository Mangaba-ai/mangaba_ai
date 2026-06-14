# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed
- Repository restructured under `refactor/core-restructure` branch
- Added `Makefile` with targets for install, lint, test, docker, build, and CI

---

## [3.3.0] - 2026-05-01

### Added
- PostgreSQL vector store backend using `pgvector` (`psycopg[binary]`)
- Redis memory backend via `redis-stack` Docker image
- `docker-compose.vectorstores.yml` to spin up Redis and Postgres locally
- Optional dependency groups: `redis`, `postgres`, `chroma`

### Removed
- Deprecated `VectorStoreFactory` class
- Deprecated `PostgresVectorStore` legacy class (replaced by new backend)

### Changed
- Vector store backends consolidated under `mangaba/vectorstores/`

---

## [3.2.0] - 2026-04-25

### Added
- **OpenRouter provider** — unified access to 200+ models via OpenRouter API
- `OpenRouterLLMProvider` with streaming, tool calling, and token usage support
- `OPENROUTER_API_KEY` environment variable support

---

## [3.1.1] - 2026-04-22

### Added
- Native tool calling for 11 HuggingFace models with automatic detection:
  - Native: Mistral 7B, Mixtral 8x7B/8x22B/Nemo, Llama 3.1 8B/70B/405B, Qwen 2.5 7B/72B, Qwen 2.5 Coder 7B/32B
  - Prompt-based fallback: Llama 3.0/3.2, Gemma 2, Phi-3, StarCoder2, DeepSeek Coder/R1
- `hf_model_supports_tools(model_id)` — public function to check native tool calling support
- `_HF_NATIVE_TOOL_MODELS` — internal index of natively-capable models
- `tool_calling` field corrected across `HF_OPEN_MODELS` catalog

### Changed
- `HuggingFaceLLMProvider.generate_with_tools()` — dispatches to native or prompt-injection based on model

---

## [3.1.0] - 2026-04-22

### Added
- HuggingFace open-source model catalog (`HF_OPEN_MODELS`) with 28 curated models:
  - 19 general: Mistral, Mixtral, Llama 3/3.1/3.2, Qwen 2.5, Phi-3/3.5, Gemma 2
  - 4 code: StarCoder2 15B, Qwen 2.5 Coder 7B/32B, DeepSeek Coder 33B
  - 2 reasoning: DeepSeek R1 Distill Qwen 7B and Llama 70B
  - 3 embedding: BGE-M3, all-MiniLM-L6-v2, Multilingual E5 Large
- `list_huggingface_models(category=None)` — public function to list/filter by category
- `HuggingFaceLLMProvider.list_models(category=None)` — classmethod on provider

### Changed
- `HuggingFaceLLMProvider` migrated from `text_generation` (legacy) to `chat_completion` (OpenAI-compatible):
  - `generate()` — uses `chat_completion` with `system_prompt` and `TokenUsage`
  - `stream()` — real token-by-token streaming via `chat_completion(stream=True)`
- Default HuggingFace model updated to `mistralai/Mistral-7B-Instruct-v0.3`

### Fixed
- HuggingFace streaming was broken for modern instruction models (Llama 3, Mistral v0.3, Qwen 2.5)

---

## [3.0.0] - 2026-03-15

### Added
- Long-term and short-term memory modules (`mangaba/memory/`)
- RAG pipeline (`mangaba/rag/`) with pluggable vector stores
- Tool system (`mangaba/tools/`) — web search (DuckDuckGo), file I/O, and custom tools
- Callback system (`mangaba/callbacks/`) with `on_event` hook
- Embeddings module (`mangaba/embeddings/`) with `sentence-transformers` support
- Vector store backends: in-memory, SQLite, ChromaDB
- Optional dependency groups: `rag`, `embeddings`, `tools`, `chroma`
- Support for **Anthropic** and **HuggingFace** LLM providers
- ReAct reasoning loop in `MangabaAgent`

### Changed
- Major internal refactor — all framework code moved into `mangaba/core/`
- `handle_event` renamed to `on_event` in callbacks

---

## [2.0.4] - 2026-02-13

### Fixed
- GitHub URLs now use correct branch `/blob/master/` instead of `/blob/main/`
- All documentation links verified working on GitHub and PyPI

---

## [2.0.3] - 2026-02-13

### Fixed
- Corrected repository name in URLs: `Mangaba-ai/mangaba_ai`

---

## [2.0.2] - 2026-02-13

### Fixed
- Converted relative links to absolute GitHub URLs in README for PyPI compatibility

---

## [2.0.1] - 2026-01-20

### Changed
- Multi-provider support: Gemini, OpenAI, Anthropic, HuggingFace
- Improved thread safety in broadcast with tag filters
- Removed duplicate methods and fixed incorrect success flags

---

## [1.0.2] - 2025-11-16

### Added
- Official PyPI installation instructions

### Fixed
- `mangaba_ai` module now correctly exposes `MangabaAgent` via `pip install mangaba`
- Version aligned across `pyproject.toml`, `setup.py`, and `__version__`

---

## [1.0.0] - 2024-12-19

### Added
- Initial release of Mangaba AI
- `MangabaAgent` with Gemini backend
- Auto-configuration via `.env`
- Colorized logger (`loguru`)
- Core methods: `chat()`, `chat_with_context()`, `analyze_text()`, `translate()`, `summarize()`, `code_review()`, `explain_code()`
- A2A and MCP protocol foundations (`protocols/`)
- Basic test suite and examples

---

[Unreleased]: https://github.com/Mangaba-ai/mangaba_ai/compare/v3.3.0...HEAD
[3.3.0]: https://github.com/Mangaba-ai/mangaba_ai/compare/v3.2.0...v3.3.0
[3.2.0]: https://github.com/Mangaba-ai/mangaba_ai/compare/v3.1.1...v3.2.0
[3.1.1]: https://github.com/Mangaba-ai/mangaba_ai/compare/v3.1.0...v3.1.1
[3.1.0]: https://github.com/Mangaba-ai/mangaba_ai/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/Mangaba-ai/mangaba_ai/compare/v2.0.4...v3.0.0
[2.0.4]: https://github.com/Mangaba-ai/mangaba_ai/compare/v2.0.3...v2.0.4
[2.0.3]: https://github.com/Mangaba-ai/mangaba_ai/compare/v2.0.2...v2.0.3
[2.0.2]: https://github.com/Mangaba-ai/mangaba_ai/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/Mangaba-ai/mangaba_ai/compare/v1.0.2...v2.0.1
[1.0.2]: https://github.com/Mangaba-ai/mangaba_ai/compare/v1.0.0...v1.0.2
[1.0.0]: https://github.com/Mangaba-ai/mangaba_ai/releases/tag/v1.0.0
