"""Protocolo MCP (Model Context Protocol) para gerenciamento de contexto avançado"""

import json
import uuid
import threading
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class ContextType(Enum):
    """Enumeração de tipos de contexto MCP.

    Define os vários tipos de contextos que podem ser gerenciados no
    Model Context Protocol.

    Attributes:
        CONVERSATION: Contexto relacionado ao histórico de conversa.
        TASK: Contexto relacionado a tarefas ou trabalhos específicos.
        KNOWLEDGE: Contexto contendo informações da base de conhecimento.
        MEMORY: Contexto para memória e aprendizado do agente.
        SYSTEM: Contexto para informações de nível de sistema.
        USER_PROFILE: Contexto contendo dados de perfil do usuário.
    """
    CONVERSATION = "conversation"
    TASK = "task"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    SYSTEM = "system"
    USER_PROFILE = "user_profile"

class ContextPriority(Enum):
    """Enumeração de níveis de prioridade de contexto.

    Define os níveis de prioridade para contextos no protocolo MCP.
    Contextos de prioridade mais alta são mais importantes e devem ser retidos por mais tempo.

    Attributes:
        LOW: Contexto de baixa prioridade.
        MEDIUM: Contexto de prioridade média.
        HIGH: Contexto de alta prioridade.
        CRITICAL: Contexto de prioridade crítica que deve ser retido.
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class MCPContext:
    """Contexto individual no protocolo MCP.

    Representa um item de contexto único com conteúdo, metadados e relacionamentos
    com outros contextos. Contextos podem ser organizados hierarquicamente e etiquetados para
    fácil recuperação.

    Attributes:
        id: Identificador único para o contexto.
        context_type: O tipo de contexto (conversa, tarefa, etc.).
        content: Os dados do contexto como um dicionário.
        priority: O nível de prioridade do contexto.
        created_at: Timestamp em formato ISO quando o contexto foi criado.
        updated_at: Timestamp em formato ISO quando o contexto foi atualizado pela última vez.
        expires_at: Timestamp opcional em formato ISO quando o contexto expira.
        tags: Lista de tags para categorização e filtragem.
        metadata: Metadados adicionais sobre o contexto.
        parent_id: ID opcional do contexto pai para organização hierárquica.
        children_ids: Lista de IDs dos contextos filhos.
    """
    id: str
    context_type: ContextType
    content: Dict[str, Any]
    priority: ContextPriority
    created_at: str
    updated_at: str
    expires_at: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    
    def __post_init__(self):
        """Inicializa valores padrão para campos opcionais.

        Garante que campos opcionais de lista e dicionário sejam inicializados como
        coleções vazias em vez de None.
        """
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.children_ids is None:
            self.children_ids = []
    
    @classmethod
    def create(cls, context_type: ContextType, content: Dict[str, Any],
               priority: ContextPriority = ContextPriority.MEDIUM,
               expires_in_hours: Optional[int] = None,
               tags: List[str] = None,
               parent_id: Optional[str] = None) -> 'MCPContext':
        """Cria um novo contexto MCP.

        Método de fábrica para criar um novo contexto com ID e timestamps gerados automaticamente.

        Args:
            context_type: O tipo de contexto a criar.
            content: Os dados do contexto como um dicionário.
            priority: O nível de prioridade do contexto (padrão: MEDIUM).
            expires_in_hours: Horas opcionais até o contexto expirar.
            tags: Lista opcional de tags para categorização.
            parent_id: ID opcional do contexto pai para organização hierárquica.

        Returns:
            Uma nova instância MCPContext com ID e timestamps gerados automaticamente.
        """
        now = datetime.now().isoformat()
        expires_at = None
        if expires_in_hours:
            expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()

        return cls(
            id=str(uuid.uuid4()),
            context_type=context_type,
            content=content,
            priority=priority,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            tags=tags or [],
            parent_id=parent_id
        )
    
    def update_content(self, new_content: Dict[str, Any]):
        """Atualiza o conteúdo do contexto.

        Mescla novo conteúdo no dicionário de conteúdo existente e atualiza
        o timestamp.

        Args:
            new_content: Novo conteúdo para mesclar no contexto.
        """
        self.content.update(new_content)
        self.updated_at = datetime.now().isoformat()
    
    def add_tag(self, tag: str):
        """Adiciona uma tag ao contexto.

        Adiciona a tag especificada se ainda não estiver presente e atualiza o timestamp.

        Args:
            tag: A tag para adicionar ao contexto.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().isoformat()
    
    def is_expired(self) -> bool:
        """Verifica se o contexto expirou.

        Returns:
            True se o contexto tem um tempo de expiração e ele passou,
            False caso contrário.
        """
        if not self.expires_at:
            return False
        return datetime.now() > datetime.fromisoformat(self.expires_at)
    
    def get_hash(self) -> str:
        """Gera um hash do conteúdo para detecção de alterações.

        Cria um hash MD5 do conteúdo do contexto, útil para detectar
        quando o conteúdo foi alterado.

        Returns:
            Uma string de hash MD5 do conteúdo do contexto.
        """
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o contexto para um dicionário.

        Serializa o contexto para um formato de dicionário, convertendo valores de enum
        para suas representações de string.

        Returns:
            Uma representação em dicionário do contexto com valores de enum convertidos para strings.
        """
        data = asdict(self)
        data['context_type'] = self.context_type.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPContext':
        """Cria um contexto a partir de um dicionário.

        Desserializa uma representação de dicionário de um contexto de volta em uma
        instância MCPContext, convertendo valores de enum de string de volta para enums.

        Args:
            data: Um dicionário contendo os dados do contexto com valores de enum como strings.

        Returns:
            Uma instância MCPContext reconstruída a partir dos dados do dicionário.

        Raises:
            ValueError: Se os valores context_type ou priority não forem valores de enum válidos.
        """
        data['context_type'] = ContextType(data['context_type'])
        data['priority'] = ContextPriority(data['priority'])
        return cls(**data)

@dataclass
class MCPSession:
    """Sessão MCP para agrupar contextos.

    Representa uma sessão que agrupa contextos relacionados, fornecendo
    uma forma de organizar e gerenciar contextos para tarefas ou períodos de tempo específicos.

    Attributes:
        id: Identificador único para a sessão.
        name: Nome legível para a sessão.
        created_at: Timestamp em formato ISO quando a sessão foi criada.
        updated_at: Timestamp em formato ISO quando a sessão foi atualizada pela última vez.
        context_ids: Lista de IDs de contexto pertencentes a esta sessão.
        metadata: Metadados adicionais sobre a sessão.
    """
    id: str
    name: str
    created_at: str
    updated_at: str
    context_ids: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Inicializa valores padrão para campos opcionais.

        Garante que o campo opcional metadata seja inicializado como um
        dicionário vazio em vez de None.
        """
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def create(cls, name: str) -> 'MCPSession':
        """Cria uma nova sessão MCP.

        Método de fábrica para criar uma nova sessão com ID e timestamps gerados automaticamente.

        Args:
            name: O nome para a nova sessão.

        Returns:
            Uma nova instância MCPSession com ID e timestamps gerados automaticamente.
        """
        now = datetime.now().isoformat()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            created_at=now,
            updated_at=now,
            context_ids=[]
        )

class MCPProtocol:
    """Implementação do protocolo de gerenciamento de contexto MCP.

    Gerencia contextos, sessões e seus relacionamentos no Model Context Protocol.
    Fornece funcionalidade para adicionar, recuperar, atualizar e pesquisar contextos
    com suporte para expiração, prioridades e indexação baseada em tags.

    Attributes:
        contexts: Dicionário de todos os contextos chaveados por ID de contexto.
        sessions: Dicionário de todas as sessões chaveadas por ID de sessão.
        max_contexts: Número máximo de contextos para armazenar (padrão: 1000).
        context_index: Índice baseado em tags mapeando tags para IDs de contexto.
        _lock: Bloqueio reentrante para operações thread-safe.
    """

    def __init__(self, max_contexts: int = 1000):
        """Inicializa o protocolo MCP.

        Args:
            max_contexts: Número máximo de contextos para armazenar (padrão: 1000).
        """
        self.contexts: Dict[str, MCPContext] = {}
        self.sessions: Dict[str, MCPSession] = {}
        self.max_contexts = max_contexts
        self.context_index: Dict[str, List[str]] = {}  # tag -> context_ids
        self._lock = threading.RLock()  # Lock para operações thread-safe
        
    def add_context(self, context: MCPContext, session_id: Optional[str] = None) -> str:
        """Adiciona um contexto ao protocolo MCP.

        Adiciona o contexto ao armazenamento, opcionalmente associando-o a uma sessão.
        Limpa contextos expirados e remove contextos antigos se o limite for excedido.
        Atualiza o índice de tags para pesquisa eficiente.

        Args:
            context: O MCPContext para adicionar.
            session_id: ID de sessão opcional para associar o contexto.

        Returns:
            O ID do contexto adicionado.
        """
        with self._lock:
            # Remover contextos expirados se necessário
            self._cleanup_expired_contexts()

            # Remover contextos antigos se limite excedido
            if len(self.contexts) >= self.max_contexts:
                self._remove_oldest_contexts()

            self.contexts[context.id] = context

            # Adicionar à sessão se especificado
            if session_id and session_id in self.sessions:
                self.sessions[session_id].context_ids.append(context.id)
                self.sessions[session_id].updated_at = datetime.now().isoformat()

            # Atualizar índice de tags
            for tag in context.tags:
                if tag not in self.context_index:
                    self.context_index[tag] = []
                self.context_index[tag].append(context.id)

            return context.id
    
    def get_context(self, context_id: str) -> Optional[MCPContext]:
        """Recupera um contexto por ID.

        Retorna o contexto com o ID especificado se ele existe e não está expirado.
        Remove contextos expirados automaticamente.

        Args:
            context_id: O ID do contexto para recuperar.

        Returns:
            O MCPContext se encontrado e não expirado, None caso contrário.
        """
        context = self.contexts.get(context_id)
        if context and context.is_expired():
            self.remove_context(context_id)
            return None
        return context
    
    def update_context(self, context_id: str, new_content: Dict[str, Any]) -> bool:
        """Atualiza o conteúdo de um contexto.

        Mescla novo conteúdo no contexto especificado se ele existe e não está expirado.

        Args:
            context_id: O ID do contexto para atualizar.
            new_content: O novo conteúdo para mesclar no contexto.

        Returns:
            True se o contexto foi atualizado, False se não encontrado ou expirado.
        """
        context = self.get_context(context_id)
        if context:
            context.update_content(new_content)
            return True
        return False
    
    def remove_context(self, context_id: str) -> bool:
        """Remove um contexto.

        Remove o contexto do armazenamento, do índice de tags e de todas as sessões
        que o referenciam.

        Args:
            context_id: O ID do contexto para remover.

        Returns:
            True se o contexto foi removido, False se não encontrado.
        """
        if context_id in self.contexts:
            context = self.contexts[context_id]

            # Remover das tags
            for tag in context.tags:
                if tag in self.context_index:
                    self.context_index[tag] = [cid for cid in self.context_index[tag] if cid != context_id]
                    if not self.context_index[tag]:
                        del self.context_index[tag]

            # Remover das sessões
            for session in self.sessions.values():
                if context_id in session.context_ids:
                    session.context_ids.remove(context_id)
                    session.updated_at = datetime.now().isoformat()

            del self.contexts[context_id]
            return True
        return False
    
    def find_contexts_by_tag(self, tag: str) -> List[MCPContext]:
        """Encontra contextos por tag.

        Recupera todos os contextos não expirados que têm a tag especificada.

        Args:
            tag: A tag para pesquisar.

        Returns:
            Uma lista de instâncias MCPContext com a tag especificada.
        """
        context_ids = self.context_index.get(tag, [])
        return [self.get_context(cid) for cid in context_ids if self.get_context(cid)]
    
    def find_contexts_by_type(self, context_type: ContextType) -> List[MCPContext]:
        """Encontra contextos por tipo.

        Recupera todos os contextos não expirados do tipo especificado.

        Args:
            context_type: O tipo de contexto para pesquisar.

        Returns:
            Uma lista de instâncias MCPContext do tipo especificado.
        """
        return [ctx for ctx in self.contexts.values() if ctx.context_type == context_type and not ctx.is_expired()]
    
    def find_contexts_by_priority(self, min_priority: ContextPriority) -> List[MCPContext]:
        """Encontra contextos por prioridade mínima.

        Recupera todos os contextos não expirados com prioridade igual ou superior
        à prioridade mínima especificada.

        Args:
            min_priority: O nível de prioridade mínimo para pesquisar.

        Returns:
            Uma lista de instâncias MCPContext com prioridade >= min_priority.
        """
        return [ctx for ctx in self.contexts.values()
                if ctx.priority.value >= min_priority.value and not ctx.is_expired()]
    
    def create_session(self, name: str) -> str:
        """Cria uma nova sessão.

        Cria uma nova sessão com o nome especificado e a adiciona ao armazenamento.

        Args:
            name: O nome para a nova sessão.

        Returns:
            O ID da sessão criada.
        """
        with self._lock:
            session = MCPSession.create(name)
            self.sessions[session.id] = session
            return session.id
    
    def get_session_contexts(self, session_id: str) -> List[MCPContext]:
        """Recupera todos os contextos de uma sessão.

        Retorna todos os contextos não expirados pertencentes à sessão especificada.

        Args:
            session_id: O ID da sessão para recuperar contextos.

        Returns:
            Uma lista de instâncias MCPContext pertencentes à sessão.
        """
        session = self.sessions.get(session_id)
        if not session:
            return []

        return [self.get_context(cid) for cid in session.context_ids if self.get_context(cid)]
    
    def get_relevant_contexts(self, query: str, max_results: int = 10) -> List[MCPContext]:
        """Encontra contextos relevantes para uma consulta.

        Realiza uma pesquisa simples de palavras-chave no conteúdo e tags dos contextos,
        pontuando contextos com base em correspondências de palavras-chave, tags e prioridade.

        Args:
            query: A string de consulta de pesquisa.
            max_results: Número máximo de resultados para retornar (padrão: 10).

        Returns:
            Uma lista de instâncias MCPContext ordenadas por pontuação de relevância.
        """
        query_words = query.lower().split()
        scored_contexts = []

        for context in self.contexts.values():
            if context.is_expired():
                continue

            score = 0
            content_str = json.dumps(context.content).lower()

            # Pontuar por palavras-chave no conteúdo
            for word in query_words:
                score += content_str.count(word)

            # Pontuar por tags
            for tag in context.tags:
                if any(word in tag.lower() for word in query_words):
                    score += 2

            # Pontuar por prioridade
            score += context.priority.value

            if score > 0:
                scored_contexts.append((score, context))

        # Sort by score and return the best matches
        scored_contexts.sort(key=lambda x: x[0], reverse=True)
        return [ctx for _, ctx in scored_contexts[:max_results]]
    
    def _cleanup_expired_contexts(self):
        """Remove todos os contextos expirados.

        Identifica e remove todos os contextos que passaram de seu tempo de expiração.
        """
        expired_ids = [cid for cid, ctx in self.contexts.items() if ctx.is_expired()]
        for cid in expired_ids:
            self.remove_context(cid)
    
    def _remove_oldest_contexts(self, count: int = 100):
        """Remove os contextos mais antigos.

        Remove o número especificado de contextos mais antigos com base no tempo de criação.
        Usado quando o limite de contextos é excedido.

        Args:
            count: O número de contextos para remover (padrão: 100).
        """
        # Sort by creation date and remove the oldest
        sorted_contexts = sorted(self.contexts.items(), key=lambda x: x[1].created_at)
        for i in range(min(count, len(sorted_contexts))):
            context_id = sorted_contexts[i][0]
            self.remove_context(context_id)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Retorna um resumo do estado atual do contexto.

        Fornece estatísticas sobre contextos, sessões e tags, excluindo
        contextos expirados das contagens.

        Returns:
            Um dicionário contendo estatísticas de resumo incluindo total de contextos,
            total de sessões, contextos por tipo, contextos por prioridade e total de tags.
        """
        type_counts = {}
        priority_counts = {}

        for context in self.contexts.values():
            if not context.is_expired():
                type_counts[context.context_type.value] = type_counts.get(context.context_type.value, 0) + 1
                priority_counts[context.priority.value] = priority_counts.get(context.priority.value, 0) + 1

        return {
            "total_contexts": len([ctx for ctx in self.contexts.values() if not ctx.is_expired()]),
            "total_sessions": len(self.sessions),
            "contexts_by_type": type_counts,
            "contexts_by_priority": priority_counts,
            "total_tags": len(self.context_index)
        }