"""Provedor de LLM Google (Gemini)."""

from typing import Any, List, Dict, Optional, Iterator
from mangaba.core.llm.base import BaseLLMProvider
from mangaba.core.types import LLMResponse, TokenUsage, FinishReason, ToolCall
from mangaba.core.exceptions import LLMError
from .schemas import _tool_to_google_declaration


class GoogleLLMProvider(BaseLLMProvider):
    name = "google"
    aliases = ("gemini", "google-ai", "googleai")

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Inicializa o provedor LLM Google Gemini.

        Args:
            api_key: Chave de API do Google AI.
            model: Nome do modelo (por exemplo, "gemini-2.5-flash", "gemini-2.5-pro").
            **options: Opções adicionais específicas do provedor (generation_config, safety_settings).

        Raises:
            ImportError: Se o pacote google-generativeai não estiver instalado.
        """
        super().__init__(api_key, model, **options)
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'google-generativeai' not found. Install with: pip install google-generativeai"
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

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Gera uma resposta do Google Gemini.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais para passar à API.

        Returns:
            LLMResponse contendo o texto gerado, metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
        try:
            response = self._model.generate_content(
                prompt, **{k: v for k, v in kwargs.items() if v is not None}
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
        """Gera uma resposta com suporte a chamada de ferramenta/função.

        Args:
            messages: Lista de dicionários de mensagem com chaves 'role' e 'content'.
            tools: Lista opcional de definições de ferramenta para chamada de função.
            **kwargs: Parâmetros adicionais para passar à API.

        Returns:
            LLMResponse contendo texto, chamadas de ferramenta (se houver), metadados de uso e resposta bruta.

        Raises:
            LLMError: Se a solicitação da API falhar.
        """
        try:
            genai_tools = None
            if tools:
                declarations = [_tool_to_google_declaration(t) for t in tools]
                genai_tools = [
                    self._genai.protos.Tool(
                        function_declarations=[
                            self._genai.protos.FunctionDeclaration(**d)
                            for d in declarations
                        ]
                    )
                ]

            # Construir conteúdos a partir das mensagens
            contents = []
            for m in messages:
                role = "model" if m["role"] == "assistant" else m["role"]
                if role == "system":
                    continue
                contents.append(
                    {"role": role, "parts": [{"text": m.get("content", "")}]}
                )

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
                    tool_calls.append(
                        ToolCall(
                            tool_name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                    )
        except (IndexError, AttributeError):
            text = getattr(response, "text", "") or ""

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(response)
        return LLMResponse(
            content=text,
            tool_calls=tool_calls,
            usage=usage,
            model=self.model,
            finish_reason=finish,
            raw=response,
        )

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Transmite a resposta token por token.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais para passar à API.

        Yields:
            str: Tokens de resposta conforme são gerados.

        Raises:
            LLMError: Se a solicitação de streaming falhar.
        """
        try:
            response = self._model.generate_content(prompt, stream=True)
            for chunk in response:
                txt = getattr(chunk, "text", None) or ""
                if txt:
                    yield txt
        except Exception as exc:
            raise LLMError(f"Google streaming error: {exc}", cause=exc) from exc

    def _parse_usage(self, response: Any) -> TokenUsage:
        """Analisa o uso de tokens da resposta Google.

        Args:
            response: O objeto de resposta da API Google.

        Returns:
            Objeto TokenUsage com prompt_tokens, completion_tokens e total_tokens.
        """
        try:
            um = response.usage_metadata
            return TokenUsage(
                prompt_tokens=getattr(um, "prompt_token_count", 0),
                completion_tokens=getattr(um, "candidates_token_count", 0),
                total_tokens=getattr(um, "total_token_count", 0),
            )
        except Exception:
            return TokenUsage()
