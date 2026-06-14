#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para o protocolo MCP (Model Context Protocol)
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba.protocols.mcp import (
    MCPContext,
    MCPSession,
    MCPProtocol,
    ContextType,
    ContextPriority,
)


class TestMCPContext:
    """Testes para a classe MCPContext"""

    def test_context_creation(self):
        """Testa criação de contexto MCP"""
        content = {"message": "test message", "user": "test_user"}
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content=content,
            priority=ContextPriority.HIGH,
            tags=["test", "conversation"],
        )

        assert context.context_type == ContextType.CONVERSATION
        assert context.content == content
        assert context.priority == ContextPriority.HIGH
        assert "test" in context.tags
        assert "conversation" in context.tags
        assert context.id is not None
        assert context.created_at is not None
        assert context.updated_at is not None

    def test_context_creation_with_expiration(self):
        """Testa criação de contexto com expiração"""
        context = MCPContext.create(
            context_type=ContextType.MEMORY,
            content={"data": "temporary"},
            expires_in_hours=24,
        )

        assert context.expires_at is not None
        expires_time = datetime.fromisoformat(context.expires_at)
        created_time = datetime.fromisoformat(context.created_at)

        # Verifica se a expiração está aproximadamente 24 horas no futuro
        time_diff = expires_time - created_time
        assert abs(time_diff.total_seconds() - 24 * 3600) < 60  # Margem de 1 minuto

    def test_context_creation_with_parent(self):
        """Testa criação de contexto com pai"""
        parent_context = MCPContext.create(
            context_type=ContextType.TASK, content={"task": "parent_task"}
        )

        child_context = MCPContext.create(
            context_type=ContextType.TASK,
            content={"subtask": "child_task"},
            parent_id=parent_context.id,
        )

        assert child_context.parent_id == parent_context.id

    def test_update_content(self):
        """Testa atualização de conteúdo"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "original"}
        )

        original_updated_at = context.updated_at

        # Pequena pausa para garantir timestamp diferente
        import time

        time.sleep(0.01)

        context.update_content({"message": "updated", "new_field": "value"})

        assert context.content["message"] == "updated"
        assert context.content["new_field"] == "value"
        assert context.updated_at != original_updated_at

    def test_add_tag(self):
        """Testa adição de tag"""
        context = MCPContext.create(
            context_type=ContextType.KNOWLEDGE,
            content={"info": "test"},
            tags=["initial"],
        )

        original_updated_at = context.updated_at

        # Pequena pausa para garantir timestamp diferente
        import time

        time.sleep(0.01)

        context.add_tag("new_tag")

        assert "new_tag" in context.tags
        assert "initial" in context.tags
        assert context.updated_at != original_updated_at

    def test_add_duplicate_tag(self):
        """Testa adição de tag duplicada"""
        context = MCPContext.create(
            context_type=ContextType.KNOWLEDGE,
            content={"info": "test"},
            tags=["existing"],
        )

        original_tags_count = len(context.tags)
        context.add_tag("existing")

        assert len(context.tags) == original_tags_count

    def test_is_expired_false(self):
        """Testa contexto não expirado"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "test"},
            expires_in_hours=1,
        )

        assert not context.is_expired()

    def test_is_expired_true(self):
        """Testa contexto expirado"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test"}
        )

        # Define expiração no passado
        past_time = datetime.now() - timedelta(hours=1)
        context.expires_at = past_time.isoformat()

        assert context.is_expired()

    def test_is_expired_no_expiration(self):
        """Testa contexto sem expiração"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test"}
        )

        assert not context.is_expired()

    def test_get_hash(self):
        """Testa geração de hash do conteúdo"""
        # Usa dicionários distintos para evitar compartilhamento de referência
        context1 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "test", "user": "test_user"},
        )
        context2 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "test", "user": "test_user"},
        )

        # Mesmo conteúdo deve gerar mesmo hash
        assert context1.get_hash() == context2.get_hash()

        # Conteúdo diferente deve gerar hash diferente
        # Cria novo contexto com conteúdo diferente
        context3 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "different", "user": "test_user"},
        )
        assert context1.get_hash() != context3.get_hash()

    def test_to_dict(self):
        """Testa conversão para dicionário"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "test"},
            tags=["test"],
        )

        context_dict = context.to_dict()

        assert isinstance(context_dict, dict)
        assert context_dict["context_type"] == "conversation"
        assert context_dict["priority"] == 2  # MEDIUM
        assert context_dict["content"] == {"message": "test"}
        assert context_dict["tags"] == ["test"]

    def test_from_dict(self):
        """Testa criação a partir de dicionário"""
        context_data = {
            "id": "test_id",
            "context_type": "conversation",
            "content": {"message": "test"},
            "priority": 3,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "expires_at": None,
            "tags": ["test"],
            "metadata": {},
            "parent_id": None,
            "children_ids": [],
        }

        context = MCPContext.from_dict(context_data)

        assert context.id == "test_id"
        assert context.context_type == ContextType.CONVERSATION
        assert context.priority == ContextPriority.HIGH
        assert context.content == {"message": "test"}


class TestMCPSession:
    """Testes para a classe MCPSession"""

    def test_session_creation(self):
        """Testa criação de sessão MCP"""
        session = MCPSession.create("test_session")

        assert session.name == "test_session"
        assert session.id is not None
        assert session.created_at is not None
        assert session.updated_at is not None
        assert isinstance(session.context_ids, list)
        assert len(session.context_ids) == 0
        assert isinstance(session.metadata, dict)


class TestMCPProtocol:
    """Testes para a classe MCPProtocol"""

    @pytest.fixture
    def protocol(self):
        """Fixture para criar um protocolo MCP"""
        return MCPProtocol(max_contexts=100)

    def test_protocol_initialization(self, protocol):
        """Testa inicialização do protocolo"""
        assert protocol.max_contexts == 100
        assert len(protocol.contexts) == 0
        assert len(protocol.sessions) == 0

    def test_add_context(self, protocol):
        """Testa adição de contexto"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test"}
        )

        context_id = protocol.add_context(context)

        assert context_id == context.id
        assert context.id in protocol.contexts
        assert protocol.contexts[context.id] == context

    def test_add_context_to_session(self, protocol):
        """Testa adição de contexto a uma sessão"""
        session_id = protocol.create_session("test_session")
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test"}
        )

        context_id = protocol.add_context(context, session_id)

        assert context_id in protocol.sessions[session_id].context_ids

    def test_get_context(self, protocol):
        """Testa obtenção de contexto"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test"}
        )

        context_id = protocol.add_context(context)
        retrieved_context = protocol.get_context(context_id)

        assert retrieved_context == context

    def test_get_nonexistent_context(self, protocol):
        """Testa obtenção de contexto inexistente"""
        result = protocol.get_context("nonexistent_id")
        assert result is None

    def test_update_context(self, protocol):
        """Testa atualização de contexto"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "original"}
        )

        context_id = protocol.add_context(context)
        result = protocol.update_context(context_id, {"message": "updated"})

        assert result is True
        updated_context = protocol.get_context(context_id)
        assert updated_context.content["message"] == "updated"

    def test_update_nonexistent_context(self, protocol):
        """Testa atualização de contexto inexistente"""
        result = protocol.update_context("nonexistent_id", {"data": "test"})
        assert result is False

    def test_remove_context(self, protocol):
        """Testa remoção de contexto"""
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test"}
        )

        context_id = protocol.add_context(context)
        result = protocol.remove_context(context_id)

        assert result is True
        assert context_id not in protocol.contexts

    def test_remove_context_from_session(self, protocol):
        """Testa remoção de contexto de sessão"""
        session_id = protocol.create_session("test_session")
        context = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test"}
        )

        context_id = protocol.add_context(context, session_id)
        result = protocol.remove_context(context_id)

        assert result is True
        assert context_id not in protocol.sessions[session_id].context_ids

    def test_remove_nonexistent_context(self, protocol):
        """Testa remoção de contexto inexistente"""
        result = protocol.remove_context("nonexistent_id")
        assert result is False

    def test_find_contexts_by_tag(self, protocol):
        """Testa busca de contextos por tag"""
        context1 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "test1"},
            tags=["important", "conversation"],
        )
        context2 = MCPContext.create(
            context_type=ContextType.TASK,
            content={"task": "test2"},
            tags=["important", "task"],
        )
        context3 = MCPContext.create(
            context_type=ContextType.MEMORY,
            content={"memory": "test3"},
            tags=["memory"],
        )

        protocol.add_context(context1)
        protocol.add_context(context2)
        protocol.add_context(context3)

        important_contexts = protocol.find_contexts_by_tag("important")

        assert len(important_contexts) == 2
        assert context1 in important_contexts
        assert context2 in important_contexts
        assert context3 not in important_contexts

    def test_find_contexts_by_type(self, protocol):
        """Testa busca de contextos por tipo"""
        context1 = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test1"}
        )
        context2 = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test2"}
        )
        context3 = MCPContext.create(
            context_type=ContextType.TASK, content={"task": "test3"}
        )

        protocol.add_context(context1)
        protocol.add_context(context2)
        protocol.add_context(context3)

        conversation_contexts = protocol.find_contexts_by_type(ContextType.CONVERSATION)

        assert len(conversation_contexts) == 2
        assert context1 in conversation_contexts
        assert context2 in conversation_contexts
        assert context3 not in conversation_contexts

    def test_find_contexts_by_priority(self, protocol):
        """Testa busca de contextos por prioridade mínima"""
        context1 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "low"},
            priority=ContextPriority.LOW,
        )
        context2 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "medium"},
            priority=ContextPriority.MEDIUM,
        )
        context3 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "high"},
            priority=ContextPriority.HIGH,
        )
        context4 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "critical"},
            priority=ContextPriority.CRITICAL,
        )

        protocol.add_context(context1)
        protocol.add_context(context2)
        protocol.add_context(context3)
        protocol.add_context(context4)

        high_priority_contexts = protocol.find_contexts_by_priority(
            ContextPriority.HIGH
        )

        assert len(high_priority_contexts) == 2
        assert context3 in high_priority_contexts
        assert context4 in high_priority_contexts
        assert context1 not in high_priority_contexts
        assert context2 not in high_priority_contexts

    def test_create_session(self, protocol):
        """Testa criação de sessão"""
        session_id = protocol.create_session("test_session")

        assert session_id is not None
        assert session_id in protocol.sessions
        assert protocol.sessions[session_id].name == "test_session"

    def test_get_session_contexts(self, protocol):
        """Testa obtenção de contextos de sessão"""
        session_id = protocol.create_session("test_session")

        context1 = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test1"}
        )
        context2 = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "test2"}
        )

        protocol.add_context(context1, session_id)
        protocol.add_context(context2, session_id)

        session_contexts = protocol.get_session_contexts(session_id)

        assert len(session_contexts) == 2
        assert context1 in session_contexts
        assert context2 in session_contexts

    def test_get_relevant_contexts(self, protocol):
        """Testa busca de contextos relevantes"""
        context1 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "Python programming tutorial"},
            tags=["programming", "python"],
        )
        context2 = MCPContext.create(
            context_type=ContextType.KNOWLEDGE,
            content={"info": "JavaScript web development"},
            tags=["programming", "javascript"],
        )
        context3 = MCPContext.create(
            context_type=ContextType.MEMORY,
            content={"memory": "Cooking recipes"},
            tags=["cooking", "food"],
        )

        protocol.add_context(context1)
        protocol.add_context(context2)
        protocol.add_context(context3)

        relevant_contexts = protocol.get_relevant_contexts("python programming")

        # O contexto sobre Python deve ser mais relevante
        assert len(relevant_contexts) > 0
        assert context1 in relevant_contexts

    def test_cleanup_expired_contexts(self, protocol):
        """Testa limpeza de contextos expirados"""
        # Contexto não expirado
        context1 = MCPContext.create(
            context_type=ContextType.CONVERSATION,
            content={"message": "current"},
            expires_in_hours=1,
        )

        # Contexto expirado
        context2 = MCPContext.create(
            context_type=ContextType.CONVERSATION, content={"message": "expired"}
        )
        past_time = datetime.now() - timedelta(hours=1)
        context2.expires_at = past_time.isoformat()

        protocol.add_context(context1)
        protocol.add_context(context2)

        assert len(protocol.contexts) == 2

        protocol._cleanup_expired_contexts()

        assert len(protocol.contexts) == 1
        assert context1.id in protocol.contexts
        assert context2.id not in protocol.contexts

    def test_max_contexts_limit(self, protocol):
        """Testa limite máximo de contextos"""
        # Adiciona contextos até o limite
        for i in range(protocol.max_contexts + 10):
            context = MCPContext.create(
                context_type=ContextType.CONVERSATION, content={"message": f"test_{i}"}
            )
            protocol.add_context(context)

        # Deve manter apenas o limite máximo
        assert len(protocol.contexts) <= protocol.max_contexts

    def test_get_context_summary(self, protocol):
        """Testa obtenção de resumo de contextos"""
        # Adiciona alguns contextos
        for i in range(5):
            context = MCPContext.create(
                context_type=ContextType.CONVERSATION,
                content={"message": f"test_{i}"},
                priority=ContextPriority.MEDIUM,
            )
            protocol.add_context(context)

        summary = protocol.get_context_summary()

        assert isinstance(summary, dict)
        assert "total_contexts" in summary
        assert "contexts_by_type" in summary
        assert "contexts_by_priority" in summary
        assert summary["total_contexts"] == 5


if __name__ == "__main__":
    pytest.main([__file__])
