"""
Declarative YAML configuration loader for Mangaba AI v3.0

Turns ``agents.yaml`` / ``tasks.yaml`` / ``crew.yaml`` files into real
:class:`~mangaba.core.agent.Agent`, :class:`~mangaba.core.task.Task` and
:class:`~mangaba.core.crew.Crew` objects, so a project can be described in
data instead of code.

Example::

    from mangaba.config_loader import load_project

    project = load_project("./my_crew")
    result = project.crew.kickoff(inputs={"topic": "AI trends"})
    print(result.final_output)
"""

from __future__ import annotations

import importlib
import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mangaba.core.agent import Agent
from mangaba.core.crew import Crew, Process
from mangaba.core.exceptions import ConfigurationError
from mangaba.core.task import Task
from mangaba.core.types import LLMConfig

log = logging.getLogger(__name__)


AGENTS_FILE = "agents.yaml"
TASKS_FILE = "tasks.yaml"
CREW_FILE = "crew.yaml"

#: Built-in tools addressable by name from YAML. Any other tool can be
#: referenced with a fully-qualified ``package.module:ClassName`` string.
TOOL_REGISTRY: Dict[str, str] = {
    "calculator": "mangaba.tools.math_tools:CalculatorTool",
    "text_splitter": "mangaba.tools.text_tools:TextSplitterTool",
    "word_counter": "mangaba.tools.text_tools:WordCounterTool",
    "file_reader": "mangaba.tools.file_tools:FileReaderTool",
    "file_writer": "mangaba.tools.file_tools:FileWriterTool",
    "directory_list": "mangaba.tools.file_tools:DirectoryListTool",
    "serper_search": "mangaba.tools.web_search:SerperSearchTool",
    "duckduckgo_search": "mangaba.tools.web_search:DuckDuckGoSearchTool",
}

# The tool registry contributes its own built-ins to the table above. Import it
# here so YAML can address them whether or not the caller touched the registry
# first — otherwise resolution would depend on import order.
from mangaba.tools.registry import BUILTIN_TOOLS as _BUILTIN_TOOLS  # noqa: E402

for _name, _target in _BUILTIN_TOOLS.items():
    TOOL_REGISTRY.setdefault(_name, _target)

#: Environment variables holding an API key, per provider.
PROVIDER_KEY_ENVS: Dict[str, List[str]] = {
    "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "huggingface": ["HUGGINGFACE_API_KEY", "HUGGINGFACE_TOKEN", "HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN"],
    "openrouter": ["OPENROUTER_API_KEY"],
}

#: Default model per provider (mirrors ``config.Config.DEFAULT_MODELS``).
PROVIDER_DEFAULT_MODELS: Dict[str, str] = {
    "google": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
    "huggingface": "mistralai/Mistral-7B-Instruct-v0.3",
    "openrouter": "google/gemini-2.5-flash",
}

_PROVIDER_ALIASES: Dict[str, str] = {
    "gemini": "google",
    "google-ai": "google",
    "googleai": "google",
    "gpt": "openai",
    "chatgpt": "openai",
    "claude": "anthropic",
    "hf": "huggingface",
    "hugging-face": "huggingface",
    "or": "openrouter",
    "open-router": "openrouter",
}


# ---------------------------------------------------------------------------
# Lazy pyyaml import
# ---------------------------------------------------------------------------

def _require_yaml() -> Any:
    """Import pyyaml lazily with an actionable error message."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "pyyaml package is required to read agents.yaml/tasks.yaml. "
            "Install with: pip install mangaba[yaml]  (or: pip install pyyaml)"
        ) from exc
    return yaml


def read_yaml(path: str) -> Dict[str, Any]:
    """Read a YAML mapping from *path*.

    Example::

        data = read_yaml("agents.yaml")
    """
    yaml = _require_yaml()
    if not os.path.isfile(path):
        raise ConfigurationError(f"Configuration file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:
        raise ConfigurationError(f"Could not parse YAML file '{path}': {exc}", cause=exc)

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigurationError(f"'{path}' must contain a mapping at the top level, got {type(data).__name__}")
    return data


# ---------------------------------------------------------------------------
# Provider/env resolution
# ---------------------------------------------------------------------------

class LLMSettings(BaseModel):
    """Resolved LLM provider settings (the key value itself is never exposed).

    Example::

        settings = resolve_llm_settings()
        print(settings.provider, settings.model, settings.api_key_set)
    """

    provider: str = "google"
    model: str = "gemini-2.5-flash"
    temperature: float = 0.7
    max_tokens: int = 1024
    api_key_env: Optional[str] = None
    api_key_set: bool = False
    candidate_envs: List[str] = Field(default_factory=list)


def normalize_provider(provider: str) -> str:
    """Normalise provider aliases (``gemini`` → ``google``)."""
    name = (provider or "").strip().lower().replace("_", "-")
    return _PROVIDER_ALIASES.get(name, name)


def resolve_llm_settings(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMSettings:
    """Resolve provider/model/key presence from the environment.

    Reads the same environment variables as ``config.Config`` but never
    raises when the key is missing — callers decide how to degrade.

    Example::

        settings = resolve_llm_settings()
        if not settings.api_key_set:
            print("no API key configured")
    """
    raw_provider = (
        provider
        or os.getenv("LLM_PROVIDER")
        or os.getenv("AI_PROVIDER")
        or os.getenv("PROVIDER")
        or "google"
    )
    prov = normalize_provider(raw_provider)

    resolved_model = (
        model
        or os.getenv("MODEL_NAME")
        or os.getenv("MODEL")
        or PROVIDER_DEFAULT_MODELS.get(prov)
        or "gemini-2.5-flash"
    )

    candidates = list(PROVIDER_KEY_ENVS.get(prov, []))
    key_env: Optional[str] = None
    for env_name in candidates + ["API_KEY"]:
        if os.getenv(env_name):
            key_env = env_name
            break

    try:
        temperature = float(os.getenv("MODEL_TEMPERATURE", os.getenv("TEMPERATURE", "0.7")))
    except ValueError:
        temperature = 0.7
    try:
        max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", os.getenv("MAX_TOKENS", "1024")))
    except ValueError:
        max_tokens = 1024

    return LLMSettings(
        provider=prov,
        model=resolved_model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key_env=key_env,
        api_key_set=key_env is not None,
        candidate_envs=candidates,
    )


def get_api_key(settings: Optional[LLMSettings] = None) -> Optional[str]:
    """Return the API key value for the resolved provider (or ``None``)."""
    settings = settings or resolve_llm_settings()
    if not settings.api_key_env:
        return None
    return os.getenv(settings.api_key_env)


def missing_key_message(settings: Optional[LLMSettings] = None) -> str:
    """Human-friendly explanation of which environment variable to set."""
    settings = settings or resolve_llm_settings()
    envs = " or ".join(settings.candidate_envs) or "API_KEY"
    return (
        f"No API key configured for provider '{settings.provider}'. "
        f"Set {envs} in your environment or .env file."
    )


# ---------------------------------------------------------------------------
# YAML specs
# ---------------------------------------------------------------------------

class AgentSpec(BaseModel):
    """Declarative description of a single agent entry in ``agents.yaml``."""

    model_config = ConfigDict(extra="forbid")

    role: str
    goal: str
    backstory: str
    tools: List[str] = Field(default_factory=list)
    verbose: bool = False
    allow_delegation: bool = True
    max_iterations: int = Field(default=15, ge=1)
    max_retry_on_error: int = Field(default=3, ge=0)
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    @field_validator("role", "goal", "backstory")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class TaskSpec(BaseModel):
    """Declarative description of a single task entry in ``tasks.yaml``."""

    model_config = ConfigDict(extra="forbid")

    description: str
    expected_output: str
    agent: Optional[str] = None
    context: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    output_file: Optional[str] = None
    async_execution: bool = False
    human_input: bool = False
    retry_on_failure: int = Field(default=0, ge=0)

    @field_validator("description", "expected_output")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class CrewSpec(BaseModel):
    """Optional ``crew.yaml`` describing how the crew is orchestrated."""

    model_config = ConfigDict(extra="forbid")

    name: str = "crew"
    kind: str = "crew"
    process: str = "sequential"
    verbose: bool = False
    max_rpm: Optional[int] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("kind")
    @classmethod
    def known_kind(cls, v: str) -> str:
        if v.lower() not in ("crew", "flow"):
            raise ValueError(f"Unknown kind '{v}'. Valid: crew, flow")
        return v.lower()

    @field_validator("process")
    @classmethod
    def known_process(cls, v: str) -> str:
        valid = [p.value for p in Process]
        if v.lower() not in valid:
            raise ValueError(f"Unknown process '{v}'. Valid: {', '.join(valid)}")
        return v.lower()


class Project:
    """A crew loaded from YAML, with the objects that compose it.

    Example::

        project = load_project(".")
        project.crew.kickoff(project.inputs)
    """

    def __init__(
        self,
        crew: Crew,
        agents: Dict[str, Agent],
        tasks: Dict[str, Task],
        spec: CrewSpec,
        directory: str,
    ) -> None:
        self.crew = crew
        self.agents = agents
        self.tasks = tasks
        self.spec = spec
        self.directory = directory

    @property
    def inputs(self) -> Dict[str, Any]:
        return dict(self.spec.inputs)

    def __repr__(self) -> str:
        return f"Project(dir='{self.directory}', agents={len(self.agents)}, tasks={len(self.tasks)})"


# ---------------------------------------------------------------------------
# Building real objects
# ---------------------------------------------------------------------------

def resolve_tool(reference: str) -> Any:
    """Instantiate a tool from a registry name or ``module:ClassName`` path."""
    target = TOOL_REGISTRY.get(reference, reference)
    if ":" not in target:
        raise ConfigurationError(
            f"Unknown tool '{reference}'. Use one of {sorted(TOOL_REGISTRY)} "
            "or a fully-qualified 'package.module:ClassName' reference."
        )
    module_name, _, attr = target.partition(":")
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, attr)
    except (ImportError, AttributeError) as exc:
        raise ConfigurationError(f"Could not import tool '{reference}' ({target}): {exc}", cause=exc)
    try:
        return obj() if isinstance(obj, type) else obj
    except Exception as exc:
        raise ConfigurationError(f"Could not instantiate tool '{reference}': {exc}", cause=exc)


def build_agent(
    spec: AgentSpec,
    llm: Optional[Any] = None,
    settings: Optional[LLMSettings] = None,
    api_key: Optional[str] = None,
    verbose: Optional[bool] = None,
) -> Agent:
    """Build an :class:`Agent` from an :class:`AgentSpec`.

    Pass ``llm`` to inject an already-built client (handy for tests); leave
    it ``None`` to build one from the environment configuration.

    Example::

        agent = build_agent(AgentSpec(role="Analyst", goal="...", backstory="..."))
    """
    tools = [resolve_tool(name) for name in spec.tools]

    kwargs: Dict[str, Any] = {
        "role": spec.role,
        "goal": spec.goal,
        "backstory": spec.backstory,
        "tools": tools,
        "verbose": spec.verbose if verbose is None else verbose,
        "max_iterations": spec.max_iterations,
        "max_retry_on_error": spec.max_retry_on_error,
        "allow_delegation": spec.allow_delegation,
    }

    if llm is not None:
        kwargs["llm"] = llm
        return Agent(**kwargs)

    settings = settings or resolve_llm_settings(provider=spec.provider, model=spec.model)
    key = api_key or get_api_key(settings)
    if not key:
        raise ConfigurationError(missing_key_message(settings))

    kwargs["llm_config"] = LLMConfig(
        provider=spec.provider or settings.provider,
        model=spec.model or settings.model,
        api_key=key,
        temperature=spec.temperature if spec.temperature is not None else settings.temperature,
        max_tokens=spec.max_tokens if spec.max_tokens is not None else settings.max_tokens,
    )
    kwargs["api_key"] = key
    return Agent(**kwargs)


def build_agents(
    data: Dict[str, Any],
    llm: Optional[Any] = None,
    settings: Optional[LLMSettings] = None,
    api_key: Optional[str] = None,
    verbose: Optional[bool] = None,
) -> Dict[str, Agent]:
    """Build every agent declared in an ``agents.yaml`` mapping."""
    if not data:
        raise ConfigurationError(f"No agents declared — '{AGENTS_FILE}' is empty.")

    agents: Dict[str, Agent] = {}
    for name, raw in data.items():
        if not isinstance(raw, dict):
            raise ConfigurationError(f"Agent '{name}' must be a mapping of fields, got {type(raw).__name__}")
        try:
            spec = AgentSpec(**raw)
        except Exception as exc:
            raise ConfigurationError(f"Invalid agent '{name}': {exc}", cause=exc)
        agents[name] = build_agent(spec, llm=llm, settings=settings, api_key=api_key, verbose=verbose)
        log.debug("Built agent '%s' (role=%s)", name, spec.role)
    return agents


def build_tasks(data: Dict[str, Any], agents: Dict[str, Agent]) -> Dict[str, Task]:
    """Build every task declared in a ``tasks.yaml`` mapping.

    Task names referenced in ``context:`` are resolved after all tasks
    exist, so declaration order does not matter.
    """
    if not data:
        raise ConfigurationError(f"No tasks declared — '{TASKS_FILE}' is empty.")

    specs: Dict[str, TaskSpec] = {}
    for name, raw in data.items():
        if not isinstance(raw, dict):
            raise ConfigurationError(f"Task '{name}' must be a mapping of fields, got {type(raw).__name__}")
        try:
            specs[name] = TaskSpec(**raw)
        except Exception as exc:
            raise ConfigurationError(f"Invalid task '{name}': {exc}", cause=exc)

    agent_names = list(agents)
    tasks: Dict[str, Task] = {}
    for name, spec in specs.items():
        if spec.agent is None:
            if len(agents) != 1:
                raise ConfigurationError(
                    f"Task '{name}' has no 'agent:' and the project declares {len(agents)} agents "
                    f"({', '.join(agent_names)}) — the assignment is ambiguous."
                )
            agent = agents[agent_names[0]]
        elif spec.agent not in agents:
            raise ConfigurationError(
                f"Task '{name}' references unknown agent '{spec.agent}'. Declared agents: {', '.join(agent_names)}"
            )
        else:
            agent = agents[spec.agent]

        tasks[name] = Task(
            description=spec.description,
            expected_output=spec.expected_output,
            agent=agent,
            tools=[resolve_tool(t) for t in spec.tools],
            output_file=spec.output_file,
            async_execution=spec.async_execution,
            human_input=spec.human_input,
            retry_on_failure=spec.retry_on_failure,
        )

    for name, spec in specs.items():
        for dep in spec.context:
            if dep not in tasks:
                raise ConfigurationError(
                    f"Task '{name}' declares context on unknown task '{dep}'. Declared tasks: {', '.join(tasks)}"
                )
            if dep == name:
                raise ConfigurationError(f"Task '{name}' cannot declare itself as context.")
            tasks[name].context.append(tasks[dep])

    return tasks


def build_crew(
    agents_data: Dict[str, Any],
    tasks_data: Dict[str, Any],
    crew_data: Optional[Dict[str, Any]] = None,
    llm: Optional[Any] = None,
    verbose: Optional[bool] = None,
) -> Project:
    """Build a full :class:`Crew` (wrapped in a :class:`Project`) from raw mappings.

    Example::

        project = build_crew(
            {"writer": {"role": "Writer", "goal": "Write", "backstory": "Wordsmith"}},
            {"write": {"description": "Write a haiku", "expected_output": "3 lines"}},
        )
    """
    try:
        spec = CrewSpec(**(crew_data or {}))
    except Exception as exc:
        raise ConfigurationError(f"Invalid '{CREW_FILE}': {exc}", cause=exc)

    crew_verbose = spec.verbose if verbose is None else verbose
    agents = build_agents(agents_data, llm=llm, verbose=verbose)
    tasks = build_tasks(tasks_data, agents)

    crew = Crew(
        agents=list(agents.values()),
        tasks=list(tasks.values()),
        process=Process(spec.process),
        verbose=crew_verbose,
        max_rpm=spec.max_rpm,
    )
    return Project(crew=crew, agents=agents, tasks=tasks, spec=spec, directory=".")


def load_project(
    directory: str = ".",
    llm: Optional[Any] = None,
    verbose: Optional[bool] = None,
) -> Project:
    """Load ``agents.yaml`` + ``tasks.yaml`` (+ optional ``crew.yaml``) from *directory*.

    Example::

        project = load_project("./my_crew")
        result = project.crew.kickoff(project.inputs)
    """
    agents_path = os.path.join(directory, AGENTS_FILE)
    tasks_path = os.path.join(directory, TASKS_FILE)
    crew_path = os.path.join(directory, CREW_FILE)

    for path, what in ((agents_path, AGENTS_FILE), (tasks_path, TASKS_FILE)):
        if not os.path.isfile(path):
            raise ConfigurationError(
                f"'{what}' not found in {os.path.abspath(directory)}. "
                "Run this from a Mangaba project directory, or create one with: mangaba create crew <name>"
            )

    agents_data = read_yaml(agents_path)
    tasks_data = read_yaml(tasks_path)
    crew_data = read_yaml(crew_path) if os.path.isfile(crew_path) else {}

    project = build_crew(agents_data, tasks_data, crew_data, llm=llm, verbose=verbose)
    project.directory = directory
    log.info("Loaded project from %s — %d agents, %d tasks", directory, len(project.agents), len(project.tasks))
    return project


def load_crew(directory: str = ".", llm: Optional[Any] = None, verbose: Optional[bool] = None) -> Crew:
    """Convenience wrapper returning only the :class:`Crew`."""
    return load_project(directory, llm=llm, verbose=verbose).crew


__all__ = [
    "AGENTS_FILE",
    "TASKS_FILE",
    "CREW_FILE",
    "TOOL_REGISTRY",
    "PROVIDER_KEY_ENVS",
    "PROVIDER_DEFAULT_MODELS",
    "AgentSpec",
    "TaskSpec",
    "CrewSpec",
    "LLMSettings",
    "Project",
    "read_yaml",
    "normalize_provider",
    "resolve_llm_settings",
    "get_api_key",
    "missing_key_message",
    "resolve_tool",
    "build_agent",
    "build_agents",
    "build_tasks",
    "build_crew",
    "load_project",
    "load_crew",
]
