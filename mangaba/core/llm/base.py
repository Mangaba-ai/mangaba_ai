"""Classe base abstrata para provedores LLM."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Tuple

from mangaba.core.types import LLMResponse


class BaseLLMProvider(ABC):
    """Interface abstrata para provedores LLM."""

    name: str = "base"
    aliases: Tuple[str, ...] = ()

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Inicializa o provedor LLM.

        Args:
            api_key: Chave de API para o serviço do provedor.
            model: Nome/identificador do modelo a ser usado.
            **options: Opções adicionais específicas do provedor (ex: temperature,
                max_output_tokens, system_prompt).

        Attributes:
            api_key: A chave de API para autenticação.
            model: O nome/identificador do modelo.
            options: Dicionário de opções adicionais.
            _temperature: Temperatura para geração (padrão: 0.7).
            _max_tokens: Máximo de tokens na saída (padrão: 1024).
            _system_prompt: Prompt de sistema opcional para usar.
        """
        self.api_key = api_key
        self.model = model
        self.options = options or {}
        self._temperature = options.get("temperature", 0.7)
        self._max_tokens = options.get("max_output_tokens", 1024)
        self._system_prompt = options.get("system_prompt")

    @classmethod
    def matches(cls, provider_name: str) -> bool:
        """Verifica se o nome do provedor corresponde a este provedor.

        Args:
            provider_name: O nome do provedor a verificar (insensível a maiúsculas).

        Returns:
            True se o nome do provedor corresponder ao nome ou aliases deste provedor,
            False caso contrário.
        """
        n = provider_name.lower()
        return n == cls.name or n in cls.aliases

    # -- API pública ----------------------------------------------------------

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Gera uma resposta do LLM.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais específicos do provedor.

        Returns:
            LLMResponse contendo o texto gerado, metadados de uso e
            informações adicionais.

        Raises:
            NotImplementedError: Este método deve ser implementado por subclasses.
        """
        raise NotImplementedError("generate() must be implemented by subclass")

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Gera uma resposta com suporte opcional de chamada de ferramenta/função.

        Esta implementação padrão extrai conteúdo de usuário das mensagens e
        retorna para generate() simples. Subclasses devem sobrescrever isto para
        implementar suporte nativo de chamada de ferramentas.

        Args:
            messages: Lista de dicionários de mensagem com chaves 'role' e 'content'.
            tools: Lista opcional de definições de ferramenta/função para o LLM usar.
            **kwargs: Parâmetros adicionais específicos do provedor.

        Returns:
            LLMResponse contendo o texto gerado, chamadas de ferramenta (se houver),
            metadados de uso e informações adicionais.
        """
        # Default: ignore tools and fall back to plain generate
        user_content = ""
        for m in messages:
            if m.get("role") == "user":
                user_content = m.get("content", "")
        return self.generate(user_content, **kwargs)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Transmite a resposta token por token.

        Esta implementação padrão gera a resposta completa e a produz
        como um único chunk. Subclasses devem sobrescrever isto para implementar
        streaming verdadeiro token por token.

        Args:
            prompt: O prompt de entrada para gerar uma resposta.
            **kwargs: Parâmetros adicionais específicos do provedor.

        Yields:
            str: Tokens ou chunks de resposta conforme são gerados.
        """
        resp = self.generate(prompt, **kwargs)
        yield resp.text

    def count_tokens(self, text: str) -> int:
        """Estima a contagem de tokens para o texto fornecido.

        Esta implementação padrão usa uma estimativa aproximada baseada em palavras
        (aproximadamente 4 caracteres por token). Subclasses devem sobrescrever
        isto para usar tokenizadores específicos do provedor para contagens precisas.

        Args:
            text: O texto para estimar a contagem de tokens.

        Returns:
            Número estimado de tokens (mínimo 1).
        """
        return max(1, len(text) // 4)
