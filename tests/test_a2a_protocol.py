#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para o protocolo A2A (Agent-to-Agent)
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime
import uuid

# Adiciona o diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba.protocols.a2a import A2AMessage, A2AProtocol, A2AAgent, MessageType


class TestA2AMessage:
    """Testes para a classe A2AMessage"""

    def test_message_creation(self):
        """Testa criação de mensagem A2A"""
        content = {"action": "test", "data": "test_data"}
        message = A2AMessage.create(
            sender_id="agent1",
            message_type=MessageType.REQUEST,
            content=content,
            receiver_id="agent2",
        )

        assert message.sender_id == "agent1"
        assert message.receiver_id == "agent2"
        assert message.message_type == MessageType.REQUEST
        assert message.content == content
        assert message.id is not None
        assert message.timestamp is not None

    def test_message_creation_without_receiver(self):
        """Testa criação de mensagem sem receptor (broadcast)"""
        content = {"message": "broadcast"}
        message = A2AMessage.create(
            sender_id="agent1", message_type=MessageType.BROADCAST, content=content
        )

        assert message.sender_id == "agent1"
        assert message.receiver_id is None
        assert message.message_type == MessageType.BROADCAST
        assert message.content == content

    def test_message_with_correlation_id(self):
        """Testa criação de mensagem com correlation_id"""
        correlation_id = str(uuid.uuid4())
        message = A2AMessage.create(
            sender_id="agent1",
            message_type=MessageType.RESPONSE,
            content={"result": "success"},
            correlation_id=correlation_id,
        )

        assert message.correlation_id == correlation_id

    def test_message_to_dict(self):
        """Testa conversão de mensagem para dicionário"""
        message = A2AMessage.create(
            sender_id="agent1",
            message_type=MessageType.REQUEST,
            content={"test": "data"},
        )

        message_dict = message.to_dict()

        assert isinstance(message_dict, dict)
        assert message_dict["sender_id"] == "agent1"
        assert message_dict["message_type"] == "request"
        assert message_dict["content"] == {"test": "data"}
        assert "id" in message_dict
        assert "timestamp" in message_dict

    def test_message_from_dict(self):
        """Testa criação de mensagem a partir de dicionário"""
        message_data = {
            "id": str(uuid.uuid4()),
            "sender_id": "agent1",
            "receiver_id": "agent2",
            "message_type": "request",
            "content": {"action": "test"},
            "timestamp": datetime.now().isoformat(),
            "correlation_id": None,
            "metadata": {},
        }

        message = A2AMessage.from_dict(message_data)

        assert message.sender_id == "agent1"
        assert message.receiver_id == "agent2"
        assert message.message_type == MessageType.REQUEST
        assert message.content == {"action": "test"}


class TestA2AProtocol:
    """Testes para a classe A2AProtocol"""

    @pytest.fixture
    def protocol(self):
        """Fixture para criar um protocolo A2A"""
        return A2AProtocol("test_agent")

    def test_protocol_initialization(self, protocol):
        """Testa inicialização do protocolo"""
        assert protocol.agent_id == "test_agent"
        assert len(protocol.message_handlers) == len(MessageType)
        assert len(protocol.connected_agents) == 0
        assert len(protocol.message_history) == 0

    def test_register_handler(self, protocol):
        """Testa registro de handler"""

        def test_handler(message):
            pass

        protocol.register_handler(MessageType.REQUEST, test_handler)

        assert test_handler in protocol.message_handlers[MessageType.REQUEST]

    def test_connect_agent(self, protocol):
        """Testa conexão de agente"""
        mock_agent = Mock()
        mock_agent.agent_id = "other_agent"

        protocol.connect_agent(mock_agent)

        assert "other_agent" in protocol.connected_agents
        assert protocol.connected_agents["other_agent"] == mock_agent

    def test_disconnect_agent(self, protocol):
        """Testa desconexão de agente"""
        mock_agent = Mock()
        mock_agent.agent_id = "other_agent"

        protocol.connect_agent(mock_agent)
        protocol.disconnect_agent("other_agent")

        assert "other_agent" not in protocol.connected_agents

    def test_send_message_to_connected_agent(self, protocol):
        """Testa envio de mensagem para agente conectado"""
        mock_agent = Mock()
        mock_agent.agent_id = "receiver"
        protocol.connect_agent(mock_agent)

        message = A2AMessage.create(
            sender_id="test_agent",
            message_type=MessageType.REQUEST,
            content={"action": "test"},
            receiver_id="receiver",
        )

        result = protocol.send_message(message)

        assert result is True
        mock_agent.receive_message.assert_called_once_with(message)
        assert message in protocol.message_history

    def test_send_message_to_nonexistent_agent(self, protocol):
        """Testa envio de mensagem para agente não conectado"""
        message = A2AMessage.create(
            sender_id="test_agent",
            message_type=MessageType.REQUEST,
            content={"action": "test"},
            receiver_id="nonexistent",
        )

        result = protocol.send_message(message)

        assert result is False
        assert message not in protocol.message_history

    def test_broadcast_message(self, protocol):
        """Testa broadcast de mensagem"""
        # Conecta múltiplos agentes
        agents = []
        for i in range(3):
            mock_agent = Mock()
            mock_agent.agent_id = f"agent_{i}"
            agents.append(mock_agent)
            protocol.connect_agent(mock_agent)

        message = A2AMessage.create(
            sender_id="test_agent",
            message_type=MessageType.BROADCAST,
            content={"message": "broadcast_test"},
        )

        result = protocol.send_message(message)

        assert result is True
        for agent in agents:
            agent.receive_message.assert_called_once_with(message)
        assert message in protocol.message_history

    def test_receive_message_with_handlers(self, protocol):
        """Testa recebimento de mensagem com handlers"""
        handler_called = False
        received_message = None

        def test_handler(message):
            nonlocal handler_called, received_message
            handler_called = True
            received_message = message

        protocol.register_handler(MessageType.REQUEST, test_handler)

        message = A2AMessage.create(
            sender_id="sender",
            message_type=MessageType.REQUEST,
            content={"action": "test"},
        )

        protocol.receive_message(message)

        assert handler_called
        assert received_message == message

    def test_create_request(self, protocol):
        """Testa criação de requisição"""
        message = protocol.create_request(
            "receiver", "test_action", {"param1": "value1"}
        )

        assert message.sender_id == "test_agent"
        assert message.receiver_id == "receiver"
        assert message.message_type == MessageType.REQUEST
        assert message.content["action"] == "test_action"
        assert message.content["params"] == {"param1": "value1"}

    def test_create_response(self, protocol):
        """Testa criação de resposta"""
        original_message = A2AMessage.create(
            sender_id="sender",
            message_type=MessageType.REQUEST,
            content={"action": "test"},
        )

        response = protocol.create_response(original_message, "success_result", True)

        assert response.sender_id == "test_agent"
        assert response.receiver_id == "sender"
        assert response.message_type == MessageType.RESPONSE
        assert response.correlation_id == original_message.id
        assert response.content["result"] == "success_result"
        assert response.content["success"] is True

    def test_create_response_error(self, protocol):
        """Testa criação de resposta de erro"""
        original_message = A2AMessage.create(
            sender_id="sender",
            message_type=MessageType.REQUEST,
            content={"action": "test"},
        )

        response = protocol.create_response(original_message, "error_message", False)

        assert response.content["result"] == "error_message"
        assert response.content["success"] is False

    def test_broadcast_creation(self, protocol):
        """Testa criação de broadcast"""
        content = {"announcement": "test broadcast"}
        message = protocol.broadcast(content)

        assert message.sender_id == "test_agent"
        assert message.receiver_id is None
        assert message.message_type == MessageType.BROADCAST
        assert message.content == content


class TestA2AAgent:
    """Testes para a classe A2AAgent"""

    @pytest.fixture
    def agent(self):
        """Fixture para criar um agente A2A"""
        return A2AAgent("test_agent")

    def test_agent_initialization(self, agent):
        """Testa inicialização do agente"""
        assert agent.agent_id == "test_agent"
        assert isinstance(agent.a2a_protocol, A2AProtocol)
        assert agent.a2a_protocol.agent_id == "test_agent"

    def test_default_handlers_setup(self, agent):
        """Testa se os handlers padrão foram configurados"""
        # Verifica se há handlers registrados para os tipos principais
        assert len(agent.a2a_protocol.message_handlers[MessageType.REQUEST]) > 0
        assert len(agent.a2a_protocol.message_handlers[MessageType.RESPONSE]) > 0
        assert len(agent.a2a_protocol.message_handlers[MessageType.NOTIFICATION]) > 0

    def test_connect_to_other_agent(self, agent):
        """Testa conexão com outro agente"""
        other_agent = A2AAgent("other_agent")

        agent.connect_to(other_agent)

        assert "other_agent" in agent.a2a_protocol.connected_agents
        assert "test_agent" in other_agent.a2a_protocol.connected_agents

    def test_send_request(self, agent):
        """Testa envio de requisição"""
        other_agent = A2AAgent("other_agent")
        agent.connect_to(other_agent)

        # Não podemos mockar send_message e depois verificar o retorno,
        # pois send_request retorna o resultado de send_message
        result = agent.send_request("other_agent", "test_action", {"param": "value"})

        # send_request retorna True se a mensagem foi enviada com sucesso
        assert result is True
        # Verifica se a mensagem foi registrada no histórico
        assert len(agent.a2a_protocol.message_history) > 0
        last_message = agent.a2a_protocol.message_history[-1]
        assert last_message.message_type == MessageType.REQUEST

    def test_notify_all(self, agent):
        """Testa notificação para todos os agentes"""
        with patch.object(agent.a2a_protocol, "broadcast") as mock_broadcast:
            content = {"notification": "test"}
            message = agent.notify_all(content)

            mock_broadcast.assert_called_once_with(content)

    def test_receive_message(self, agent):
        """Testa recebimento de mensagem"""
        message = A2AMessage.create(
            sender_id="sender",
            message_type=MessageType.REQUEST,
            content={"action": "test"},
        )

        with patch.object(agent.a2a_protocol, "receive_message") as mock_receive:
            agent.receive_message(message)
            mock_receive.assert_called_once_with(message)

    def test_handle_request_default(self, agent):
        """Testa handler padrão de requisição"""
        message = A2AMessage.create(
            sender_id="sender",
            message_type=MessageType.REQUEST,
            content={"action": "unknown"},
        )

        # O handler padrão deve processar sem erro
        agent.handle_request(message)
        # Teste passa se não há exceção

    def test_handle_response_default(self, agent):
        """Testa handler padrão de resposta"""
        message = A2AMessage.create(
            sender_id="sender",
            message_type=MessageType.RESPONSE,
            content={"result": "success"},
        )

        # O handler padrão deve processar sem erro
        agent.handle_response(message)
        # Teste passa se não há exceção

    def test_handle_notification_default(self, agent):
        """Testa handler padrão de notificação"""
        message = A2AMessage.create(
            sender_id="sender",
            message_type=MessageType.NOTIFICATION,
            content={"info": "test notification"},
        )

        # O handler padrão deve processar sem erro
        agent.handle_notification(message)
        # Teste passa se não há exceção


if __name__ == "__main__":
    pytest.main([__file__])
