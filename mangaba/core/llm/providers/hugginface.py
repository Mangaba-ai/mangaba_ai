"""Provedor da API de Inferência do Hugging Face."""

import json
from typing import Any, Dict, Iterator, List, Optional, Tuple

from mangaba.core.llm.base import BaseLLMProvider
from mangaba.core.exceptions import LLMError
from mangaba.core.types import FinishReason, LLMResponse, TokenUsage, ToolCall
from .schemas import _tools_to_hf_prompt_section


def list_huggingface_models(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna modelos abertos curados do HuggingFace, opcionalmente filtrados por categoria.

    Args:
        category: Filtro de categoria opcional (general, code, reasoning, embedding).

    Returns:
        Lista de dicionários de modelos com metadados (id, name, category, context, etc.).
    """
    from .constants import HF_OPEN_MODELS

    if category:
        return [m for m in HF_OPEN_MODELS if m["category"] == category]
    return list(HF_OPEN_MODELS)


def hf_model_supports_tools(model_id: str) -> bool:
    """Verifica se um modelo suporta chamada de função nativa via chat_completion.

    Args:
        model_id: O ID do modelo HuggingFace para verificar.

    Returns:
        True se o modelo suporta chamada de função nativa, False caso contrário.
    """
    from .constants import _HF_NATIVE_TOOL_MODELS

    return model_id in _HF_NATIVE_TOOL_MODELS


class HuggingFaceLLMProvider(BaseLLMProvider):
    """API de Inferência do Hugging Face. Usa engenharia de prompt para uso de ferramentas."""

    name = "huggingface"
    aliases = ("hf", "hugging-face")

    @property
    def SUPPORTED_MODELS(self) -> Tuple[str, ...]:
        """Modelos suportados excluindo embeddings."""
        from .constants import HF_OPEN_MODELS

        return tuple(m["id"] for m in HF_OPEN_MODELS if m["category"] != "embedding")

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Inicializa o provedor da API de Inferência do HuggingFace.

        Args:
            api_key: Token de API do HuggingFace.
            model: ID do modelo (por exemplo, "mistralai/Mistral-7B-Instruct-v0.3").
            **options: Opções adicionais específicas do provedor.

        Raises:
            ImportError: Se o pacote huggingface-hub não estiver instalado.
        """
        super().__init__(api_key, model, **options)
        try:
            from huggingface_hub import InferenceClient  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'huggingface-hub' not found. Install with: pip install huggingface-hub"
            ) from exc
        self._client = InferenceClient(token=api_key)

    @classmethod
    def list_models(cls, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retorna modelos abertos curados disponíveis via API de Inferência do HuggingFace.

        Args:
            category: Filtro de categoria opcional (general, code, reasoning, embedding).

        Returns:
            Lista de dicionários de modelos com metadados.
        """
        return list_huggingface_models(category=category)

    def _chat_messages(self, prompt: str) -> List[Dict[str, str]]:
        """Constrói mensagens de chat a partir de um prompt simples.

        Args:
            prompt: O prompt do usuário.

        Returns:
            Lista de dicionários de mensagem com prompt do sistema (se definido) e mensagem do usuário.
        """
        msgs: List[Dict[str, str]] = []
        if self._system_prompt:
            msgs.append({"role": "system", "content": self._system_prompt})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Gera uma resposta da API de Inferência do HuggingFace.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais (max_output_tokens, temperature).

        Returns:
            LLMResponse contendo o texto gerado, metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
        try:
            response = self._client.chat_completion(
                messages=self._chat_messages(prompt),
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
            )
        except Exception as exc:
            raise LLMError(f"HuggingFace error: {exc}", cause=exc) from exc

        choice = response.choices[0]
        text = choice.message.content or ""
        usage = getattr(response, "usage", None)
        token_usage = (
            TokenUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                total_tokens=getattr(usage, "total_tokens", 0),
            )
            if usage
            else TokenUsage()
        )
        return LLMResponse(
            content=text, model=self.model, usage=token_usage, raw=response
        )

    def _supports_native_tools(self) -> bool:
        """Verifica se o modelo atual suporta chamada de função nativa.

        Returns:
            True se o modelo suporta chamada de função nativa, False caso contrário.
        """
        return hf_model_supports_tools(self.model)

    def _openai_tool_schema(self, tool: Any) -> Dict[str, Any]:
        """Converte uma ferramenta para o formato de esquema de função compatível com OpenAI.

        Args:
            tool: Uma instância BaseTool com método get_function_schema().

        Returns:
            Dicionário no formato de chamada de função OpenAI.
        """
        schema = tool.get_function_schema()
        return {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema.get(
                    "parameters", {"type": "object", "properties": {}}
                ),
            },
        }

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Gera uma resposta com suporte a chamada de ferramenta/função.

        Usa chamada de função nativa se o modelo suportar, caso contrário usa
        chamada de ferramenta baseada em prompt injetando descrições de ferramentas na mensagem do sistema.

        Args:
            messages: Lista de dicionários de mensagem com chaves 'role' e 'content'.
            tools: Lista opcional de definições de ferramenta para chamada de função.
            **kwargs: Parâmetros adicionais (max_output_tokens, temperature).

        Returns:
            LLMResponse contendo texto, chamadas de ferramenta (se houver), metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
        tool_list = tools or []

        if self._supports_native_tools() and tool_list:
            # Chamada de função nativa via parâmetro de ferramentas chat_completion
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
                        arguments=json.loads(c.function.arguments)
                        if isinstance(c.function.arguments, str)
                        else c.function.arguments,
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
            return LLMResponse(
                content=choice.message.content or "", model=self.model, raw=response
            )

        # Fallback: injetar descrições de ferramentas na mensagem do sistema (baseado em prompt)
        tool_section = _tools_to_hf_prompt_section(tool_list)
        enriched: List[Dict[str, Any]] = []
        injected = False
        for m in messages:
            if m.get("role") == "system" and tool_section:
                enriched.append(
                    {"role": "system", "content": f"{m['content']}\n\n{tool_section}"}
                )
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
                content=text,
                tool_calls=tool_calls,
                model=self.model,
                finish_reason=FinishReason.TOOL_CALLS,
                raw=response,
            )
        return LLMResponse(content=text, model=self.model, raw=response)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Transmite a resposta token por token.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais (max_output_tokens, temperature).

        Yields:
            str: Tokens de resposta conforme são gerados.

        Raises:
            LLMError: Se a solicitação de streaming falhar.
        """
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
        """Tenta extrair JSON de tool_calls da saída do modelo.

        Usado para fallback de chamada de ferramenta baseada em prompt. Extrai blocos JSON
        contendo chamadas de ferramenta da resposta de texto do modelo.

        Args:
            text: A saída de texto do modelo para analisar.

        Returns:
            Lista de objetos ToolCall extraídos do texto, ou lista vazia se a análise falhar.
        """
        try:
            # Encontrar bloco JSON na saída
            start = text.find("{")
            end = text.rfind("}") + 1
            if start < 0 or end <= start:
                return []
            data = json.loads(text[start:end])
            calls = data.get("tool_calls", [])
            return [
                ToolCall(tool_name=c["tool_name"], arguments=c.get("arguments", {}))
                for c in calls
                if isinstance(c, dict) and "tool_name" in c
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []
