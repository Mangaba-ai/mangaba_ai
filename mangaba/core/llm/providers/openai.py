"""Provedor OpenAI para integração de LLM."""

import json

from typing import Any, List, Dict, Optional, Iterator
from mangaba.core.llm.base import BaseLLMProvider
from mangaba.core.types import LLMResponse, TokenUsage, FinishReason, ToolCall
from mangaba.core.exceptions import (
    AuthenticationError,
    LLMError,
    RateLimitError,
    RetryableError,
)

from .schemas import _tool_to_openai_schema


class OpenAILLMProvider(BaseLLMProvider):
    name = "openai"
    aliases = ("gpt", "chatgpt")

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Inicializa o provedor LLM OpenAI.

        Args:
            api_key: Chave de API da OpenAI.
            model: Nome do modelo (ex: "gpt-4o", "gpt-4o-mini").
            **options: Opções adicionais específicas do provedor.

        Raises:
            ImportError: Se o pacote openai não estiver instalado.
        """
        super().__init__(api_key, model, **options)
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'openai' not found. Install with: pip install openai"
            ) from exc
        self._client = OpenAI(api_key=api_key)

    def _build_messages(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Constrói mensagens de chat a partir de um prompt simples.

        Args:
            prompt: O prompt do usuário.
            system_prompt: Prompt de sistema opcional para substituir o padrão.

        Returns:
            Lista de dicionários de mensagens com prompt de sistema (se definido) e mensagem do usuário.
        """
        msgs: List[Dict[str, str]] = []
        sp = system_prompt or self._system_prompt
        if sp:
            msgs.append({"role": "system", "content": sp})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Gera uma resposta a partir da OpenAI.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais (temperature, max_output_tokens, system_prompt).

        Returns:
            LLMResponse contendo o texto gerado, metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
        msgs = self._build_messages(prompt, kwargs.pop("system_prompt", None))
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
        """Gera uma resposta com suporte a chamada de ferramentas/funções.

        Args:
            messages: Lista de dicionários de mensagens com chaves 'role' e 'content'.
            tools: Lista opcional de definições de ferramentas para chamada de função.
            **kwargs: Parâmetros adicionais (temperature, max_output_tokens).

        Returns:
            LLMResponse contendo texto, chamadas de ferramenta (se houver), metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
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
                args = (
                    json.loads(tc.function.arguments) if tc.function.arguments else {}
                )
                tool_calls.append(
                    ToolCall(id=tc.id, tool_name=tc.function.name, arguments=args)
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
            **kwargs: Parâmetros adicionais (temperature, max_output_tokens, system_prompt).

        Yields:
            str: Tokens de resposta conforme são gerados.

        Raises:
            LLMError: Se a solicitação de streaming falhar.
        """
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
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            raise LLMError(f"OpenAI streaming error: {exc}", cause=exc) from exc

    def count_tokens(self, text: str) -> int:
        """Conta tokens usando tiktoken para tokenização precisa do modelo OpenAI.

        Args:
            text: O texto para contar os tokens.

        Returns:
            Contagem precisa de tokens usando tiktoken, ou estimativa aproximada se o tiktoken falhar.
        """
        try:
            import tiktoken  # type: ignore

            enc = tiktoken.encoding_for_model(self.model)
            return len(enc.encode(text))
        except Exception:
            return super().count_tokens(text)

    def _parse_usage(self, resp: Any) -> TokenUsage:
        """Analisa o uso de tokens da resposta OpenAI.

        Args:
            resp: O objeto de resposta da API OpenAI.

        Returns:
            Objeto TokenUsage com prompt_tokens, completion_tokens e total_tokens.
        """
        if resp.usage:
            return TokenUsage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
                total_tokens=resp.usage.total_tokens or 0,
            )
        return TokenUsage()

    def _handle_openai_error(self, exc: Exception) -> None:
        """Converte exceções OpenAI para exceções Mangaba.

        Args:
            exc: A exceção original do SDK OpenAI.

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
