#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para MangabaAgent
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Adiciona o diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba_agent import MangabaAgent
from mangaba.protocols.a2a import A2AMessage, MessageType


class TestMangabaAgent:
    """Testes para a classe MangabaAgent"""

    @pytest.fixture
    def mock_llm(self):
        """Mock para cliente LLM genérico"""
        with patch("mangaba_agent.create_llm_client") as mock_factory:
            mock_client = Mock()
            mock_client.generate_text.return_value = "Resposta mockada do AI"
            mock_factory.return_value = mock_client
            yield mock_factory, mock_client

    @pytest.fixture
    def mock_config(self):
        """Mock para configuração"""
        with patch("config.config") as mock_cfg:
            mock_cfg.api_key = "test_api_key"
            mock_cfg.model = "gemini-2.5-flash"
            mock_cfg.log_level = "INFO"
            yield mock_cfg

    @pytest.fixture
    def agent(self, mock_llm, mock_config):
        """Fixture para criar um agente de teste"""
        return MangabaAgent(api_key="test_key", model="test-model")

    def test_agent_initialization(self, mock_llm, mock_config):
        """Testa inicialização do agente"""
        agent = MangabaAgent(api_key="test_key", model="test-model")

        assert agent.api_key == "test_key"
        assert agent.model_name == "test-model"
        assert agent.agent_id.startswith("mangaba_")
        assert agent.mcp_enabled is True
        assert hasattr(agent, "mcp")
        assert hasattr(agent, "current_session_id")

    def test_agent_initialization_without_mcp(self, mock_llm, mock_config):
        """Testa inicialização do agente sem MCP"""
        agent = MangabaAgent(api_key="test_key", enable_mcp=False)

        assert agent.mcp_enabled is False

    def test_chat_basic(self, agent, mock_llm):
        """Testa funcionalidade básica de chat"""
        _, mock_client = mock_llm
        mock_client.generate_text.return_value = "Olá! Como posso ajudar?"

        response = agent.chat("Olá")

        assert response == "Olá! Como posso ajudar?"
        mock_client.generate_text.assert_called_once()

    def test_chat_with_context(self, agent, mock_llm):
        """Testa chat com contexto MCP"""
        _, mock_client = mock_llm
        mock_client.generate_text.return_value = "Resposta com contexto"

        response = agent.chat("Teste com contexto", use_context=True)

        assert response == "Resposta com contexto"
        # Verifica se o contexto foi adicionado ao MCP
        assert len(agent.mcp.contexts) > 0

    def test_chat_without_context(self, agent, mock_llm):
        """Testa chat sem usar contexto MCP"""
        _, mock_client = mock_llm
        mock_client.generate_text.return_value = "Resposta sem contexto"

        initial_context_count = len(agent.mcp.contexts)
        response = agent.chat("Teste sem contexto", use_context=False)

        assert response == "Resposta sem contexto"
        # Verifica se não foi adicionado contexto
        assert len(agent.mcp.contexts) == initial_context_count

    def test_analyze_text(self, agent, mock_llm):
        """Testa análise de texto"""
        _, mock_client = mock_llm
        mock_client.generate_text.return_value = "Análise: Texto positivo"

        response = agent.analyze_text("Texto para análise", "Analise o sentimento")

        assert response == "Análise: Texto positivo"
        mock_client.generate_text.assert_called_once()

    def test_translate(self, agent, mock_llm):
        """Testa tradução de texto"""
        _, mock_client = mock_llm
        mock_client.generate_text.return_value = "Hello world"

        response = agent.translate("Olá mundo", "inglês")

        assert response == "Hello world"
        mock_client.generate_text.assert_called_once()

    def test_get_context_summary(self, agent):
        """Testa obtenção do resumo de contexto"""
        # Adiciona alguns contextos
        agent.chat("Primeira mensagem")
        agent.chat("Segunda mensagem")

        summary = agent.get_context_summary()

        assert isinstance(summary, str)
        # O resumo deve ter algum conteúdo ou indicar que está vazio
        assert len(summary) > 0

    def test_handle_mangaba_request_chat(self, agent, mock_llm):
        """Testa handler de requisição A2A para chat"""
        _, mock_client = mock_llm
        mock_client.generate_text.return_value = "Resposta via A2A"

        message = A2AMessage.create(
            sender_id="test_sender",
            message_type=MessageType.REQUEST,
            content={"action": "chat", "params": {"message": "Olá via A2A"}},
            receiver_id=agent.agent_id,
        )

        with patch.object(agent.a2a_protocol, "send_message") as mock_send:
            agent.handle_mangaba_request(message)
            mock_send.assert_called_once()

    def test_handle_mangaba_request_analyze(self, agent, mock_llm):
        """Testa handler de requisição A2A para análise"""
        _, mock_client = mock_llm
        mock_client.generate_text.return_value = "Análise via A2A"

        message = A2AMessage.create(
            sender_id="test_sender",
            message_type=MessageType.REQUEST,
            content={
                "action": "analyze",
                "params": {
                    "text": "Texto para análise",
                    "instruction": "Analise este texto",
                },
            },
            receiver_id=agent.agent_id,
        )

        with patch.object(agent.a2a_protocol, "send_message") as mock_send:
            agent.handle_mangaba_request(message)
            mock_send.assert_called_once()

    def test_handle_mangaba_request_unknown_action(self, agent):
        """Testa handler com ação desconhecida"""
        message = A2AMessage.create(
            sender_id="test_sender",
            message_type=MessageType.REQUEST,
            content={"action": "unknown_action", "params": {}},
            receiver_id=agent.agent_id,
        )

        with patch.object(agent.a2a_protocol, "send_message") as mock_send:
            agent.handle_mangaba_request(message)
            mock_send.assert_called_once()
            # Verifica se a resposta contém erro
            call_args = mock_send.call_args[0][0]
            assert "não reconhecida" in call_args.content.get("result", "")

    def test_send_agent_request(self, agent):
        """Testa envio de requisição para outro agente"""
        with patch.object(agent.a2a_protocol, "send_message") as mock_send:
            result = agent.send_agent_request(
                "target_agent", "chat", {"message": "Olá"}
            )

            # Verifica se contém parte da mensagem esperada (encoding pode variar)
            assert "enviada" in result.lower() or "target_agent" in result
            mock_send.assert_called_once()

    def test_broadcast_message(self, agent):
        """Testa broadcast de mensagem"""
        with patch.object(agent.a2a_protocol, "send_message") as mock_send:
            result = agent.broadcast_message("Mensagem de broadcast", ["tag1", "tag2"])

            assert "Broadcast enviado" in result
            mock_send.assert_called_once()

    def test_error_handling_in_chat(self, agent, mock_llm):
        """Testa tratamento de erro no chat"""
        _, mock_client = mock_llm
        mock_client.generate_text.side_effect = Exception("API Error")

        response = agent.chat("Teste de erro")

        assert "Erro" in response or "erro" in response

    def test_agent_id_uniqueness(self, mock_llm, mock_config):
        """Testa se IDs de agentes são únicos"""
        agent1 = MangabaAgent()
        agent2 = MangabaAgent()

        assert agent1.agent_id != agent2.agent_id
        assert agent1.agent_id.startswith("mangaba_")
        assert agent2.agent_id.startswith("mangaba_")

    def test_custom_agent_id(self, mock_llm, mock_config):
        """Testa criação de agente com ID customizado"""
        custom_id = "custom_agent_123"
        agent = MangabaAgent(agent_id=custom_id)

        assert agent.agent_id == custom_id


if __name__ == "__main__":
    pytest.main([__file__])
