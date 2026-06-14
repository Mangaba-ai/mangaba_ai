"""
Hierarquia de exceções para Mangaba AI v3.0

Exceções tipadas para cada subsistema, permitindo tratamento de erros granular
e repetição automática de falhas transitórias.
"""

from __future__ import annotations

from typing import Optional


class MangabaError(Exception):
    """Exceção base para todos os erros do Mangaba.

    Todas as exceções personalizadas no framework herdam desta classe,
    permitindo tratamento de erros granular e captura de erros específicos do framework.

    Attributes:
        cause: Exceção original opcional que causou este erro.
    """

    def __init__(self, message: str, *, cause: Optional[Exception] = None) -> None:
        """Inicializa o erro base do Mangaba.

        Args:
            message: Mensagem de erro legível por humanos.
            cause: Exceção original opcional que causou este erro.

        Attributes:
            cause: A exceção original se fornecida.
        """
        self.cause = cause
        super().__init__(message)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class ConfigurationError(MangabaError):
    """Configuração inválida ou ausente.

    Levantada quando valores de configuração necessários estão ausentes, inválidos,
    ou não podem ser carregados de variáveis de ambiente ou arquivos de configuração.
    """


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------


class LLMError(MangabaError):
    """Erro genérico de provedor LLM.

    Classe base para todos os erros relacionados a LLM incluindo autenticação,
    limitação de taxa, limites de token e problemas de filtragem de conteúdo.
    """


class AuthenticationError(LLMError):
    """Chave de API inválida ou expirada.

    Levantada quando a chave de API fornecida a um provedor LLM é inválida,
    expirada, ou não tem permissões suficientes.
    """


class RetryableError(LLMError):
    """Erro transitório que pode ter sucesso ao repetir.

    Indica uma falha temporária (problemas de rede, timeout, serviço indisponível)
    que pode ser resolvida se a solicitação for repetida com backoff.
    """


class RateLimitError(RetryableError):
    """Limite de taxa do provedor atingido.

    Levantada quando o limite de taxa do provedor LLM foi excedido.
    Inclui informação opcional retry_after para temporização de backoff.

    Attributes:
        retry_after: Segundos opcionais para esperar antes de repetir.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[float] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Inicializa o erro de limite de taxa.

        Args:
            message: Mensagem de erro legível por humanos.
            retry_after: Segundos opcionais para esperar antes de repetir.
            cause: Exceção original opcional que causou este erro.

        Attributes:
            retry_after: O atraso de repetição sugerido em segundos.
        """
        self.retry_after = retry_after
        super().__init__(message, cause=cause)


class TokenLimitError(LLMError):
    """Prompt ou resposta excede o limite de token.

    Levantada quando o prompt e resposta combinados excederiam
    a janela de contexto máximo de token do modelo.
    """


class ContentFilterError(LLMError):
    """Conteúdo bloqueado por filtro de segurança.

    Levantada quando o sistema de moderação de conteúdo do provedor LLM
    bloqueia a entrada ou saída por violações de política.
    """


# ---------------------------------------------------------------------------
# Ferramentas
# ---------------------------------------------------------------------------


class ToolError(MangabaError):
    """Erro durante a execução da ferramenta.

    Classe base para erros que ocorrem ao executar ferramentas,
    incluindo falhas de validação e erros de execução.

    Attributes:
        tool_name: Nome da ferramenta que causou o erro.
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str = "",
        cause: Optional[Exception] = None,
    ) -> None:
        """Inicializa o erro de ferramenta.

        Args:
            message: Mensagem de erro legível por humanos.
            tool_name: Nome da ferramenta que causou o erro.
            cause: Exceção original opcional que causou este erro.

        Attributes:
            tool_name: O nome da ferramenta que causou o erro.
        """
        self.tool_name = tool_name
        super().__init__(message, cause=cause)


class ToolValidationError(ToolError):
    """Validação de entrada de ferramenta falhou.

    Levantada quando os parâmetros de entrada fornecidos não correspondem
    ao esquema esperado ou restrições de tipo da ferramenta.
    """


class ToolNotFoundError(ToolError):
    """Ferramenta solicitada não existe.

    Levantada ao tentar usar uma ferramenta que não foi
    registrada ou não está disponível para o agente.
    """


# ---------------------------------------------------------------------------
# Agente
# ---------------------------------------------------------------------------


class AgentError(MangabaError):
    """Erro na execução do agente.

    Classe base para erros que ocorrem durante operações de agente,
    incluindo limites de iteração, falhas de delegação e erros de execução.
    """


class MaxIterationsError(AgentError):
    """Agente atingiu o limite máximo de iteração.

    Levantada quando o loop de raciocínio ReAct excede o
    max_iterations configurado sem alcançar uma resposta final.
    """


class DelegationError(AgentError):
    """Falha ao delegar tarefa para outro agente.

    Levantada quando um agente tenta delegar uma tarefa mas a delegação
    não pode ser concluída (ex: nenhum agente delegado adequado disponível).
    """


# ---------------------------------------------------------------------------
# Task / Crew
# ---------------------------------------------------------------------------


class TaskError(MangabaError):
    """Erro durante a execução da tarefa.

    Levantada quando uma tarefa não pode ser concluída com sucesso,
    incluindo falhas de agente, timeout ou erros de execução.
    """


class CrewError(MangabaError):
    """Erro na orquestração da crew.

    Levantada quando erros ocorrem durante operações de nível de crew como
    execução de processo, coordenação de agentes ou distribuição de tarefas.
    """


class ValidationError(MangabaError):
    """Falha genérica de validação de dados.

    Levantada quando dados de entrada falham nas verificações de validação, incluindo
    validação de esquema, incompatibilidades de tipo ou violações de restrição.
    """


# ---------------------------------------------------------------------------
# Memory / RAG
# ---------------------------------------------------------------------------


class MemoryError(MangabaError):
    """Erro no subsistema de memória.

    Levantada quando erros ocorrem em operações de memória como armazenamento,
    recuperação ou busca em sistemas de memória de curto ou longo prazo.
    """


class EmbeddingError(MangabaError):
    """Erro ao computar embeddings.

    Levantada quando o modelo de embedding falha ao gerar embeddings
    para texto, devido a erros de modelo, problemas de API ou entrada inválida.
    """


class VectorStoreError(MangabaError):
    """Erro no subsistema de armazenamento vetorial.

    Levantada quando erros ocorrem em operações de banco de dados vetorial como
    inserção, busca ou exclusão de embeddings vetoriais.
    """
