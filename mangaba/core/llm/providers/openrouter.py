"""Provedor OpenRouter."""

from typing import Any, Dict, List, Union, Optional

from .openai import OpenAILLMProvider
from mangaba.core.types import LLMResponse, ToolCall, FinishReason
from mangaba.core.exceptions import LLMError
from .schemas import _tool_to_openai_schema


class OpenRouterLLMProvider(OpenAILLMProvider):
    """
    Implementação do provedor OpenRouter para Mangaba AI.
    Manipula o roteamento de fallback nativo formatando o payload do SDK OpenAI
    especificamente para os requisitos do OpenRouter.
    """

    name = "openrouter"
    aliases = ("or", "open-router")

    def __init__(
        self, api_key: str, model: Union[str, List[str]], **options: Any
    ) -> None:
        """Inicializa o provedor LLM OpenRouter.

        O OpenRouter fornece acesso a múltiplos provedores LLM através de uma API unificada.
        Suporta roteamento de fallback de modelo aceitando uma lista de modelos.

        Args:
            api_key: Chave de API do OpenRouter.
            model: Nome do modelo (string) ou lista de modelos para roteamento de fallback.
            **options: Opções adicionais específicas do provedor (base_url, site_url, site_name).
        """
        # Padrões de configuração para o endpoint OpenRouter
        base_url = options.get("base_url") or "https://openrouter.ai/api/v1"
        site_url = options.get("site_url", "https://www.mangaba.ia.br/")
        site_name = options.get("site_name", "Mangaba AI")

        # Inicializar provedor base OpenAI
        super().__init__(api_key, model, **options)

        from openai import OpenAI

        # Reinicializar o cliente com base_url e cabeçalhos de identidade do OpenRouter
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": site_url,
                "X-Title": site_name,
            },
        )

    def _get_call_params(self, **kwargs: Any) -> Dict[str, Any]:
        """Constrói parâmetros de chamada de API para OpenRouter.

        Garante que o 'model' seja uma string única e a lista de fallback
        seja movida para 'extra_body' para satisfazer os requisitos da API do OpenRouter.

        Args:
            **kwargs: Parâmetros adicionais do método chamador.

        Returns:
            Dicionário de parâmetros formatados para a API do OpenRouter.
        """
        # Garantir que temos uma string para o parâmetro 'model' do SDK
        if isinstance(self.model, list):
            primary_model = self.model[0]
            # Lista de fallback do OpenRouter vai para extra_body.models
            extra_body = kwargs.get("extra_body", {})
            extra_body["models"] = self.model
            kwargs["extra_body"] = extra_body
        else:
            primary_model = self.model

        # Extrair opções de geração padrão
        params = {
            "model": primary_model,
            "temperature": kwargs.get("temperature", self._temperature),
            "max_tokens": kwargs.get("max_output_tokens", self._max_tokens),
            "extra_body": kwargs.get("extra_body"),
            "stream": kwargs.get("stream", False),
        }

        # Mesclar quaisquer outros argumentos extras (como top_p, etc)
        return {k: v for k, v in params.items() if v is not None}

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Gera uma resposta a partir do OpenRouter.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais (temperature, max_output_tokens, system_prompt).

        Returns:
            LLMResponse contendo o texto gerado, metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
        # Construir formato de mensagem padrão
        messages = self._build_messages(prompt, kwargs.pop("system_prompt", None))
        params = self._get_call_params(**kwargs)

        try:
            # Chamamos o cliente diretamente para evitar conflitos de parâmetros da classe pai
            resp = self._client.chat.completions.create(messages=messages, **params)
            usage = self._parse_usage(resp)
            return LLMResponse(
                content=resp.choices[0].message.content or "",
                usage=usage,
                model=params["model"],
                raw=resp,
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
        # Crítico para o ReActEngine funcionar com fallbacks
        params = self._get_call_params(**kwargs)

        # Converter ferramentas Mangaba para esquemas compatíveis com OpenAI
        if tools:
            params["tools"] = [_tool_to_openai_schema(t) for t in tools]

        try:
            resp = self._client.chat.completions.create(messages=messages, **params)

            msg = resp.choices[0].message
            tool_calls: List[ToolCall] = []

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    import json

                    args = (
                        json.loads(tc.function.arguments)
                        if tc.function.arguments
                        else {}
                    )
                    tool_calls.append(
                        ToolCall(id=tc.id, tool_name=tc.function.name, arguments=args)
                    )

            finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
            usage = self._parse_usage(resp)

            return LLMResponse(
                content=msg.content or "",
                tool_calls=tool_calls,
                usage=usage,
                model=params["model"],
                finish_reason=finish,
                raw=resp,
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenRouter tool-use error: {exc}", cause=exc) from exc
