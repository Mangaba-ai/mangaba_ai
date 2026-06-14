"""Protocolos A2A e MCP para Mangaba AI.

Este módulo fornece protocolos de comunicação entre agentes:

- A2A (Agent-to-Agent): Protocolo para comunicação direta de agentes
  com passagem de mensagens e descoberta de agentes.

- MCP (Model Context Protocol): Protocolo para compartilhamento de contexto
  e gerenciamento de sessões entre agentes e ferramentas.

Estes protocolos permitem sistemas multi-agentes onde agentes podem
comunicar, compartilhar contexto e coordenar ações.
"""

from .a2a import A2AProtocol, A2AMessage, A2AAgent
from .mcp import MCPProtocol, MCPContext, MCPSession

__all__ = [
    "A2AProtocol",
    "A2AMessage",
    "A2AAgent",
    "MCPProtocol",
    "MCPContext",
    "MCPSession",
]
