#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de integração para o projeto Mangaba AI
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba_agent import MangabaAgent
from mangaba.protocols.a2a import A2AMessage, A2AProtocol, A2AAgent, MessageType
from mangaba.protocols.mcp import MCPContext, MCPProtocol, ContextType, ContextPriority


class TestMangabaAgentIntegration:
    """Testes de integração para MangabaAgent com protocolos A2A e MCP"""

    @pytest.fixture
    def mock_llm(self):
        """Mock para cliente LLM"""
        with patch("mangaba_agent.create_llm_client") as mock_factory:
            mock_client = Mock()
            mock_client.generate_text.return_value = "Resposta simulada do modelo"
            mock_factory.return_value = mock_client
            yield mock_factory, mock_client

    @pytest.fixture
    def agent(self, mock_llm):
        """Fixture para criar um agente Mangaba"""
        return MangabaAgent(
            api_key="test_key", agent_name="TestAgent", use_mcp=True, use_a2a=True
        )

    def test_agent_initialization_with_protocols(self, agent):
        """Testa inicialização do agente com protocolos"""
        assert "TestAgent" in agent.agent_id
        assert agent.mcp_enabled is True
        assert agent.use_a2a is True
        assert isinstance(agent.mcp, MCPProtocol)
        assert isinstance(agent.a2a_protocol, A2AProtocol)
        assert agent.agent_id is not None

    def test_chat_with_mcp_context_integration(self, agent):
        """Testa chat com integração MCP"""
        # Adiciona contexto MCP
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"previous_message": "Olá, como você está?"},
            tags=["greeting"],
        )
        agent.mcp.add_context(context, agent.current_session_id)

        # Realiza chat
        response = agent.chat("Como posso ajudar você hoje?")

        assert isinstance(response, str)
        assert len(response) > 0

        # Verifica se novo contexto foi adicionado
        contexts = agent.mcp.find_contexts_by_type(ContextType.CONVERSATION)
        assert len(contexts) >= 2  # Contexto original + novo contexto do chat

    def test_a2a_request_with_mcp_context(self, agent):
        """Testa requisição A2A com contexto MCP"""
        # Adiciona contexto relevante
        context = MCPContext.create(
            context_type=ContextType.KNOWLEDGE,
            content={"expertise": "análise de texto"},
            tags=["text_analysis"],
        )
        agent.mcp.add_context(context, agent.current_session_id)

        # Simula outro agente
        other_agent = A2AAgent("OtherAgent")
        agent.a2a_protocol.connect_agent(other_agent)

        # Envia requisição
        response = agent.send_agent_request(
            "OtherAgent", "Pode analisar este texto?", {"text": "Texto para análise"}
        )

        assert isinstance(response, str)

    def test_broadcast_with_context_sharing(self, agent):
        """Testa broadcast com compartilhamento de contexto"""
        # Adiciona contexto importante
        context = MCPContext.create(
            context_type=ContextType.SYSTEM,
            content={"alert": "Sistema atualizado"},
            priority=ContextPriority.CRITICAL,
            tags=["system_update"],
        )
        agent.mcp.add_context(context, agent.current_session_id)

        # Conecta outros agentes
        agent1 = A2AAgent("Agent1")
        agent2 = A2AAgent("Agent2")
        agent.a2a_protocol.connect_agent(agent1)
        agent.a2a_protocol.connect_agent(agent2)

        # Envia broadcast - tags deve ser uma lista de strings
        result = agent.broadcast_message(
            "Atualização importante do sistema", ["system_update", "alert"]
        )

        # broadcast_message retorna uma string, não um booleano
        assert isinstance(result, str)
        assert "sucesso" in result.lower() or "Broadcast enviado" in result

    def test_context_summary_integration(self, agent):
        """Testa resumo de contexto com múltiplos tipos"""
        # Adiciona diferentes tipos de contexto
        contexts = [
            MCPContext.create(
                context_type=ContextType.CONVERSATION,
                content={"message": "Conversa sobre IA"},
                tags=["ai", "conversation"],
            ),
            MCPContext.create(
                context_type=ContextType.TASK,
                content={"task": "Analisar dados"},
                tags=["analysis", "data"],
            ),
            MCPContext.create(
                context_type=ContextType.MEMORY,
                content={"memory": "Preferências do usuário"},
                tags=["user", "preferences"],
            ),
        ]

        for context in contexts:
            agent.mcp.add_context(context, agent.current_session_id)

        # Gera resumo
        summary = agent.get_context_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_error_handling_integration(self, agent):
        """Testa tratamento de erros com protocolos"""
        # Simula erro no modelo
        with patch.object(
            agent.llm, "generate_text", side_effect=Exception("API Error")
        ):
            response = agent.chat("Teste de erro")

            assert "erro" in response.lower() or "error" in response.lower()

    def test_agent_communication_flow(self, agent):
        """Testa fluxo completo de comunicação entre agentes"""
        # Cria segundo agente
        agent2 = MangabaAgent(
            api_key="test_key2", agent_name="Agent2", use_mcp=True, use_a2a=True
        )

        # Conecta agentes (deve passar o agente, não o protocolo)
        agent.connect_to(agent2)

        # Agent1 envia requisição para Agent2
        response = agent.send_agent_request(
            agent2.agent_id, "chat", {"message": "Pode me ajudar com análise de texto?"}
        )

        assert isinstance(response, str)


class TestProtocolsIntegration:
    """Testes de integração entre protocolos A2A e MCP"""

    @pytest.fixture
    def a2a_protocol(self):
        """Fixture para protocolo A2A"""
        return A2AProtocol("test_agent")

    @pytest.fixture
    def mcp_protocol(self):
        """Fixture para protocolo MCP"""
        return MCPProtocol()

    def test_a2a_message_to_mcp_context(self, a2a_protocol, mcp_protocol):
        """Testa conversão de mensagem A2A para contexto MCP"""
        # Cria mensagem A2A usando o método correto
        message = A2AMessage.create(
            sender_id="agent1",
            message_type=MessageType.REQUEST,
            content={"action": "analyze", "data": {"text": "Texto para análise"}},
            receiver_id="agent2",
        )

        # Converte para contexto MCP
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={
                "a2a_message": message.to_dict(),
                "message_type": "a2a_request",
                "sender": message.sender_id,
                "receiver": message.receiver_id,
            },
            tags=["a2a", "request", "communication"],
        )

        # Adiciona ao protocolo MCP
        context_id = mcp_protocol.add_context(context)

        assert context_id is not None

        # Verifica se pode recuperar o contexto
        retrieved_context = mcp_protocol.get_context(context_id)
        assert retrieved_context is not None
        assert retrieved_context.content["sender"] == "agent1"
        assert retrieved_context.content["receiver"] == "agent2"

    def test_mcp_context_influences_a2a_response(self, a2a_protocol, mcp_protocol):
        """Testa como contexto MCP influencia resposta A2A"""
        # Adiciona contexto relevante no MCP
        context = MCPContext.create(
            context_type=ContextType.KNOWLEDGE,
            content={
                "expertise": "análise de sentimento",
                "capabilities": ["sentiment_analysis", "text_classification"],
            },
            tags=["nlp", "analysis"],
        )
        mcp_protocol.add_context(context)

        # Busca contextos relevantes para uma requisição
        relevant_contexts = mcp_protocol.get_relevant_contexts("análise de sentimento")

        assert len(relevant_contexts) > 0
        assert context in relevant_contexts

        # Simula uso do contexto para gerar resposta A2A
        response_data = {
            "analysis_result": "Sentimento positivo",
            "confidence": 0.95,
            "context_used": context.id,
        }

        response_message = A2AMessage.create(
            sender_id="agent2",
            message_type=MessageType.RESPONSE,
            content=response_data,
            receiver_id="agent1",
            correlation_id="req_123",
        )

        assert response_message.content["context_used"] == context.id

    def test_cross_protocol_error_handling(self, a2a_protocol, mcp_protocol):
        """Testa tratamento de erros entre protocolos"""
        # Simula erro em comunicação A2A
        error_message = A2AMessage.create(
            sender_id="agent1",
            message_type=MessageType.ERROR,
            content={
                "error_code": "PROCESSING_ERROR",
                "error_message": "Falha no processamento",
                "original_request": "análise de texto",
            },
            receiver_id="agent2",
        )

        # Registra erro como contexto MCP
        error_context = MCPContext.create(
            context_type=ContextType.SYSTEM,
            content={
                "error_type": "a2a_communication",
                "error_message": error_message.to_dict(),
                "timestamp": datetime.now().isoformat(),
            },
            priority=ContextPriority.HIGH,
            tags=["error", "a2a", "communication"],
        )

        context_id = mcp_protocol.add_context(error_context)

        # Verifica se erro foi registrado
        error_contexts = mcp_protocol.find_contexts_by_tag("error")
        assert len(error_contexts) > 0
        assert error_context in error_contexts

    def test_protocol_state_synchronization(self, a2a_protocol, mcp_protocol):
        """Testa sincronização de estado entre protocolos"""
        # Registra agentes conectados no A2A
        agent1 = A2AAgent("Agent1")
        agent2 = A2AAgent("Agent2")

        a2a_protocol.connect_agent(agent1)
        a2a_protocol.connect_agent(agent2)

        # Registra estado da rede no MCP
        network_state = MCPContext.create(
            context_type=ContextType.SYSTEM,
            content={
                "connected_agents": list(a2a_protocol.connected_agents.keys()),
                "total_agents": len(a2a_protocol.connected_agents),
                "network_status": "active",
            },
            tags=["network", "agents", "status"],
        )

        mcp_protocol.add_context(network_state)

        # Verifica sincronização
        network_contexts = mcp_protocol.find_contexts_by_tag("network")
        assert len(network_contexts) > 0

        latest_context = network_contexts[0]
        assert latest_context.content["total_agents"] == 2
        assert "Agent1" in latest_context.content["connected_agents"]
        assert "Agent2" in latest_context.content["connected_agents"]


class TestPerformanceIntegration:
    """Testes de performance e escalabilidade"""

    @pytest.fixture
    def mock_llm(self):
        """Mock para cliente LLM"""
        with patch("mangaba_agent.create_llm_client") as mock_factory:
            mock_client = Mock()
            mock_client.generate_text.return_value = "Resposta rápida"
            mock_factory.return_value = mock_client
            yield mock_factory, mock_client

    def test_multiple_agents_communication(self, mock_llm):
        """Testa comunicação entre múltiplos agentes"""
        agents = []

        # Cria múltiplos agentes
        for i in range(5):
            agent = MangabaAgent(
                api_key=f"test_key_{i}",
                agent_name=f"Agent{i}",
                use_mcp=True,
                use_a2a=True,
            )
            agents.append(agent)

        # Conecta todos os agentes
        for i, agent in enumerate(agents):
            for j, other_agent in enumerate(agents):
                if i != j:
                    agent.connect_to(other_agent)

        # Testa broadcast de um agente para todos - tags deve ser lista de strings
        result = agents[0].broadcast_message(
            "Mensagem para todos", ["priority", "high"]
        )

        # broadcast_message retorna string
        assert isinstance(result, str)
        assert "Broadcast enviado" in result

    def test_large_context_handling(self, mock_llm):
        """Testa manipulação de grandes volumes de contexto"""
        agent = MangabaAgent(api_key="test_key", agent_name="TestAgent", use_mcp=True)

        # Adiciona muitos contextos
        for i in range(100):
            context = MCPContext.create(
                context_type=ContextType.CONVERSATION,
                content={"message": f"Mensagem {i}", "data": f"dados_{i}"},
                tags=[f"tag_{i % 10}", "test"],
            )
            agent.mcp.add_context(context, agent.current_session_id)

        # Verifica se o protocolo MCP gerencia corretamente
        all_contexts = agent.mcp.find_contexts_by_tag("test")
        assert len(all_contexts) <= agent.mcp.max_contexts

        # Testa busca eficiente
        relevant_contexts = agent.mcp.get_relevant_contexts("Mensagem 50")
        assert len(relevant_contexts) > 0

    def test_concurrent_operations(self, mock_llm):
        """Testa operações concorrentes (simuladas)"""
        agent = MangabaAgent(
            api_key="test_key", agent_name="TestAgent", use_mcp=True, use_a2a=True
        )

        # Simula operações concorrentes
        operations = []

        # Chat concorrente
        for i in range(10):
            response = agent.chat(f"Mensagem {i}")
            operations.append(response)

        # Verifica se todas as operações foram bem-sucedidas
        assert len(operations) == 10
        for response in operations:
            assert isinstance(response, str)
            assert len(response) > 0

        # Verifica integridade dos contextos
        contexts = agent.mcp.find_contexts_by_type(ContextType.CONVERSATION)
        assert len(contexts) >= 10


if __name__ == "__main__":
    pytest.main([__file__])
