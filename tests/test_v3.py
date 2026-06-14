"""Testes para módulos principais do Mangaba AI v3.0."""

import pytest
from unittest.mock import Mock, patch

# ── Types ─────────────────────────────────────────────────────────────

from mangaba.core.types import (
    LLMConfig,
    Message,
    LLMResponse,
    AgentConfig,
    TokenUsage,
    ToolCall,
)


class TestTypes:
    def test_llm_config_defaults(self):
        cfg = LLMConfig(api_key="k", provider="google")
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 1024

    def test_llm_config_provider_alias(self):
        cfg = LLMConfig(api_key="k", provider="gemini")
        assert cfg.provider == "google"

    def test_message_factories(self):
        m = Message.user("hello")
        assert m.role == "user"
        assert m.content == "hello"
        m2 = Message.system("sys")
        assert m2.role == "system"

    def test_llm_response_tool_calls(self):
        tc = ToolCall(id="1", tool_name="fn", arguments={"x": 1})
        resp = LLMResponse(content="", tool_calls=[tc], usage=TokenUsage())
        assert resp.has_tool_calls

    def test_agent_config(self):
        cfg = AgentConfig(role="R", goal="G", backstory="B")
        assert cfg.max_iterations == 15


# ── Exceptions ────────────────────────────────────────────────────────

from mangaba.core.exceptions import (
    MangabaError,
    LLMError,
    ToolError,
    AgentError,
    CrewError,
    RateLimitError,
)


class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(LLMError, MangabaError)
        assert issubclass(RateLimitError, LLMError)
        assert issubclass(ToolError, MangabaError)
        assert issubclass(AgentError, MangabaError)
        assert issubclass(CrewError, MangabaError)


# ── Events ────────────────────────────────────────────────────────────

from mangaba.core.events import EventBus, Event, EventType, BaseCallback


class _Collector(BaseCallback):
    def __init__(self):
        super().__init__()
        self.events = []

    def on_event(self, event):
        self.events.append(event)


class TestEvents:
    def setup_method(self):
        EventBus.reset()

    def test_emit_and_receive(self):
        c = _Collector()
        EventBus.register(c)
        EventBus.emit(Event(event_type=EventType.AGENT_START, data={"hi": 1}))
        assert len(c.events) == 1
        assert c.events[0].data["hi"] == 1

    def test_unregister(self):
        c = _Collector()
        EventBus.register(c)
        EventBus.unregister(c)
        EventBus.emit(Event(event_type=EventType.AGENT_END))
        assert len(c.events) == 0

    def teardown_method(self):
        EventBus.reset()


# ── Tools ─────────────────────────────────────────────────────────────

from mangaba.tools.decorator import tool
from mangaba.tools.math_tools import CalculatorTool
from mangaba.tools.text_tools import WordCounterTool


class TestTools:
    def setup_method(self):
        EventBus.reset()

    def test_calculator(self):
        calc = CalculatorTool()
        result = calc.run(expression="2 + 3")
        assert "5" in result

    def test_word_counter(self):
        wc = WordCounterTool()
        result = wc.run(text="hello world foo")
        assert "3" in result

    def test_tool_decorator(self):
        @tool
        def add(a: int, b: int) -> str:
            """Add two numbers."""
            return str(a + b)

        assert add.name == "add"
        assert add.description == "Add two numbers."
        r = add.run(a=1, b=2)
        assert r == "3"

    def test_json_schema_generation(self):
        calc = CalculatorTool()
        schema = calc.get_function_schema()
        assert schema["name"] == "calculator"
        assert "parameters" in schema

    def teardown_method(self):
        EventBus.reset()


# ── Memory ────────────────────────────────────────────────────────────

from mangaba.memory.short_term import ShortTermMemory


class TestShortTermMemory:
    def test_add_and_search(self):
        mem = ShortTermMemory(max_items=10)
        mem.add("Python is great")
        mem.add("Java is verbose")
        results = mem.search("Python")
        assert any("Python" in r["content"] for r in results)

    def test_max_items(self):
        mem = ShortTermMemory(max_items=2)
        mem.add("a")
        mem.add("b")
        mem.add("c")
        assert len(mem.get_all()) == 2


# ── Output parsers ───────────────────────────────────────────────────

from mangaba.core.output_parsers import JSONOutputParser, ListOutputParser


class TestOutputParsers:
    def test_json_parser(self):
        parser = JSONOutputParser()
        result = parser.parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_parser_with_markdown(self):
        parser = JSONOutputParser()
        result = parser.parse('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_list_parser(self):
        parser = ListOutputParser()
        result = parser.parse("- item1\n- item2\n- item3")
        assert len(result) == 3


# ── Guardrails ────────────────────────────────────────────────────────

from mangaba.core.guardrails import LengthGuardrail, ContentFilterGuardrail


class TestGuardrails:
    def test_length_guardrail_pass(self):
        g = LengthGuardrail(max_length=100)
        result = g.validate("short text")
        assert result == "short text"

    def test_length_guardrail_truncate(self):
        g = LengthGuardrail(max_length=5)
        result = g.validate("this is too long")
        assert len(result) == 5

    def test_content_filter(self):
        g = ContentFilterGuardrail(blocked_patterns=[r"spam"])
        assert g.validate("hello world") == "hello world"
        filtered = g.validate("this is spam content")
        assert "spam" not in filtered


# ── RAG ───────────────────────────────────────────────────────────────

from mangaba.rag.document import Document
from mangaba.rag.splitters import RecursiveTextSplitter


class TestRAG:
    def test_document_creation(self):
        doc = Document(content="hello world", metadata={"src": "test"})
        assert doc.content == "hello world"

    def test_text_splitter(self):
        splitter = RecursiveTextSplitter(chunk_size=20, chunk_overlap=5)
        docs = splitter.split_text("This is a test. " * 10)
        assert len(docs) > 1


# ── Crew ──────────────────────────────────────────────────────────────

from mangaba.core.crew import Crew, Process
from mangaba.core.agent import Agent
from mangaba.core.task import Task


class TestCrew:
    def setup_method(self):
        EventBus.reset()

    def _make_agent(self, role="worker"):
        with patch("mangaba.core.agent.ReActEngine"):
            a = Agent.__new__(Agent)
            a.role = role
            a.goal = "test"
            a.backstory = ""
            a.tools = []
            a.llm = Mock()
            a.max_iterations = 5
            a.memory = None
            a.guardrails = []
            a.verbose = False
            a.agent_id = f"agent_{role}"
            a._peers = {}
            a.engine = Mock()
            return a

    def _make_task(self, agent, desc="do something"):
        t = Task.__new__(Task)
        t.description = desc
        t.expected_output = "result"
        t.agent = agent
        t.context = []
        t.guardrails = []
        t.output_parser = None
        t.human_input = False
        t.async_execution = False
        t.retry_on_failure = 0
        return t

    def test_crew_creation(self):
        a = self._make_agent()
        t = self._make_task(a)
        crew = Crew(agents=[a], tasks=[t])
        assert crew.process == Process.SEQUENTIAL

    def test_crew_requires_agents(self):
        from mangaba.core.exceptions import CrewError

        with pytest.raises(CrewError):
            Crew(agents=[], tasks=[self._make_task(self._make_agent())])

    def test_crew_requires_tasks(self):
        from mangaba.core.exceptions import CrewError

        with pytest.raises(CrewError):
            Crew(agents=[self._make_agent()], tasks=[])

    def teardown_method(self):
        EventBus.reset()


# ── Workflow ──────────────────────────────────────────────────────────

from mangaba.core.workflow import Pipeline


class TestWorkflow:
    def setup_method(self):
        EventBus.reset()

    def test_pipeline_creation(self):
        p = Pipeline(stages=[], name="test")
        result = p.run()
        assert result.duration >= 0
        assert result.stages == []

    def teardown_method(self):
        EventBus.reset()


# ── Callbacks ─────────────────────────────────────────────────────────

from mangaba.callbacks.console import ConsoleCallback
from mangaba.callbacks.file import FileCallback


class TestCallbacks:
    def test_console_callback(self):
        cb = ConsoleCallback()
        e = Event(event_type=EventType.AGENT_START, data={"test": True})
        cb.on_event(e)  # Should not raise

    def test_file_callback(self, tmp_path):
        p = tmp_path / "events.jsonl"
        cb = FileCallback(path=p)
        e = Event(event_type=EventType.TOOL_START, data={"tool": "calc"})
        cb.on_event(e)
        assert p.exists()
        content = p.read_text()
        assert "tool_start" in content


# ── Package imports ───────────────────────────────────────────────────


class TestImports:
    def test_main_package(self):
        import mangaba

        assert mangaba.__version__ == "3.0.0"
        assert hasattr(mangaba, "Agent")
        assert hasattr(mangaba, "Task")
        assert hasattr(mangaba, "Crew")
        assert hasattr(mangaba, "Pipeline")
        assert hasattr(mangaba, "BaseTool")
        assert hasattr(mangaba, "tool")
        assert hasattr(mangaba, "EventBus")

    def test_memory_package(self):
        from mangaba.memory import ShortTermMemory

        assert ShortTermMemory is not None

    def test_rag_package(self):
        from mangaba.rag import Document

        assert Document is not None

    def test_tools_package(self):
        from mangaba.tools import BaseTool

        assert BaseTool is not None
