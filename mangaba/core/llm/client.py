from __future__ import annotations

"""
LLM provider engine for Mangaba AI v3.0

Supports native function-calling (tool use), streaming, token counting
and a unified response format across Google, OpenAI, Anthropic,
Hugging Face, OpenRouter and locally hosted models (Ollama and any
OpenAI-compatible server such as vLLM, LM Studio, llama.cpp or LocalAI).
"""

import base64
import json
import logging
import mimetypes
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, Union

from mangaba.core.types import (
    FinishReason,
    LLMResponse,
    TokenUsage,
    ToolCall,
)
from mangaba.core.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ContentFilterError,
    LLMError,
    RateLimitError,
    RetryableError,
)
from mangaba.core.events import EventBus, Event, EventType

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool schema helpers
# ---------------------------------------------------------------------------

def _tool_to_google_declaration(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to Google function declaration format."""
    schema = tool.get_function_schema()
    return {
        "name": schema["name"],
        "description": schema["description"],
        "parameters": schema.get("parameters", {"type": "object", "properties": {}}),
    }


def _tool_to_openai_schema(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to OpenAI function calling format."""
    schema = tool.get_function_schema()
    return {
        "type": "function",
        "function": {
            "name": schema["name"],
            "description": schema["description"],
            "parameters": schema.get("parameters", {"type": "object", "properties": {}}),
        },
    }


def _tool_to_anthropic_schema(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to Anthropic tool-use format."""
    schema = tool.get_function_schema()
    return {
        "name": schema["name"],
        "description": schema["description"],
        "input_schema": schema.get("parameters", {"type": "object", "properties": {}}),
    }


def _tools_to_hf_prompt_section(tools: List[Any]) -> str:
    """Render available tools as a system-prompt section for Hugging Face."""
    if not tools:
        return ""
    lines = ["You have access to the following tools:\n"]
    for t in tools:
        schema = t.get_function_schema()
        params = json.dumps(schema.get("parameters", {}), indent=2)
        lines.append(f"### {schema['name']}\n{schema['description']}\nParameters: {params}\n")
    lines.append(
        "To use a tool, respond ONLY with a JSON block:\n"
        '```json\n{"tool_calls": [{"tool_name": "<name>", "arguments": {<args>}}]}\n```\n'
        "If no tool is needed, respond normally."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Image / multimodal helpers
# ---------------------------------------------------------------------------

#: Used when an image carries no explicit and no guessable MIME type.
_IMAGE_MIME_FALLBACK = "image/png"


def _normalize_image(image: Any) -> Dict[str, Any]:
    """Accept an ``ImageContent``, a mapping, or a bare path/URL string."""
    if hasattr(image, "model_dump"):
        return {k: v for k, v in image.model_dump(exclude_none=True).items() if v is not None}
    if isinstance(image, dict):
        return {k: v for k, v in image.items() if v is not None}
    if isinstance(image, str):
        if image.startswith(("http://", "https://", "data:")):
            return {"url": image}
        return {"path": image}
    raise ValueError(
        f"Unsupported image entry of type {type(image).__name__}; "
        "expected ImageContent, dict or str"
    )


def _resolve_image_source(image: Any) -> Dict[str, Any]:
    """Resolve an image entry to ``{kind, url|data, mime_type, detail}``.

    ``kind`` is ``"url"`` for remotely hosted images and ``"base64"`` once the
    bytes are inlined (local files and raw base64 payloads).
    """
    data = _normalize_image(image)
    detail = data.get("detail")
    mime = data.get("mime_type")
    path = data.get("path")
    b64 = data.get("base64_data")
    url = data.get("url")

    if path:
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
        except OSError as exc:
            raise LLMError(f"Could not read image file '{path}': {exc}", cause=exc) from exc
        # The file on disk is authoritative: ImageContent.mime_type carries a
        # default ("image/png") that would otherwise mislabel every .jpg/.webp.
        mime = mimetypes.guess_type(str(path))[0] or mime or _IMAGE_MIME_FALLBACK
        return {
            "kind": "base64",
            "data": base64.b64encode(raw).decode("ascii"),
            "mime_type": mime,
            "detail": detail,
        }

    if b64:
        payload = b64
        if payload.startswith("data:"):
            header, _, payload = payload.partition(",")
            mime = header[len("data:"):].split(";")[0] or mime or None
        return {
            "kind": "base64",
            "data": payload,
            "mime_type": mime or _IMAGE_MIME_FALLBACK,
            "detail": detail,
        }

    if url:
        if url.startswith("data:"):
            header, _, payload = url.partition(",")
            mime = header[len("data:"):].split(";")[0] or mime or None
            return {
                "kind": "base64",
                "data": payload,
                "mime_type": mime or _IMAGE_MIME_FALLBACK,
                "detail": detail,
            }
        return {"kind": "url", "url": url, "mime_type": mime, "detail": detail}

    raise ValueError("Image entry must define one of 'url', 'path' or 'base64_data'")


def _image_to_data_url(source: Dict[str, Any]) -> str:
    """Render a resolved image source as a URL the OpenAI API accepts."""
    if source["kind"] == "url":
        return source["url"]
    return "data:{0};base64,{1}".format(source["mime_type"], source["data"])


def _images_to_openai_parts(images: List[Any]) -> List[Dict[str, Any]]:
    """Convert images to OpenAI ``image_url`` content parts."""
    parts: List[Dict[str, Any]] = []
    for image in images:
        source = _resolve_image_source(image)
        block: Dict[str, Any] = {"url": _image_to_data_url(source)}
        if source.get("detail"):
            block["detail"] = source["detail"]
        parts.append({"type": "image_url", "image_url": block})
    return parts


def _openai_user_content(prompt: str, images: Optional[List[Any]]) -> Any:
    """Return a plain string when there are no images, else a content-parts array."""
    if not images:
        return prompt
    parts: List[Dict[str, Any]] = []
    if prompt:
        parts.append({"type": "text", "text": prompt})
    parts.extend(_images_to_openai_parts(images))
    return parts


def _images_to_anthropic_blocks(images: List[Any]) -> List[Dict[str, Any]]:
    """Convert images to Anthropic ``image`` content blocks."""
    blocks: List[Dict[str, Any]] = []
    for image in images:
        source = _resolve_image_source(image)
        if source["kind"] == "url":
            blocks.append({"type": "image", "source": {"type": "url", "url": source["url"]}})
        else:
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": source["mime_type"],
                    "data": source["data"],
                },
            })
    return blocks


def _anthropic_user_content(prompt: str, images: Optional[List[Any]]) -> Any:
    """Return a plain string when there are no images, else a content-blocks array."""
    if not images:
        return prompt
    blocks = _images_to_anthropic_blocks(images)
    if prompt:
        blocks.append({"type": "text", "text": prompt})
    return blocks


def _images_to_google_parts(images: List[Any]) -> List[Dict[str, Any]]:
    """Convert images to Gemini ``inline_data`` blob parts.

    The SDK base64-encodes the blob on the wire, so raw bytes are handed over.
    Gemini cannot fetch remote URLs inline, hence the explicit error.
    """
    parts: List[Dict[str, Any]] = []
    for image in images:
        source = _resolve_image_source(image)
        if source["kind"] == "url":
            raise LLMError(
                "Google Gemini cannot read images from a remote URL. "
                "Provide 'path' or 'base64_data' instead."
            )
        parts.append({
            "inline_data": {
                "mime_type": source["mime_type"],
                "data": base64.b64decode(source["data"]),
            }
        })
    return parts


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    name: str = "base"
    aliases: Tuple[str, ...] = ()
    #: Local/self-hosted providers set this to False so ``create_llm_client``
    #: does not demand an API key the server will never check.
    requires_api_key: bool = True
    #: Whether ``generate`` accepts the optional ``images`` argument.
    supports_images: bool = False

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.options = options or {}
        self._temperature = options.get("temperature", 0.7)
        self._max_tokens = options.get("max_output_tokens", 1024)
        self._system_prompt = options.get("system_prompt")

    @classmethod
    def matches(cls, provider_name: str) -> bool:
        n = provider_name.lower()
        return n == cls.name or n in cls.aliases

    # -- public API ----------------------------------------------------------

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        ...

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response with optional tool/function calling support."""
        # Default: ignore tools and fall back to plain generate
        user_content = ""
        for m in messages:
            if m.get("role") == "user":
                user_content = m.get("content", "")
        return self.generate(user_content, **kwargs)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream response token-by-token. Default: yield full response."""
        resp = self.generate(prompt, **kwargs)
        yield resp.text

    def count_tokens(self, text: str) -> int:
        """Estimate token count. Default: rough word-based estimate."""
        return max(1, len(text) // 4)

    # -- internal ------------------------------------------------------------

    def _reject_images(self, images: Optional[List[Any]]) -> None:
        """Raise the contractual ``TypeError`` when images cannot be honoured."""
        if images:
            raise TypeError(
                f"Provider '{self.name}' does not support image input. "
                "Use a vision-capable provider (e.g. openai, anthropic, google, "
                "or ollama with a vision model such as llava)."
            )


# ---------------------------------------------------------------------------
# Google (Gemini)
# ---------------------------------------------------------------------------

class GoogleLLMProvider(BaseLLMProvider):
    name = "google"
    aliases = ("gemini", "google-ai", "googleai")
    supports_images = True

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        super().__init__(api_key, model, **options)
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'google-generativeai' not found. Install with: pip install 'mangaba[google]'"
            ) from exc

        genai.configure(api_key=api_key)
        gen_cfg = options.get("generation_config")
        safety = options.get("safety_settings")
        if gen_cfg is None:
            gen_cfg = {
                k: options.get(k)
                for k in ("temperature", "top_p", "top_k", "max_output_tokens")
                if options.get(k) is not None
            } or None

        self._model = genai.GenerativeModel(
            model_name=model,
            generation_config=gen_cfg,
            safety_settings=safety,
        )
        self._genai = genai

    def generate(self, prompt: str, images: Optional[List[Any]] = None, **kwargs: Any) -> LLMResponse:
        contents: Any = prompt
        if images:
            contents = [{"text": prompt}] if prompt else []
            contents.extend(_images_to_google_parts(images))
        try:
            response = self._model.generate_content(
                contents, **{k: v for k, v in kwargs.items() if v is not None}
            )
        except Exception as exc:
            raise LLMError(f"Google LLM error: {exc}", cause=exc) from exc

        text = getattr(response, "text", None) or ""
        usage = self._parse_usage(response)
        return LLMResponse(content=text, usage=usage, model=self.model, raw=response)

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        try:
            genai_tools = None
            if tools:
                declarations = [_tool_to_google_declaration(t) for t in tools]
                genai_tools = [self._genai.protos.Tool(function_declarations=[
                    self._genai.protos.FunctionDeclaration(**d) for d in declarations
                ])]

            # Build contents from messages
            contents = []
            for m in messages:
                role = "model" if m["role"] == "assistant" else m["role"]
                if role == "system":
                    continue
                contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

            response = self._model.generate_content(
                contents,
                tools=genai_tools,
                **{k: v for k, v in kwargs.items() if v is not None},
            )
        except Exception as exc:
            raise LLMError(f"Google LLM error: {exc}", cause=exc) from exc

        text = ""
        tool_calls: List[ToolCall] = []
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append(ToolCall(
                        tool_name=fc.name,
                        arguments=dict(fc.args) if fc.args else {},
                    ))
        except (IndexError, AttributeError):
            text = getattr(response, "text", "") or ""

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(response)
        return LLMResponse(content=text, tool_calls=tool_calls, usage=usage, model=self.model, finish_reason=finish, raw=response)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        try:
            response = self._model.generate_content(prompt, stream=True)
            for chunk in response:
                txt = getattr(chunk, "text", None) or ""
                if txt:
                    yield txt
        except Exception as exc:
            raise LLMError(f"Google streaming error: {exc}", cause=exc) from exc

    def _parse_usage(self, response: Any) -> TokenUsage:
        try:
            um = response.usage_metadata
            return TokenUsage(
                prompt_tokens=getattr(um, "prompt_token_count", 0),
                completion_tokens=getattr(um, "candidates_token_count", 0),
                total_tokens=getattr(um, "total_token_count", 0),
            )
        except Exception:
            return TokenUsage()


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

class OpenAILLMProvider(BaseLLMProvider):
    name = "openai"
    aliases = ("gpt", "chatgpt")
    supports_images = True

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        super().__init__(api_key, model, **options)
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Package 'openai' not found. Install with: pip install openai") from exc
        self._client = OpenAI(api_key=api_key)

    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        images: Optional[List[Any]] = None,
    ) -> List[Dict[str, Any]]:
        msgs: List[Dict[str, Any]] = []
        sp = system_prompt or self._system_prompt
        if sp:
            msgs.append({"role": "system", "content": sp})
        msgs.append({"role": "user", "content": _openai_user_content(prompt, images)})
        return msgs

    def generate(self, prompt: str, images: Optional[List[Any]] = None, **kwargs: Any) -> LLMResponse:
        msgs = self._build_messages(prompt, kwargs.pop("system_prompt", None), images)
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenAI error: {exc}", cause=exc) from exc

        text = resp.choices[0].message.content or ""
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, usage=usage, model=self.model, raw=resp)

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        openai_tools = [_tool_to_openai_schema(t) for t in tools] if tools else None
        try:
            create_kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self._temperature),
                "max_tokens": kwargs.get("max_output_tokens", self._max_tokens),
            }
            if openai_tools:
                create_kwargs["tools"] = openai_tools
            resp = self._client.chat.completions.create(**create_kwargs)
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenAI error: {exc}", cause=exc) from exc

        msg = resp.choices[0].message
        text = msg.content or ""
        tool_calls: List[ToolCall] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                tool_calls.append(ToolCall(id=tc.id, tool_name=tc.function.name, arguments=args))

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, tool_calls=tool_calls, usage=usage, model=self.model, finish_reason=finish, raw=resp)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        msgs = self._build_messages(prompt, kwargs.pop("system_prompt", None))
        try:
            stream = self._client.chat.completions.create(
                model=self.model, messages=msgs,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            raise LLMError(f"OpenAI streaming error: {exc}", cause=exc) from exc

    def count_tokens(self, text: str) -> int:
        try:
            import tiktoken  # type: ignore
            enc = tiktoken.encoding_for_model(self.model)
            return len(enc.encode(text))
        except Exception:
            return super().count_tokens(text)

    def _parse_usage(self, resp: Any) -> TokenUsage:
        if resp.usage:
            return TokenUsage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
                total_tokens=resp.usage.total_tokens or 0,
            )
        return TokenUsage()

    def _handle_openai_error(self, exc: Exception) -> None:
        exc_name = type(exc).__name__
        if "AuthenticationError" in exc_name:
            raise AuthenticationError(str(exc), cause=exc) from exc
        if "RateLimitError" in exc_name:
            raise RateLimitError(str(exc), cause=exc) from exc
        if "APITimeoutError" in exc_name or "APIConnectionError" in exc_name:
            raise RetryableError(str(exc), cause=exc) from exc


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicLLMProvider(BaseLLMProvider):
    name = "anthropic"
    aliases = ("claude",)
    supports_images = True

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        super().__init__(api_key, model, **options)
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Package 'anthropic' not found. Install with: pip install 'mangaba[anthropic]'") from exc
        self._client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, images: Optional[List[Any]] = None, **kwargs: Any) -> LLMResponse:
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                system=kwargs.get("system_prompt", self._system_prompt) or "",
                messages=[{"role": "user", "content": _anthropic_user_content(prompt, images)}],
            )
        except Exception as exc:
            self._handle_anthropic_error(exc)
            raise LLMError(f"Anthropic error: {exc}", cause=exc) from exc

        parts = [getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text"]
        text = "\n".join(p for p in parts if p)
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, usage=usage, model=self.model, raw=resp)

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        anthropic_tools = [_tool_to_anthropic_schema(t) for t in tools] if tools else None
        # Extract system from messages
        system_text = ""
        api_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text = m.get("content", "")
            else:
                api_messages.append(m)

        try:
            create_kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": kwargs.get("max_output_tokens", self._max_tokens),
                "temperature": kwargs.get("temperature", self._temperature),
                "messages": api_messages,
            }
            if system_text:
                create_kwargs["system"] = system_text
            if anthropic_tools:
                create_kwargs["tools"] = anthropic_tools

            resp = self._client.messages.create(**create_kwargs)
        except Exception as exc:
            self._handle_anthropic_error(exc)
            raise LLMError(f"Anthropic error: {exc}", cause=exc) from exc

        text = ""
        tool_calls: List[ToolCall] = []
        for block in resp.content:
            if getattr(block, "type", "") == "text":
                text += getattr(block, "text", "")
            elif getattr(block, "type", "") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    tool_name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else {},
                ))

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, tool_calls=tool_calls, usage=usage, model=self.model, finish_reason=finish, raw=resp)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        try:
            with self._client.messages.stream(
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                system=kwargs.get("system_prompt", self._system_prompt) or "",
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as exc:
            raise LLMError(f"Anthropic streaming error: {exc}", cause=exc) from exc

    def _parse_usage(self, resp: Any) -> TokenUsage:
        if hasattr(resp, "usage") and resp.usage:
            return TokenUsage(
                prompt_tokens=getattr(resp.usage, "input_tokens", 0),
                completion_tokens=getattr(resp.usage, "output_tokens", 0),
                total_tokens=getattr(resp.usage, "input_tokens", 0) + getattr(resp.usage, "output_tokens", 0),
            )
        return TokenUsage()

    def _handle_anthropic_error(self, exc: Exception) -> None:
        exc_name = type(exc).__name__
        if "AuthenticationError" in exc_name:
            raise AuthenticationError(str(exc), cause=exc) from exc
        if "RateLimitError" in exc_name:
            raise RateLimitError(str(exc), cause=exc) from exc
        if "APITimeoutError" in exc_name or "APIConnectionError" in exc_name:
            raise RetryableError(str(exc), cause=exc) from exc


# ---------------------------------------------------------------------------
# Hugging Face – open-model catalogue
# ---------------------------------------------------------------------------

# Curated list of models available via HuggingFace Inference API.
# Fields: id, name, category, context_window, tool_calling, streaming, notes
HF_OPEN_MODELS: List[Dict[str, Any]] = [
    # ── Instruction-tuned general ──────────────────────────────────────────
    {"id": "mistralai/Mistral-7B-Instruct-v0.3",       "name": "Mistral 7B Instruct v0.3",       "category": "general",    "context": 32768,  "tool_calling": True,  "streaming": True,  "notes": "default; native function calling"},
    {"id": "mistralai/Mixtral-8x7B-Instruct-v0.1",     "name": "Mixtral 8x7B Instruct",          "category": "general",    "context": 32768,  "tool_calling": True,  "streaming": True,  "notes": "MoE; native function calling"},
    {"id": "mistralai/Mixtral-8x22B-Instruct-v0.1",    "name": "Mixtral 8x22B Instruct",         "category": "general",    "context": 65536,  "tool_calling": True,  "streaming": True,  "notes": "MoE; near GPT-4 quality; native function calling"},
    {"id": "mistralai/Mistral-Nemo-Instruct-2407",      "name": "Mistral Nemo 12B Instruct",      "category": "general",    "context": 128000, "tool_calling": True,  "streaming": True,  "notes": "128k context; native function calling"},
    # ── Meta Llama 3 ──────────────────────────────────────────────────────
    {"id": "meta-llama/Meta-Llama-3-8B-Instruct",      "name": "Llama 3 8B Instruct",            "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "fast, lightweight; prompt-based tools"},
    {"id": "meta-llama/Meta-Llama-3-70B-Instruct",     "name": "Llama 3 70B Instruct",           "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "high quality; prompt-based tools"},
    {"id": "meta-llama/Meta-Llama-3.1-8B-Instruct",    "name": "Llama 3.1 8B Instruct",          "category": "general",    "context": 128000, "tool_calling": True,  "streaming": True,  "notes": "128k context; native function calling"},
    {"id": "meta-llama/Meta-Llama-3.1-70B-Instruct",   "name": "Llama 3.1 70B Instruct",         "category": "general",    "context": 128000, "tool_calling": True,  "streaming": True,  "notes": "128k context; native function calling"},
    {"id": "meta-llama/Meta-Llama-3.1-405B-Instruct",  "name": "Llama 3.1 405B Instruct",        "category": "general",    "context": 128000, "tool_calling": True,  "streaming": True,  "notes": "largest open model; PRO required; native function calling"},
    {"id": "meta-llama/Llama-3.2-1B-Instruct",         "name": "Llama 3.2 1B Instruct",          "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "ultra-light edge model; prompt-based tools"},
    {"id": "meta-llama/Llama-3.2-3B-Instruct",         "name": "Llama 3.2 3B Instruct",          "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "edge-friendly; prompt-based tools"},
    # ── Code ──────────────────────────────────────────────────────────────
    {"id": "bigcode/starcoder2-15b-instruct-v0.1",     "name": "StarCoder2 15B Instruct",        "category": "code",       "context": 16384,  "tool_calling": False, "streaming": True,  "notes": "code generation & completion; prompt-based tools"},
    {"id": "Qwen/Qwen2.5-Coder-7B-Instruct",           "name": "Qwen 2.5 Coder 7B Instruct",     "category": "code",       "context": 32768,  "tool_calling": True,  "streaming": True,  "notes": "strong coding; native function calling"},
    {"id": "Qwen/Qwen2.5-Coder-32B-Instruct",          "name": "Qwen 2.5 Coder 32B Instruct",    "category": "code",       "context": 32768,  "tool_calling": True,  "streaming": True,  "notes": "top open code model; native function calling"},
    {"id": "deepseek-ai/deepseek-coder-33b-instruct",  "name": "DeepSeek Coder 33B Instruct",    "category": "code",       "context": 16384,  "tool_calling": False, "streaming": True,  "notes": "competitive code assistant; prompt-based tools"},
    # ── Qwen general ──────────────────────────────────────────────────────
    {"id": "Qwen/Qwen2.5-7B-Instruct",                 "name": "Qwen 2.5 7B Instruct",           "category": "general",    "context": 32768,  "tool_calling": True,  "streaming": True,  "notes": "multilingual; native function calling"},
    {"id": "Qwen/Qwen2.5-72B-Instruct",                "name": "Qwen 2.5 72B Instruct",          "category": "general",    "context": 32768,  "tool_calling": True,  "streaming": True,  "notes": "near GPT-4 quality; native function calling"},
    # ── Phi (Microsoft) ───────────────────────────────────────────────────
    {"id": "microsoft/Phi-3-mini-4k-instruct",         "name": "Phi-3 Mini 4K Instruct",         "category": "general",    "context": 4096,   "tool_calling": False, "streaming": True,  "notes": "3.8B, efficient small model"},
    {"id": "microsoft/Phi-3-medium-128k-instruct",     "name": "Phi-3 Medium 128K Instruct",     "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "14B, 128k context"},
    {"id": "microsoft/Phi-3.5-mini-instruct",          "name": "Phi-3.5 Mini Instruct",          "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "3.8B, multilingual"},
    # ── Gemma (Google) ────────────────────────────────────────────────────
    {"id": "google/gemma-2-2b-it",                     "name": "Gemma 2 2B Instruct",            "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "tiny but capable"},
    {"id": "google/gemma-2-9b-it",                     "name": "Gemma 2 9B Instruct",            "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "strong 9B model"},
    {"id": "google/gemma-2-27b-it",                    "name": "Gemma 2 27B Instruct",           "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "top Gemma, near 70B quality"},
    # ── Math / Reasoning ──────────────────────────────────────────────────
    {"id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",  "name": "DeepSeek R1 Distill Qwen 7B",   "category": "reasoning",  "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "chain-of-thought reasoning"},
    {"id": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B","name": "DeepSeek R1 Distill Llama 70B", "category": "reasoning",  "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "top open reasoning model"},
    # ── Embeddings ────────────────────────────────────────────────────────
    {"id": "BAAI/bge-m3",                              "name": "BGE-M3",                         "category": "embedding",  "context": 8192,   "tool_calling": False, "streaming": False, "notes": "multilingual, multi-granularity"},
    {"id": "sentence-transformers/all-MiniLM-L6-v2",   "name": "all-MiniLM-L6-v2",              "category": "embedding",  "context": 512,    "tool_calling": False, "streaming": False, "notes": "fast, lightweight embeddings"},
    {"id": "intfloat/multilingual-e5-large-instruct",  "name": "Multilingual E5 Large Instruct", "category": "embedding",  "context": 512,    "tool_calling": False, "streaming": False, "notes": "100+ languages"},
]

# Index by category for quick lookup
_HF_MODELS_BY_CATEGORY: Dict[str, List[Dict[str, Any]]] = {}
for _m in HF_OPEN_MODELS:
    _HF_MODELS_BY_CATEGORY.setdefault(_m["category"], []).append(_m)

# Set of model IDs with native function calling support
_HF_NATIVE_TOOL_MODELS: set = {
    m["id"] for m in HF_OPEN_MODELS if m["tool_calling"]
}


def list_huggingface_models(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return curated HuggingFace open models, optionally filtered by category.

    Categories: general, code, reasoning, embedding.
    """
    if category:
        return [m for m in HF_OPEN_MODELS if m["category"] == category]
    return list(HF_OPEN_MODELS)


def hf_model_supports_tools(model_id: str) -> bool:
    """Return True if the model supports native function calling via chat_completion."""
    return model_id in _HF_NATIVE_TOOL_MODELS


# ---------------------------------------------------------------------------
# Hugging Face – provider
# ---------------------------------------------------------------------------

class HuggingFaceLLMProvider(BaseLLMProvider):
    """Hugging Face Inference API. Uses prompt-engineering for tool use."""

    name = "huggingface"
    aliases = ("hf", "hugging-face")
    supports_images = True

    SUPPORTED_MODELS: Tuple[str, ...] = tuple(
        m["id"] for m in HF_OPEN_MODELS if m["category"] != "embedding"
    )

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        super().__init__(api_key, model, **options)
        try:
            from huggingface_hub import InferenceClient  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Package 'huggingface-hub' not found. Install with: pip install 'mangaba[huggingface]'") from exc
        self._client = InferenceClient(token=api_key)

    @classmethod
    def list_models(cls, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return curated open models available via HuggingFace Inference API."""
        return list_huggingface_models(category=category)

    def _chat_messages(self, prompt: str, images: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        msgs: List[Dict[str, Any]] = []
        if self._system_prompt:
            msgs.append({"role": "system", "content": self._system_prompt})
        msgs.append({"role": "user", "content": _openai_user_content(prompt, images)})
        return msgs

    def generate(self, prompt: str, images: Optional[List[Any]] = None, **kwargs: Any) -> LLMResponse:
        try:
            response = self._client.chat_completion(
                messages=self._chat_messages(prompt, images),
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
            )
        except Exception as exc:
            raise LLMError(f"HuggingFace error: {exc}", cause=exc) from exc

        choice = response.choices[0]
        text = choice.message.content or ""
        usage = getattr(response, "usage", None)
        token_usage = TokenUsage(
            prompt_tokens=getattr(usage, "prompt_tokens", 0),
            completion_tokens=getattr(usage, "completion_tokens", 0),
            total_tokens=getattr(usage, "total_tokens", 0),
        ) if usage else TokenUsage()
        return LLMResponse(content=text, model=self.model, usage=token_usage, raw=response)

    def _supports_native_tools(self) -> bool:
        return hf_model_supports_tools(self.model)

    def _openai_tool_schema(self, tool: Any) -> Dict[str, Any]:
        schema = tool.get_function_schema()
        return {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema.get("parameters", {"type": "object", "properties": {}}),
            },
        }

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        tool_list = tools or []

        if self._supports_native_tools() and tool_list:
            # Native function calling via chat_completion tools parameter
            hf_tools = [self._openai_tool_schema(t) for t in tool_list]
            try:
                response = self._client.chat_completion(
                    messages=messages,
                    model=self.model,
                    tools=hf_tools,
                    max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                    temperature=kwargs.get("temperature", self._temperature),
                )
            except Exception as exc:
                raise LLMError(f"HuggingFace error: {exc}", cause=exc) from exc

            choice = response.choices[0]
            native_calls = getattr(choice.message, "tool_calls", None) or []
            if native_calls:
                tool_calls = [
                    ToolCall(
                        tool_name=c.function.name,
                        arguments=json.loads(c.function.arguments) if isinstance(c.function.arguments, str) else c.function.arguments,
                    )
                    for c in native_calls
                ]
                return LLMResponse(
                    content=choice.message.content or "",
                    tool_calls=tool_calls,
                    model=self.model,
                    finish_reason=FinishReason.TOOL_CALLS,
                    raw=response,
                )
            return LLMResponse(content=choice.message.content or "", model=self.model, raw=response)

        # Fallback: inject tool descriptions into system message (prompt-based)
        tool_section = _tools_to_hf_prompt_section(tool_list)
        enriched: List[Dict[str, Any]] = []
        injected = False
        for m in messages:
            if m.get("role") == "system" and tool_section:
                enriched.append({"role": "system", "content": f"{m['content']}\n\n{tool_section}"})
                injected = True
            else:
                enriched.append(m)
        if not injected and tool_section:
            enriched.insert(0, {"role": "system", "content": tool_section})

        try:
            response = self._client.chat_completion(
                messages=enriched,
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
            )
        except Exception as exc:
            raise LLMError(f"HuggingFace error: {exc}", cause=exc) from exc

        text = response.choices[0].message.content or ""
        tool_calls = self._try_parse_tool_calls(text)
        if tool_calls:
            return LLMResponse(
                content=text, tool_calls=tool_calls,
                model=self.model, finish_reason=FinishReason.TOOL_CALLS, raw=response,
            )
        return LLMResponse(content=text, model=self.model, raw=response)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        try:
            for chunk in self._client.chat_completion(
                messages=self._chat_messages(prompt),
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                stream=True,
            ):
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except Exception as exc:
            raise LLMError(f"HuggingFace streaming error: {exc}", cause=exc) from exc

    @staticmethod
    def _try_parse_tool_calls(text: str) -> List[ToolCall]:
        """Attempt to extract tool_calls JSON from model output."""
        try:
            # Find JSON block in output
            start = text.find("{")
            end = text.rfind("}") + 1
            if start < 0 or end <= start:
                return []
            data = json.loads(text[start:end])
            calls = data.get("tool_calls", [])
            return [
                ToolCall(tool_name=c["tool_name"], arguments=c.get("arguments", {}))
                for c in calls if isinstance(c, dict) and "tool_name" in c
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []



# ---------------------------------------------------------------------------
# OpenRouter
# ---------------------------------------------------------------------------

class OpenRouterLLMProvider(OpenAILLMProvider):
    """
    OpenRouter provider implementation for Mangaba AI.
    Handles native fallback routing by formatting the OpenAI SDK payload 
    specifically for OpenRouter's requirements.
    """

    name = "openrouter"
    aliases = ("or", "open-router")

    def __init__(self, api_key: str, model: Union[str, List[str]], **options: Any) -> None:
        # Configuration defaults for the OpenRouter endpoint
        base_url = options.get("base_url") or "https://openrouter.ai/api/v1"
        site_url = options.get("site_url", "https://www.mangaba.ia.br/")
        site_name = options.get("site_name", "Mangaba AI")

        # Initialize base OpenAI provider
        super().__init__(api_key, model, **options)

        from openai import OpenAI
        # Re-initialize the client with OpenRouter's base_url and identity headers
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": site_url,
                "X-Title": site_name,
            }
        )

    def _get_call_params(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Ensures the 'model' is a single string and the fallback list 
        is moved to 'extra_body' to satisfy OpenRouter's API.
        """
        # Ensure we have a string for the SDK's 'model' parameter
        if isinstance(self.model, list):
            primary_model = self.model[0]
            # OpenRouter fallback list goes into extra_body.models
            extra_body = kwargs.get("extra_body", {})
            extra_body["models"] = self.model
            kwargs["extra_body"] = extra_body
        else:
            primary_model = self.model

        # Extract standard generation options
        params = {
            "model": primary_model,
            "temperature": kwargs.get("temperature", self._temperature),
            "max_tokens": kwargs.get("max_output_tokens", self._max_tokens),
            "extra_body": kwargs.get("extra_body"),
            "stream": kwargs.get("stream", False),
        }
        
        # Merge any other extra arguments (like top_p, etc)
        return {k: v for k, v in params.items() if v is not None}

    def generate(self, prompt: str, images: Optional[List[Any]] = None, **kwargs: Any) -> LLMResponse:
        # Build standard message format
        messages = self._build_messages(prompt, kwargs.pop("system_prompt", None), images)
        params = self._get_call_params(**kwargs)
        
        try:
            # We call the client directly to avoid parent class parameter conflicts
            resp = self._client.chat.completions.create(
                messages=messages,
                **params
            )
            usage = self._parse_usage(resp)
            return LLMResponse(
                content=resp.choices[0].message.content or "", 
                usage=usage, 
                model=params["model"], 
                raw=resp
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenRouter generation error: {exc}", cause=exc) from exc

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        # Critical for the ReActEngine to work with fallbacks
        params = self._get_call_params(**kwargs)
        
        # Convert Mangaba tools to OpenAI-compatible schemas
        if tools:
            params["tools"] = [_tool_to_openai_schema(t) for t in tools]

        try:
            resp = self._client.chat.completions.create(
                messages=messages,
                **params
            )
            
            msg = resp.choices[0].message
            tool_calls: List[ToolCall] = []
            
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    import json
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    tool_calls.append(ToolCall(id=tc.id, tool_name=tc.function.name, arguments=args))

            finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
            usage = self._parse_usage(resp)
            
            return LLMResponse(
                content=msg.content or "",
                tool_calls=tool_calls,
                usage=usage,
                model=params["model"],
                finish_reason=finish,
                raw=resp
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenRouter tool-use error: {exc}", cause=exc) from exc


# ---------------------------------------------------------------------------
# Local models – shared helpers
# ---------------------------------------------------------------------------

#: Default endpoint exposed by a local Ollama daemon (OpenAI-compatible surface).
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434/v1"

#: Placeholder credential – local servers ignore it, but the OpenAI SDK
#: refuses to build a client without *some* api_key.
LOCAL_API_KEY_PLACEHOLDER = "ollama"

#: Model families served by Ollama that expose native tool calling.
#: Matched as a prefix against the model name (``llama3.1:8b`` -> ``llama3.1``).
OLLAMA_NATIVE_TOOL_FAMILIES: Tuple[str, ...] = (
    "llama3.1", "llama3.2", "llama3.3", "llama4",
    "mistral", "mistral-nemo", "mistral-small", "mistral-large", "mixtral",
    "qwen2.5", "qwen2.5-coder", "qwen3", "qwq",
    "command-r", "command-r-plus",
    "firefunction", "firefunction-v2",
    "hermes3", "nemotron", "nemotron-mini",
    "granite3", "granite3.1", "granite3-dense",
    "smollm2", "athene-v2", "devstral", "cogito", "phi4-mini",
)


def _normalize_ollama_host(base_url: Optional[str]) -> str:
    """Return the daemon root URL (``/v1`` suffix stripped) for native endpoints."""
    url = (base_url or OLLAMA_DEFAULT_BASE_URL).rstrip("/")
    if url.endswith("/v1"):
        url = url[: -len("/v1")]
    return url or "http://localhost:11434"


def ollama_model_supports_tools(model: str) -> bool:
    """Return True when the Ollama model family advertises native tool calling."""
    base = (model or "").split(":", 1)[0].lower()
    base = base.rsplit("/", 1)[-1]
    return any(base == fam or base.startswith(fam) for fam in OLLAMA_NATIVE_TOOL_FAMILIES)


def list_ollama_models(base_url: Optional[str] = None, timeout: float = 5.0) -> List[str]:
    """Return the model names installed on a local Ollama server.

    Queries the daemon's native ``/api/tags`` endpoint (not the OpenAI-compatible
    surface) so it works without any extra dependency.

    Args:
        base_url: Ollama endpoint. Accepts both ``http://localhost:11434`` and
            ``http://localhost:11434/v1``; the ``/v1`` suffix is stripped.
        timeout: Socket timeout in seconds.

    Raises:
        LLMError: When the server is unreachable or answers with an error.
    """
    import urllib.error
    import urllib.request

    host = _normalize_ollama_host(base_url)
    endpoint = f"{host}/api/tags"
    try:
        with urllib.request.urlopen(endpoint, timeout=timeout) as resp:  # nosec B310
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise LLMError(
            f"Ollama server at {host} answered HTTP {exc.code} for /api/tags", cause=exc
        ) from exc
    except Exception as exc:
        raise LLMError(
            f"Could not reach the Ollama server at {host}. "
            "Is it running? Start it with 'ollama serve' (or install it from https://ollama.com).",
            cause=exc,
        ) from exc

    models = payload.get("models") or []
    names = [m.get("name") or m.get("model") or "" for m in models if isinstance(m, dict)]
    return [n for n in names if n]


def _parse_prompted_tool_calls(text: str) -> List[ToolCall]:
    """Extract a ``{"tool_calls": [...]}`` JSON block from raw model output."""
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start < 0 or end <= start:
            return []
        data = json.loads(text[start:end])
        calls = data.get("tool_calls", [])
        return [
            ToolCall(tool_name=c["tool_name"], arguments=c.get("arguments", {}))
            for c in calls if isinstance(c, dict) and "tool_name" in c
        ]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return []


def _is_tools_unsupported_error(exc: Exception) -> bool:
    """True when a server rejected the request because the model has no tool support."""
    msg = str(exc).lower()
    return "tool" in msg and any(
        marker in msg
        for marker in ("does not support", "not supported", "unsupported", "no support")
    )


# ---------------------------------------------------------------------------
# OpenAI-compatible servers (vLLM, LM Studio, llama.cpp, LocalAI, …)
# ---------------------------------------------------------------------------

class OpenAICompatibleLLMProvider(OpenAILLMProvider):
    """Any self-hosted server that speaks the OpenAI ``/v1/chat/completions`` API.

    Works with vLLM, LM Studio, llama.cpp ``server``, LocalAI,
    text-generation-webui and friends. ``base_url`` is mandatory::

        client = create_llm_client(
            provider="vllm",
            api_key="",                       # most local servers ignore it
            model="meta-llama/Llama-3.1-8B-Instruct",
            base_url="http://localhost:8000/v1",
        )
    """

    name = "openai-compatible"
    aliases = (
        "openai_compatible", "openai-compat", "compatible",
        "vllm", "lmstudio", "lm-studio", "llamacpp", "llama-cpp",
        "localai", "local-ai", "text-generation-webui", "tgi",
    )
    requires_api_key = False

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        base_url = options.get("base_url")
        if not base_url:
            raise ConfigurationError(
                f"Provider '{self.name}' requires a 'base_url' option pointing at the "
                "OpenAI-compatible server (e.g. base_url='http://localhost:8000/v1')."
            )
        self.base_url = str(base_url).rstrip("/")

        super().__init__(api_key or LOCAL_API_KEY_PLACEHOLDER, model, **options)

        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Package 'openai' not found. Install with: pip install openai") from exc

        client_kwargs: Dict[str, Any] = {
            "api_key": api_key or LOCAL_API_KEY_PLACEHOLDER,
            "base_url": self.base_url,
        }
        if options.get("timeout") is not None:
            client_kwargs["timeout"] = options["timeout"]
        if options.get("default_headers"):
            client_kwargs["default_headers"] = options["default_headers"]
        self._client = OpenAI(**client_kwargs)

    # -- generation ----------------------------------------------------------

    def generate(self, prompt: str, images: Optional[List[Any]] = None, **kwargs: Any) -> LLMResponse:
        msgs = self._build_messages(prompt, kwargs.pop("system_prompt", None), images)
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"{self.name} error at {self.base_url}: {exc}", cause=exc) from exc

        text = resp.choices[0].message.content or ""
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, usage=usage, model=self.model, raw=resp)

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        tool_list = tools or []
        create_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self._temperature),
            "max_tokens": kwargs.get("max_output_tokens", self._max_tokens),
        }
        if tool_list:
            create_kwargs["tools"] = [_tool_to_openai_schema(t) for t in tool_list]

        try:
            resp = self._client.chat.completions.create(**create_kwargs)
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"{self.name} error at {self.base_url}: {exc}", cause=exc) from exc

        return self._response_from_completion(resp)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        msgs = self._build_messages(prompt, kwargs.pop("system_prompt", None))
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                content = getattr(delta, "content", None) if delta else None
                if content:
                    yield content
        except Exception as exc:
            raise LLMError(f"{self.name} streaming error at {self.base_url}: {exc}", cause=exc) from exc

    def count_tokens(self, text: str) -> int:
        # Local models use their own tokenizers; tiktoken would be misleading.
        return BaseLLMProvider.count_tokens(self, text)

    # -- internal ------------------------------------------------------------

    def _response_from_completion(self, resp: Any) -> LLMResponse:
        """Map an OpenAI-shaped chat completion into an ``LLMResponse``."""
        msg = resp.choices[0].message
        text = getattr(msg, "content", None) or ""
        tool_calls: List[ToolCall] = []
        for tc in getattr(msg, "tool_calls", None) or []:
            raw_args = tc.function.arguments
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError:
                    log.warning("Could not decode tool arguments from %s: %r", self.name, raw_args)
                    args = {}
            else:
                args = raw_args or {}
            call_id = getattr(tc, "id", None)
            tool_calls.append(
                ToolCall(id=call_id, tool_name=tc.function.name, arguments=args)
                if call_id else ToolCall(tool_name=tc.function.name, arguments=args)
            )

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(resp)
        return LLMResponse(
            content=text, tool_calls=tool_calls, usage=usage,
            model=self.model, finish_reason=finish, raw=resp,
        )

    def _parse_usage(self, resp: Any) -> TokenUsage:
        usage = getattr(resp, "usage", None)
        if not usage:
            return TokenUsage()
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        total = getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens)
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
        )


# ---------------------------------------------------------------------------
# Ollama (local models)
# ---------------------------------------------------------------------------

class OllamaLLMProvider(OpenAICompatibleLLMProvider):
    """Local models served by the Ollama daemon.

    Uses Ollama's OpenAI-compatible ``/v1`` surface through the ``openai`` SDK
    (already a hard dependency), so no extra package is needed::

        client = create_llm_client(provider="ollama", api_key="", model="llama3.1")

    Tool calling uses Ollama's native function calling for model families that
    support it and falls back to prompt injection for the ones that do not,
    mirroring :class:`HuggingFaceLLMProvider`.
    """

    name = "ollama"
    aliases = ("local",)
    requires_api_key = False

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        options = dict(options)
        options["base_url"] = options.get("base_url") or OLLAMA_DEFAULT_BASE_URL
        self._native_tools_override: Optional[bool] = options.get("supports_tools")
        super().__init__(api_key or LOCAL_API_KEY_PLACEHOLDER, model, **options)
        #: Root URL of the daemon (no ``/v1``), used by the native endpoints.
        self.host = _normalize_ollama_host(self.base_url)

    # -- discovery -----------------------------------------------------------

    @classmethod
    def list_models(cls, base_url: Optional[str] = None) -> List[str]:
        """Return the models installed on the local Ollama server."""
        return list_ollama_models(base_url=base_url)

    def _supports_native_tools(self) -> bool:
        if self._native_tools_override is not None:
            return bool(self._native_tools_override)
        return ollama_model_supports_tools(self.model)

    # -- generation ----------------------------------------------------------

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        tool_list = tools or []

        if tool_list and self._supports_native_tools():
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=[_tool_to_openai_schema(t) for t in tool_list],
                    temperature=kwargs.get("temperature", self._temperature),
                    max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                )
            except Exception as exc:
                if not _is_tools_unsupported_error(exc):
                    self._handle_openai_error(exc)
                    raise LLMError(f"Ollama error at {self.base_url}: {exc}", cause=exc) from exc
                log.warning(
                    "Ollama model '%s' rejected native tools (%s); falling back to prompt injection.",
                    self.model, exc,
                )
            else:
                return self._response_from_completion(resp)

        if not tool_list:
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=kwargs.get("temperature", self._temperature),
                    max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                )
            except Exception as exc:
                self._handle_openai_error(exc)
                raise LLMError(f"Ollama error at {self.base_url}: {exc}", cause=exc) from exc
            return self._response_from_completion(resp)

        # Fallback: describe the tools in the system message (prompt-based).
        enriched = self._inject_tool_prompt(messages, tool_list)
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=enriched,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"Ollama error at {self.base_url}: {exc}", cause=exc) from exc

        text = resp.choices[0].message.content or ""
        usage = self._parse_usage(resp)
        tool_calls = _parse_prompted_tool_calls(text)
        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        return LLMResponse(
            content=text, tool_calls=tool_calls, usage=usage,
            model=self.model, finish_reason=finish, raw=resp,
        )

    @staticmethod
    def _inject_tool_prompt(
        messages: List[Dict[str, Any]],
        tools: List[Any],
    ) -> List[Dict[str, Any]]:
        """Append the tool catalogue to the system message (prompt-based tool use)."""
        tool_section = _tools_to_hf_prompt_section(tools)
        if not tool_section:
            return list(messages)
        enriched: List[Dict[str, Any]] = []
        injected = False
        for m in messages:
            if m.get("role") == "system" and not injected:
                enriched.append({"role": "system", "content": f"{m.get('content', '')}\n\n{tool_section}"})
                injected = True
            else:
                enriched.append(m)
        if not injected:
            enriched.insert(0, {"role": "system", "content": tool_section})
        return enriched


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {
    GoogleLLMProvider.name: GoogleLLMProvider,
    OpenAILLMProvider.name: OpenAILLMProvider,
    AnthropicLLMProvider.name: AnthropicLLMProvider,
    HuggingFaceLLMProvider.name: HuggingFaceLLMProvider,
    OpenRouterLLMProvider.name: OpenRouterLLMProvider,
    OllamaLLMProvider.name: OllamaLLMProvider,
    OpenAICompatibleLLMProvider.name: OpenAICompatibleLLMProvider,
}


def _resolve_provider_class(provider_name: str) -> Type[BaseLLMProvider]:
    normalized = provider_name.lower()
    for name, provider_cls in PROVIDERS.items():
        if provider_cls.matches(normalized):
            return provider_cls
    supported = ", ".join(sorted(PROVIDERS.keys()))
    raise ValueError(f"LLM provider '{provider_name}' not supported. Valid options: {supported}")


# ---------------------------------------------------------------------------
# High-level client
# ---------------------------------------------------------------------------

class LLMClient:
    """Unified high-level LLM client with tool use and streaming support."""

    def __init__(self, provider: str, api_key: str, model: str, **options: Any) -> None:
        provider_cls = _resolve_provider_class(provider)
        self.provider_name = provider_cls.name
        self._provider = provider_cls(api_key=api_key, model=model, **options)
        self._usage_tracker: List[TokenUsage] = []

    # -- basic generation ---------------------------------------------------

    def generate(self, prompt: str, images: Optional[List[Any]] = None, **kwargs: Any) -> LLMResponse:
        if images:
            # Contract: callers (e.g. Agent._describe_images) catch TypeError and
            # translate it into "pick a vision-capable provider".
            if not self._provider.supports_images:
                self._provider._reject_images(images)
            kwargs["images"] = images
        EventBus.emit(Event(event_type=EventType.LLM_START, data={"prompt_preview": prompt[:200], "provider": self.provider_name}))
        try:
            resp = self._provider.generate(prompt, **kwargs)
            self._track_usage(resp.usage)
            EventBus.emit(Event(
                event_type=EventType.LLM_END,
                data=self._usage_event_data(resp),
            ))
            return resp
        except Exception as exc:
            EventBus.emit(Event(event_type=EventType.LLM_ERROR, data={"error": str(exc)}))
            raise

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        return self.generate(prompt, **kwargs).text

    def _usage_event_data(self, resp: LLMResponse) -> Dict[str, Any]:
        """Build the LLM_END payload.

        Tracing backends bill and chart input and output tokens separately, so
        report both directions and the model rather than only a total.
        """
        return {
            "tokens": resp.usage.total_tokens,
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "model": resp.model or "",
            "provider": self.provider_name,
            "finish_reason": resp.finish_reason.value,
        }

    # -- tool use -----------------------------------------------------------

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        EventBus.emit(Event(
            event_type=EventType.LLM_START,
            data={"mode": "tool_use", "tools_count": len(tools or []), "provider": self.provider_name},
        ))
        try:
            resp = self._provider.generate_with_tools(messages, tools, **kwargs)
            self._track_usage(resp.usage)
            EventBus.emit(Event(
                event_type=EventType.LLM_END,
                data=dict(self._usage_event_data(resp), tool_calls=len(resp.tool_calls)),
            ))
            return resp
        except Exception as exc:
            EventBus.emit(Event(event_type=EventType.LLM_ERROR, data={"error": str(exc)}))
            raise

    # -- streaming ----------------------------------------------------------

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        return self._provider.stream(prompt, **kwargs)

    # -- token counting -----------------------------------------------------

    def count_tokens(self, text: str) -> int:
        return self._provider.count_tokens(text)

    # -- usage tracking -----------------------------------------------------

    @property
    def total_usage(self) -> TokenUsage:
        total = TokenUsage()
        for u in self._usage_tracker:
            total.prompt_tokens += u.prompt_tokens
            total.completion_tokens += u.completion_tokens
            total.total_tokens += u.total_tokens
        return total

    def _track_usage(self, usage: TokenUsage) -> None:
        if usage.total_tokens > 0:
            self._usage_tracker.append(usage)



# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_llm_client(provider: str, api_key: str, model: str, **options: Any) -> LLMClient:
    """
    Create a unified LLM client for the specified provider.
    
    Supported providers:
    - "google" / "gemini": Google Gemini models
    - "openai": OpenAI GPT models
    - "anthropic": Anthropic Claude models
    - "huggingface" / "hf": HuggingFace Inference API models
    - "openrouter" / "or" / "open-router": OpenRouter models (uses OpenAI-compatible API)
    - "ollama" / "local": models served by a local Ollama daemon
    - "openai-compatible" / "vllm" / "lmstudio" / "llamacpp" / "localai":
      any self-hosted OpenAI-compatible server

    Args:
        provider: Provider name (see supported providers above)
        api_key: API key for the provider (optional for local providers)
        model: Model name/ID (e.g., "gpt-4o", "anthropic/claude-3-haiku")
        **options: Provider-specific options (e.g., base_url, temperature, max_tokens)

    For OpenRouter:
        - Use model format like "openai/gpt-4o" or "anthropic/claude-3-haiku"
        - Optional: base_url (default: https://openrouter.ai/api/v1)
        - Optional: site_url, site_name for OpenRouter headers

    For Ollama:
        - api_key may be empty; base_url defaults to http://localhost:11434/v1
        - Use ``list_ollama_models()`` to discover installed models

    For OpenAI-compatible servers:
        - base_url is REQUIRED (e.g. http://localhost:8000/v1 for vLLM)

    Returns:
        LLMClient instance with generate/generate_with_tools methods
    """
    if not provider:
        raise ValueError("LLM provider name is required")
    if not model:
        raise ValueError("Model name is required")
    if not api_key and _resolve_provider_class(provider).requires_api_key:
        raise ValueError("API key is required to initialise LLM provider")
    return LLMClient(provider=provider, api_key=api_key, model=model, **options)


def get_supported_providers() -> Tuple[str, ...]:
    aliases: set[str] = set()
    for provider_cls in PROVIDERS.values():
        aliases.add(provider_cls.name)
        aliases.update(provider_cls.aliases)
    return tuple(sorted(aliases))
