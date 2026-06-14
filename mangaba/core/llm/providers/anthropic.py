"""Provedor Anthropic para integração de LLM."""

from typing import Any, Dict, Iterator, List, Optional


from mangaba.core.llm.base import BaseLLMProvider
from mangaba.core.types import LLMResponse, TokenUsage, ToolCall, FinishReason
from mangaba.core.exceptions import (
    LLMError,
    AuthenticationError,
    RateLimitError,
    RetryableError,
)

from .schemas import _tool_to_anthropic_schema


class AnthropicLLMProvider(BaseLLMProvider):
    name = "anthropic"
    aliases = ("claude",)

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Inicializa o provedor LLM Anthropic.

        Args:
            api_key: Chave de API da Anthropic.
            model: Nome do modelo (por exemplo, "claude-3-haiku", "claude-3-opus").
            **options: Opções adicionais específicas do provedor.

        Raises:
            ImportError: Se o pacote anthropic não estiver instalado.
        """
        super().__init__(api_key, model, **options)
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'anthropic' not found. Install with: pip install anthropic"
            ) from exc
        self._client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Gera uma resposta do Anthropic Claude.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais (max_output_tokens, temperature, system_prompt).

        Returns:
            LLMResponse contendo o texto gerado, metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                system=kwargs.get("system_prompt", self._system_prompt) or "",
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            self._handle_anthropic_error(exc)
            raise LLMError(f"Anthropic error: {exc}", cause=exc) from exc

        parts = [
            getattr(b, "text", "")
            for b in resp.content
            if getattr(b, "type", "") == "text"
        ]
        text = "\n".join(p for p in parts if p)
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, usage=usage, model=self.model, raw=resp)

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Gera uma resposta com suporte a chamada de ferramenta/função.

        Args:
            messages: Lista de dicionários de mensagem com chaves 'role' e 'content'.
            tools: Lista opcional de definições de ferramenta para chamada de função.
            **kwargs: Parâmetros adicionais (max_output_tokens, temperature).

        Returns:
            LLMResponse contendo texto, chamadas de ferramenta (se houver), metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
        anthropic_tools = (
            [_tool_to_anthropic_schema(t) for t in tools] if tools else None
        )
        # Extrair system das mensagens
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
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        tool_name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(resp)
        return LLMResponse(
            content=text,
            tool_calls=tool_calls,
            usage=usage,
            model=self.model,
            finish_reason=finish,
            raw=resp,
        )

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Transmite a resposta token por token.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais (max_output_tokens, temperature, system_prompt).

        Yields:
            str: Tokens de resposta conforme são gerados.

        Raises:
            LLMError: Se a solicitação de streaming falhar.
        """
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
        """Analisa o uso de tokens da resposta Anthropic.

        Args:
            resp: O objeto de resposta da API Anthropic.

        Returns:
            Objeto TokenUsage com prompt_tokens, completion_tokens e total_tokens.
        """
        if hasattr(resp, "usage") and resp.usage:
            return TokenUsage(
                prompt_tokens=getattr(resp.usage, "input_tokens", 0),
                completion_tokens=getattr(resp.usage, "output_tokens", 0),
                total_tokens=getattr(resp.usage, "input_tokens", 0)
                + getattr(resp.usage, "output_tokens", 0),
            )
        return TokenUsage()

    def _handle_anthropic_error(self, exc: Exception) -> None:
        """Converte exceções Anthropic em exceções Mangaba.

        Args:
            exc: A exceção original do SDK Anthropic.

        Raises:
            AuthenticationError: Se a autenticação falhar.
            RateLimitError: Se o limite de taxa for excedido.
            RetryableError: Se o erro for recuperável (timeout, conexão).
        """
        exc_name = type(exc).__name__
        if "AuthenticationError" in exc_name:
            raise AuthenticationError(str(exc), cause=exc) from exc
        if "RateLimitError" in exc_name:
            raise RateLimitError(str(exc), cause=exc) from exc
        if "APITimeoutError" in exc_name or "APIConnectionError" in exc_name:
            raise RetryableError(str(exc), cause=exc) from exc
