"""
Definições de tipos principais para Mangaba AI v3.0

Modelos Pydantic v2 usados em todo o framework para validação,
serialização e geração de esquema JSON.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Role(str, Enum):
    """Papel da mensagem em uma conversa.

    Define quem enviou uma mensagem em uma conversa de chat:
    - SYSTEM: Instruções/prompt do sistema
    - USER: Entrada do usuário humano
    - ASSISTANT: Resposta do agente de IA
    - TOOL: Resultado da execução da ferramenta
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentStatus(str, Enum):
    """Status atual de execução de um agente.

    - IDLE: O agente não está executando nenhuma tarefa no momento
    - RUNNING: O agente está processando ativamente uma tarefa
    - WAITING_TOOL: O agente está esperando uma ferramenta ser concluída
    - COMPLETED: O agente concluiu a tarefa com sucesso
    - ERROR: O agente encontrou um erro durante a execução
    """
    IDLE = "idle"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    COMPLETED = "completed"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Status de execução de uma tarefa.

    - PENDING: A tarefa está na fila e esperando para começar
    - RUNNING: A tarefa está sendo executada no momento
    - COMPLETED: A tarefa foi concluída com sucesso
    - FAILED: A tarefa falhou com um erro
    - SKIPPED: A tarefa foi pulada (por exemplo, devido a lógica condicional)
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FinishReason(str, Enum):
    """Motivo pelo qual um LLM parou de gerar.

    - STOP: O modelo parou naturalmente a geração
    - TOOL_CALLS: O modelo parou para solicitar chamadas de ferramenta
    - LENGTH: O modelo atingiu o limite máximo de tokens
    - ERROR: A geração falhou devido a um erro
    - CONTENT_FILTER: O conteúdo foi bloqueado por filtros de segurança
    """
    STOP = "stop"
    TOOL_CALLS = "tool_calls"
    LENGTH = "length"
    ERROR = "error"
    CONTENT_FILTER = "content_filter"


# ---------------------------------------------------------------------------
# LLM related
# ---------------------------------------------------------------------------


class LLMConfig(BaseModel):
    """Configuração para um provedor de LLM.

    Attributes:
        provider: Nome do provedor de LLM (por exemplo, 'openai', 'anthropic', 'google').
        model: Nome do modelo ou lista de modelos para fallback (para OpenRouter).
        api_key: Chave de API para o provedor (pode ser None se for de variável de ambiente).
        temperature: Temperatura de amostragem (0.0 a 2.0, padrão 0.7).
        max_tokens: Máximo de tokens na resposta (padrão 1024).
        top_p: Parâmetro de amostragem de núcleo (0.0 a 1.0, padrão 1.0).
        stop_sequences: Lista opcional de sequências que param a geração.
        timeout: Tempo limite de solicitação em segundos (padrão 60).
        base_url: URL base de API personalizada opcional.
    """

    provider: str = "google"
    model: Union[str, List[str]] = "gemini-2.5-flash"
    api_key: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stop_sequences: Optional[List[str]] = None
    timeout: int = Field(default=60, ge=1)
    base_url: Optional[str] = None

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, v: str) -> str:
        """Normaliza o nome do provedor resolvendo aliases.

        Args:
            v: Nome do provedor ou alias.

        Returns:
            Nome do provedor normalizado.
        """
        aliases = {
            "gemini": "google",
            "google-ai": "google",
            "googleai": "google",
            "gpt": "openai",
            "chatgpt": "openai",
            "claude": "anthropic",
            "hf": "huggingface",
            "hugging-face": "huggingface",
            "openrouter": "openrouter",
            "open-router": "openrouter",
            "or": "openrouter",
        }
        return aliases.get(v.lower(), v.lower())


class OpenRouterConfig(LLMConfig):
    """Configuração especializada para OpenRouter com suporte a fallback.

    Estende LLMConfig para suportar o roteamento de fallback multi-modelo
    do OpenRouter e cabeçalhos personalizados.

    Attributes:
        provider: Sempre 'openrouter'.
        model: Lista de modelos para roteamento de fallback (principal primeiro).
        site_name: Nome do aplicativo para cabeçalhos do OpenRouter.
        site_url: URL do aplicativo para cabeçalhos do OpenRouter.
        route: Preferência de roteamento opcional (barato, rápido, etc).
    """

    provider: str = "openrouter"

    # We can define a default fallback list here
    model: List[str] = Field(
        default_factory=lambda: [
            "google/gemini-2.5-flash",
            "anthropic/claude-3.5-sonnet",
        ]
    )

    # Specific OpenRouter headers
    site_name: str = "Mangaba AI"
    site_url: str = "https://www.mangaba.ia.br/"

    # OpenRouter routing preferences (cheap, fast, etc)
    route: Optional[str] = None


class TokenUsage(BaseModel):
    """Estatísticas de uso de tokens de uma chamada de LLM.

    Attributes:
        prompt_tokens: Número de tokens no prompt.
        completion_tokens: Número de tokens na conclusão.
        total_tokens: Total de tokens usados (prompt + conclusão).
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ToolCall(BaseModel):
    """Uma chamada de ferramenta solicitada pelo LLM.

    Attributes:
        id: Identificador único para esta chamada de ferramenta.
        tool_name: Nome da ferramenta a ser chamada.
        arguments: Dicionário de argumentos para passar à ferramenta.
    """

    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Resultado da execução de uma ferramenta.

    Attributes:
        call_id: ID da chamada de ferramenta a que este resultado corresponde.
        tool_name: Nome da ferramenta que foi executada.
        output: A saída da execução da ferramenta.
        error: Mensagem de erro se a execução falhou.
        success: Se a execução da ferramenta foi bem-sucedida.
    """

    call_id: str
    tool_name: str = ""
    output: Any = None
    error: Optional[str] = None
    success: bool = True


class Message(BaseModel):
    """Uma única mensagem em uma conversa.

    Attributes:
        role: O papel do remetente da mensagem (SYSTEM, USER, ASSISTANT, TOOL).
        content: O conteúdo de texto da mensagem.
        tool_calls: Lista de chamadas de ferramenta solicitadas pelo assistente.
        tool_results: Lista de resultados de execução de ferramenta.
        metadata: Metadados adicionais sobre a mensagem.
        timestamp: Timestamp em formato ISO de quando a mensagem foi criada.
    """

    role: Role
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def system(cls, content: str) -> Message:
        """Cria uma mensagem de sistema.

        Args:
            content: O conteúdo da instrução do sistema.

        Returns:
            Uma Message com role=SYSTEM.
        """
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> Message:
        """Cria uma mensagem de usuário.

        Args:
            content: O conteúdo de entrada do usuário.

        Returns:
            Uma Message com role=USER.
        """
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(
        cls, content: Optional[str] = None, tool_calls: Optional[List[ToolCall]] = None
    ) -> Message:
        """Cria uma mensagem de assistente.

        Args:
            content: O conteúdo de resposta do assistente.
            tool_calls: Chamadas de ferramenta opcionais solicitadas pelo assistente.

        Returns:
            Uma Message com role=ASSISTANT.
        """
        return cls(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)

    @classmethod
    def tool(cls, results: List[ToolResult]) -> Message:
        """Cria uma mensagem de resultado de ferramenta.

        Args:
            results: Lista de resultados de execução de ferramenta.

        Returns:
            Uma Message com role=TOOL contendo resultados de ferramenta.
        """
        return cls(role=Role.TOOL, tool_results=results)


class LLMResponse(BaseModel):
    """Resposta padronizada de qualquer provedor de LLM.

    Attributes:
        content: O conteúdo de texto da resposta.
        tool_calls: Lista de chamadas de ferramenta solicitadas pelo LLM.
        usage: Estatísticas de uso de tokens.
        model: O modelo que gerou a resposta.
        finish_reason: Por que o LLM parou de gerar.
        raw: Objeto de resposta bruto do provedor (excluído da serialização).
    """

    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str = ""
    finish_reason: FinishReason = FinishReason.STOP
    raw: Any = Field(default=None, exclude=True)

    @property
    def text(self) -> str:
        """Obtém o conteúdo de texto, padrão para string vazia.

        Returns:
            O conteúdo como uma string, ou string vazia se content for None.
        """
        return self.content or ""

    @property
    def has_tool_calls(self) -> bool:
        """Verifica se a resposta contém chamadas de ferramenta.

        Returns:
            True se houver chamadas de ferramenta, False caso contrário.
        """
        return len(self.tool_calls) > 0


# ---------------------------------------------------------------------------
# Configuração de Agente / Tarefa / Crew
# ---------------------------------------------------------------------------


class MemoryConfig(BaseModel):
    """Configuração de memória para um agente.

    Attributes:
        short_term: Habilita memória de curto prazo (contexto na conversa).
        long_term: Habilita armazenamento de memória persistente de longo prazo.
        entity: Habilita extração e rastreamento de entidades.
        max_short_term_items: Máximo de itens na memória de curto prazo.
        storage_path: Caminho opcional para armazenamento persistente.
    """

    short_term: bool = True
    long_term: bool = False
    entity: bool = False
    max_short_term_items: int = Field(default=50, ge=1)
    storage_path: Optional[str] = None


class AgentConfig(BaseModel):
    """Configuração completa para um Agente.

    Attributes:
        role: O papel/profissão do agente.
        goal: O objetivo principal do agente.
        backstory: Contexto e histórico sobre o agente.
        llm_config: Configuração opcional do provedor de LLM.
        tools: Lista de nomes de ferramentas disponíveis para o agente.
        memory_config: Configuração de memória para o agente.
        max_iterations: Máximo de iterações do loop de raciocínio ReAct.
        max_retry_on_error: Máximo de tentativas de retry em erros.
        verbose: Habilita registro detalhado.
        allow_delegation: Permite que o agente delegue para outros agentes.
        step_callback: Função de callback opcional para cada etapa.
        guardrails: Lista de nomes de guardrails para aplicar.
        output_parser: Nome do analisador de saída opcional para usar.
    """

    role: str
    goal: str
    backstory: str
    llm_config: Optional[LLMConfig] = None
    tools: List[str] = Field(default_factory=list)
    memory_config: MemoryConfig = Field(default_factory=MemoryConfig)
    max_iterations: int = Field(default=15, ge=1)
    max_retry_on_error: int = Field(default=3, ge=0)
    verbose: bool = False
    allow_delegation: bool = True
    step_callback: Optional[str] = None
    guardrails: List[str] = Field(default_factory=list)
    output_parser: Optional[str] = None

    @field_validator("role", "goal", "backstory")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Valida que campos de string não estão vazios ou apenas com espaços em branco.

        Args:
            v: O valor de string para validar.

        Returns:
            O valor de string sem espaços.

        Raises:
            ValueError: Se a string estiver vazia ou apenas com espaços em branco.
        """
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class TaskConfig(BaseModel):
    """Configuração completa para uma Tarefa.

    Attributes:
        description: O que a tarefa deve realizar.
        expected_output: Formato esperado da saída da tarefa.
        agent_id: ID opcional do agente atribuído a esta tarefa.
        context_ids: Lista de IDs de contexto para incluir como entrada.
        tools: Lista de nomes de ferramentas disponíveis para esta tarefa.
        output_file: Caminho de arquivo opcional para salvar a saída.
        async_execution: Se a tarefa deve ser executada de forma assíncrona.
        human_input: Se a entrada humana é necessária durante a execução.
        guardrails: Lista de nomes de guardrails para aplicar.
        output_parser: Nome do analisador de saída opcional para usar.
        retry_on_failure: Número de tentativas em caso de falha (0 = sem retry).
    """

    description: str
    expected_output: str
    agent_id: Optional[str] = None
    context_ids: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    output_file: Optional[str] = None
    async_execution: bool = False
    human_input: bool = False
    guardrails: List[str] = Field(default_factory=list)
    output_parser: Optional[str] = None
    retry_on_failure: int = Field(default=0, ge=0)

    @field_validator("description", "expected_output")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Valida que campos de string não estão vazios ou apenas com espaços em branco.

        Args:
            v: O valor de string para validar.

        Returns:
            O valor de string sem espaços.

        Raises:
            ValueError: Se a string estiver vazia ou apenas com espaços em branco.
        """
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


# ---------------------------------------------------------------------------
# Estado de execução do agente
# ---------------------------------------------------------------------------


class ReActStep(BaseModel):
    """Uma única etapa no loop de raciocínio ReAct.

    Representa uma iteração do ciclo Pensamento-Ação-Observação:
    - Thought: O que o agente está pensando
    - Action: Qual ferramenta o agente decide usar
    - Observation: O resultado da execução da ferramenta

    Attributes:
        step_number: O número da etapa na sequência de raciocínio.
        thought: O raciocínio do agente nesta etapa.
        action: A chamada de ferramenta (se houver) feita nesta etapa.
        observation: O resultado da execução da ferramenta (se houver).
        timestamp: Timestamp em formato ISO de quando esta etapa ocorreu.
    """

    step_number: int
    thought: Optional[str] = None
    action: Optional[ToolCall] = None
    observation: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AgentState(BaseModel):
    """Estado de tempo de execução de um agente durante a execução da tarefa.

    Rastreia o progresso do agente, histórico de conversa e etapas de raciocínio
    durante toda a execução de uma tarefa.

    Attributes:
        agent_id: Identificador único para o agente.
        messages: Histórico completo da conversa incluindo todas as mensagens.
        steps: Lista de etapas de raciocínio ReAct tomadas até agora.
        current_step: Número da etapa atual na sequência de raciocínio.
        iteration_count: Número total de iterações concluídas.
        status: Status atual de execução do agente.
        metadata: Informações adicionais de tempo de execução.
    """

    agent_id: str
    messages: List[Message] = Field(default_factory=list)
    steps: List[ReActStep] = Field(default_factory=list)
    current_step: int = 0
    iteration_count: int = 0
    status: AgentStatus = AgentStatus.IDLE
    metadata: Dict[str, Any] = Field(default_factory=dict)
