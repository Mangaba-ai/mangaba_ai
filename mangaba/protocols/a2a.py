"""Protocolo A2A (Agent-to-Agent) para comunicação de agentes Mangaba AI.

Este módulo implementa o protocolo de comunicação Agente-para-Agente,
habilitando passagem direta de mensagens, broadcasting e descoberta de agentes
para sistemas multi-agentes.

Classes:
    MessageType: Enumeração de tipos de mensagens (request, response, broadcast, etc.)
    A2AMessage: Formato padrão de mensagem para comunicação A2A
    A2AProtocol: Implementação de protocolo para tratamento de mensagens
    A2AAgent: Classe base de agente com capacidades A2A
"""

import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

class MessageType(Enum):
    """Enumeração de tipos de mensagens A2A.

    Define os vários tipos de mensagens que podem ser enviadas entre agentes
    no protocolo de comunicação Agente-para-Agente.

    Attributes:
        REQUEST: Uma mensagem solicitando uma ação ou informação de outro agente.
        RESPONSE: Uma mensagem respondendo a uma solicitação anterior.
        BROADCAST: Uma mensagem enviada a todos os agentes conectados.
        NOTIFICATION: Uma mensagem informando agentes sobre um evento ou atualização.
        ERROR: Uma mensagem indicando que ocorreu um erro.
    """
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    NOTIFICATION = "notification"
    ERROR = "error"

@dataclass
class A2AMessage:
    """Formato padrão de mensagem para comunicação A2A.

    Representa uma mensagem enviada entre agentes no protocolo Agente-para-Agente.
    Mensagens podem ser de vários tipos incluindo solicitações, respostas, broadcasts,
    notificações e erros.

    Attributes:
        id: Identificador único para a mensagem.
        sender_id: ID do agente enviando a mensagem.
        receiver_id: ID do agente recebendo a mensagem (None para broadcasts).
        message_type: O tipo de mensagem (request, response, broadcast, etc.).
        content: O payload da mensagem como um dicionário.
        timestamp: Timestamp em formato ISO quando a mensagem foi criada.
        correlation_id: ID da mensagem relacionada para pares solicitação-resposta.
        metadata: Metadados adicionais sobre a mensagem.
    """
    id: str
    sender_id: str
    receiver_id: Optional[str]
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, sender_id: str, message_type: MessageType, content: Dict[str, Any],
               receiver_id: Optional[str] = None, correlation_id: Optional[str] = None) -> 'A2AMessage':
        """Cria uma nova mensagem A2A.

        Método de fábrica para criar uma nova mensagem com ID e timestamp gerados automaticamente.

        Args:
            sender_id: ID do agente enviando a mensagem.
            message_type: O tipo de mensagem a criar.
            content: O payload da mensagem como um dicionário.
            receiver_id: ID do agente receptor (opcional, None para broadcasts).
            correlation_id: ID da mensagem relacionada para pares solicitação-resposta (opcional).

        Returns:
            Uma nova instância A2AMessage com ID e timestamp gerados automaticamente.
        """
        return cls(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            correlation_id=correlation_id,
            metadata={}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a mensagem para um dicionário.

        Serializa a mensagem para um formato de dicionário, convertendo o enum MessageType
        para seu valor string.

        Returns:
            Uma representação em dicionário da mensagem com valores de enum convertidos para strings.
        """
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Cria uma mensagem a partir de um dicionário.

        Desserializa uma representação de dicionário de uma mensagem de volta em uma
        instância A2AMessage, convertendo a string message_type de volta para o enum MessageType.

        Args:
            data: Um dicionário contendo os dados da mensagem com message_type como string.

        Returns:
            Uma instância A2AMessage reconstruída a partir dos dados do dicionário.

        Raises:
            ValueError: Se o valor message_type não for um MessageType válido.
        """
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)

class A2AProtocol:
    """Implementação do protocolo de comunicação Agente-para-Agente.

    Manipula a passagem de mensagens entre agentes, incluindo mensagens diretas,
    broadcasting e descoberta de agentes. Gerencia manipuladores de mensagens e mantém
    um histórico de mensagens enviadas e recebidas.

    Attributes:
        agent_id: O ID do agente usando este protocolo.
        message_handlers: Dicionário mapeando tipos de mensagens para listas de funções de manipulação.
        connected_agents: Dicionário de agentes conectados chaveados por ID de agente.
        message_history: Lista de todas as mensagens enviadas e recebidas por este protocolo.
        _lock: Bloqueio reentrante para operações thread-safe.
    """

    def __init__(self, agent_id: str):
        """Inicializa o protocolo A2A para um agente.

        Args:
            agent_id: O identificador único para o agente usando este protocolo.
        """
        self.agent_id = agent_id
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
        self.connected_agents: Dict[str, 'A2AAgent'] = {}
        self.message_history: List[A2AMessage] = []
        self._lock = threading.RLock()  # Lock for thread-safe operations
        
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Registra uma função de manipulação para um tipo de mensagem específico.

        Quando uma mensagem do tipo especificado é recebida, todos os manipuladores
        registrados para aquele tipo serão chamados.

        Args:
            message_type: O tipo de mensagem que este manipulador deve processar.
            handler: Uma função callable que aceita um A2AMessage como seu argumento.
        """
        self.message_handlers[message_type].append(handler)
    
    def connect_agent(self, agent: 'A2AAgent'):
        """Conecta outro agente para comunicação.

        Adiciona o agente especificado à lista de agentes conectados, habilitando
        passagem direta de mensagens entre eles.

        Args:
            agent: A instância A2AAgent para conectar.
        """
        with self._lock:
            self.connected_agents[agent.agent_id] = agent
        
    def disconnect_agent(self, agent_id: str):
        """Desconecta um agente.

        Remove o agente especificado da lista de agentes conectados,
        prevenindo maior passagem de mensagens para aquele agente.

        Args:
            agent_id: O ID do agente para desconectar.
        """
        with self._lock:
            if agent_id in self.connected_agents:
                del self.connected_agents[agent_id]
    
    def send_message(self, message: A2AMessage) -> bool:
        """Envia uma mensagem para outro agente ou broadcast para todos os agentes conectados.

        Para mensagens diretas, envia para o receptor especificado se conectado.
        Para mensagens de broadcast, envia para todos os agentes conectados. Opcionalmente filtra
        por tags especificadas nos metadados da mensagem.

        Args:
            message: O A2AMessage para enviar.

        Returns:
            True se a mensagem foi enviada com sucesso, False caso contrário.

        Raises:
            Exception: Se ocorrer um erro durante o envio da mensagem (capturado e registrado).
        """
        try:
            with self._lock:
                if message.receiver_id and message.receiver_id in self.connected_agents:
                    target_agent = self.connected_agents[message.receiver_id]
                    target_agent.receive_message(message)
                    self.message_history.append(message)
                    return True
                elif message.message_type == MessageType.BROADCAST:
                    # Broadcast to all connected agents
                    # Filter by tags if specified
                    target_tags = message.metadata.get('target_tags') if message.metadata else None

                    for agent in self.connected_agents.values():
                        # If target_tags specified, check if agent has the tags
                        if target_tags:
                            # Simplification: sends to all (filter would be implemented in agent)
                            agent.receive_message(message)
                        else:
                            agent.receive_message(message)
                    self.message_history.append(message)
                    return True
                return False
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def receive_message(self, message: A2AMessage):
        """Recebe e processa uma mensagem recebida.

        Adiciona a mensagem ao histórico e executa todos os manipuladores registrados
        para o tipo de mensagem. Exceções de manipuladores são capturadas e registradas.

        Args:
            message: O A2AMessage para receber e processar.
        """
        self.message_history.append(message)

        # Execute registered handlers
        for handler in self.message_handlers[message.message_type]:
            try:
                handler(message)
            except Exception as e:
                print(f"Error in handler: {e}")
    
    def create_request(self, receiver_id: str, action: str, params: Dict[str, Any]) -> A2AMessage:
        """Cria uma mensagem de solicitação.

        Cria uma mensagem do tipo REQUEST com a ação e parâmetros especificados.

        Args:
            receiver_id: O ID do agente para enviar a solicitação.
            action: A ação a ser executada pelo agente receptor.
            params: Parâmetros para a ação como um dicionário.

        Returns:
            Um A2AMessage do tipo REQUEST contendo a ação e parâmetros.
        """
        return A2AMessage.create(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=MessageType.REQUEST,
            content={
                "action": action,
                "params": params
            }
        )
    
    def create_response(self, original_message: A2AMessage, result: Any, success: bool = True) -> A2AMessage:
        """Cria uma mensagem de resposta.

        Cria uma mensagem do tipo RESPONSE em resposta a uma solicitação anterior.
        O ID de correlação vincula a resposta à solicitação original.

        Args:
            original_message: A mensagem de solicitação original para responder.
            result: Os dados de resultado para incluir na resposta.
            success: Se a solicitação foi bem-sucedida (padrão: True).

        Returns:
            Um A2AMessage do tipo RESPONSE com o resultado e ID de correlação.
        """
        return A2AMessage.create(
            sender_id=self.agent_id,
            receiver_id=original_message.sender_id,
            message_type=MessageType.RESPONSE,
            content={
                "result": result,
                "success": success
            },
            correlation_id=original_message.id
        )
    
    def broadcast(self, content: Dict[str, Any], target_tags: Optional[List[str]] = None) -> A2AMessage:
        """Cria e envia uma mensagem de broadcast com filtragem de tags opcional.

        Cria uma mensagem do tipo BROADCAST e envia para todos os agentes conectados.
        Tags de destino podem ser especificadas nos metadados para fins de filtragem.

        Args:
            content: O conteúdo da mensagem como um dicionário.
            target_tags: Lista opcional de tags para filtrar destinatários.

        Returns:
            O A2AMessage que foi transmitido.
        """
        message = A2AMessage.create(
            sender_id=self.agent_id,
            message_type=MessageType.BROADCAST,
            content=content
        )

        # Add tags to metadata if specified
        if target_tags:
            if message.metadata is None:
                message.metadata = {}
            message.metadata['target_tags'] = target_tags

        self.send_message(message)
        return message

class A2AAgent:
    """Classe base de agente com capacidades de comunicação A2A.

    Fornece funcionalidade de comunicação Agente-para-Agente incluindo envio,
    recebimento e gerenciamento de manipuladores de mensagens. Pode conectar a outros agentes
    e participar de sistemas multi-agentes.

    Attributes:
        agent_id: O identificador único para este agente.
        a2a_protocol: A instância A2AProtocol manipulando comunicação.
    """

    def __init__(self, agent_id: str):
        """Inicializa o agente A2A.

        Args:
            agent_id: O identificador único para este agente.
        """
        self.agent_id = agent_id
        self.a2a_protocol = A2AProtocol(agent_id)
        self.setup_default_handlers()
    
    def setup_default_handlers(self):
        """Configura manipuladores de mensagem padrão.

        Registra os manipuladores padrão para os tipos de mensagem REQUEST, RESPONSE e NOTIFICATION.
        Estes podem ser substituídos em subclasses para comportamento personalizado.
        """
        self.a2a_protocol.register_handler(MessageType.REQUEST, self.handle_request)
        self.a2a_protocol.register_handler(MessageType.RESPONSE, self.handle_response)
        self.a2a_protocol.register_handler(MessageType.NOTIFICATION, self.handle_notification)
    
    def handle_request(self, message: A2AMessage):
        """Manipulador padrão para mensagens de solicitação.

        Processa uma mensagem de solicitação e envia uma resposta. Esta é uma implementação
        padrão simples que deve ser substituída em subclasses para comportamento específico do agente.

        Args:
            message: A mensagem REQUEST para manipular.
        """
        action = message.content.get("action")

        # Implement agent-specific logic here
        result = f"Action '{action}' processed by agent {self.agent_id}"

        response = self.a2a_protocol.create_response(message, result)
        self.a2a_protocol.send_message(response)
    
    def handle_response(self, message: A2AMessage):
        """Manipulador padrão para mensagens de resposta.

        Imprime a resposta recebida. Esta é uma implementação padrão simples
        que deve ser substituída em subclasses para comportamento específico do agente.

        Args:
            message: A mensagem RESPONSE para manipular.
        """
        print(f"Response received from {message.sender_id}: {message.content}")
    
    def handle_notification(self, message: A2AMessage):
        """Manipulador padrão para mensagens de notificação.

        Imprime a notificação recebida. Esta é uma implementação padrão simples
        que deve ser substituída em subclasses para comportamento específico do agente.

        Args:
            message: A mensagem NOTIFICATION para manipular.
        """
        print(f"Notification from {message.sender_id}: {message.content}")
    
    def receive_message(self, message: A2AMessage):
        """Recebe uma mensagem via o protocolo A2A.

        Delega a recepção de mensagens para a instância A2AProtocol subjacente.

        Args:
            message: O A2AMessage para receber.
        """
        self.a2a_protocol.receive_message(message)
    
    def connect_to(self, other_agent: 'A2AAgent'):
        """Conecta a outro agente.

        Estabelece uma conexão bidirecional entre este agente e outro agente,
        habilitando passagem de mensagens em ambas as direções.

        Args:
            other_agent: O A2AAgent para conectar.
        """
        self.a2a_protocol.connect_agent(other_agent)
        other_agent.a2a_protocol.connect_agent(self)
    
    def send_request(self, receiver_id: str, action: str, params: Dict[str, Any]):
        """Envia uma solicitação para outro agente.

        Cria e envia uma mensagem REQUEST para o agente especificado.

        Args:
            receiver_id: O ID do agente para enviar a solicitação.
            action: A ação a ser executada pelo agente receptor.
            params: Parâmetros para a ação como um dicionário.

        Returns:
            True se a solicitação foi enviada com sucesso, False caso contrário.
        """
        message = self.a2a_protocol.create_request(receiver_id, action, params)
        return self.a2a_protocol.send_message(message)
    
    def notify_all(self, content: Dict[str, Any]):
        """Envia uma notificação para todos os agentes conectados.

        Cria e transmite uma mensagem NOTIFICATION para todos os agentes conectados.

        Args:
            content: O conteúdo da notificação como um dicionário.

        Returns:
            True se a notificação foi enviada com sucesso, False caso contrário.
        """
        return self.a2a_protocol.broadcast(content)