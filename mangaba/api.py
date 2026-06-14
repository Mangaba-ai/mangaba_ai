from typing import Optional
from datetime import datetime
from mangaba.config import config
from mangaba.utils.logger import get_logger
from mangaba.protocols.a2a import A2AAgent, A2AMessage, MessageType
from mangaba.protocols.mcp import MCPProtocol, MCPContext, ContextType, ContextPriority
import uuid
from mangaba.core.llm import create_llm_client


class MangabaAgent(A2AAgent):
    """Agente de IA inteligente e versátil com protocolos A2A e MCP"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        agent_id: Optional[str] = None,
        enable_mcp: bool = True,
        agent_name: Optional[str] = None,
        use_mcp: Optional[bool] = None,
        use_a2a: Optional[bool] = None,
    ):
        """Inicializa o agente com capacidades A2A e MCP."""

        if agent_name and not agent_id:
            agent_id = agent_name
        if use_mcp is not None:
            enable_mcp = use_mcp
        self.use_a2a = True if use_a2a is None else use_a2a

        # Inicializa A2A
        self.agent_id = agent_id or f"mangaba_{uuid.uuid4().hex[:8]}"
        super().__init__(self.agent_id)

        # Configuração básica
        self.api_key = api_key or config.api_key
        self.model_name = model or config.model
        self.provider = getattr(config, "provider", "google")

        # Configura o provedor de IA através do cliente genérico
        self.llm = create_llm_client(
            provider=self.provider,
            api_key=self.api_key,
            model=self.model_name,
            temperature=getattr(config, "temperature", 0.7),
            max_output_tokens=getattr(config, "max_output_tokens", 1024),
            system_prompt=getattr(config, "system_prompt", None),
        )

        # Protocolo MCP
        self.mcp_enabled = enable_mcp
        if self.mcp_enabled:
            self.mcp = MCPProtocol()
            self.current_session_id = self.mcp.create_session(
                f"session_{self.agent_id}"
            )

            # Validar se sessão foi criada com sucesso
            if (
                not self.current_session_id
                or self.current_session_id not in self.mcp.sessions
            ):
                self.logger = get_logger(f"MangabaAgent[{self.agent_id}]")
                self.logger.error("❌ Falha ao criar sessão MCP")
                self.mcp_enabled = False
            else:
                self.logger = get_logger(f"MangabaAgent[{self.agent_id}]")
                self.logger.info(f"✅ Sessão MCP criada: {self.current_session_id}")
        else:
            # Logger
            self.logger = get_logger(f"MangabaAgent[{self.agent_id}]")

        if not hasattr(self, "logger"):
            # Logger
            self.logger = get_logger(f"MangabaAgent[{self.agent_id}]")
        self.logger.info(
            f"✅ Agente inicializado - ID: {self.agent_id}, "
            f"Provider: {self.provider}, Modelo: {self.model_name}"
        )

        # Configurações A2A específicas
        if self.use_a2a:
            self.setup_mangaba_handlers()

    def setup_mangaba_handlers(self):
        """Configura handlers específicos do Mangaba para A2A"""
        # Sobrescreve handlers padrão com versões específicas do Mangaba
        self.a2a_protocol.register_handler(
            MessageType.REQUEST, self.handle_mangaba_request
        )
        self.a2a_protocol.register_handler(
            MessageType.RESPONSE, self.handle_mangaba_response
        )

    def handle_mangaba_request(self, message: A2AMessage):
        """Handler específico para requisições Mangaba"""
        action = message.content.get("action")
        params = message.content.get("params", {})

        try:
            if action == "chat":
                result = self.chat(params.get("message", ""))
            elif action == "analyze":
                result = self.analyze_text(
                    params.get("text", ""), params.get("instruction", "")
                )
            elif action == "translate":
                result = self.translate(
                    params.get("text", ""), params.get("target_language", "português")
                )
            elif action == "get_context":
                result = self.get_context_summary()
            else:
                result = f"Ação '{action}' não reconhecida"
                response = self.a2a_protocol.create_response(message, result, False)
                self.logger.warning(f"⚠️  Ação desconhecida recebida: {action}")
                self.a2a_protocol.send_message(response)
                return

            response = self.a2a_protocol.create_response(message, result, True)
        except Exception as e:
            response = self.a2a_protocol.create_response(message, str(e), False)

        self.a2a_protocol.send_message(response)

    def handle_mangaba_response(self, message: A2AMessage):
        """Handler específico para respostas Mangaba"""
        self.logger.info(
            f"📨 Resposta de {message.sender_id}: {message.content.get('result', '')[:100]}..."
        )

        # Armazena resposta no contexto MCP se habilitado
        if self.mcp_enabled:
            context = MCPContext.create(
                context_type=ContextType.CONVERSATION,
                content={
                    "type": "agent_response",
                    "sender": message.sender_id,
                    "response": message.content,
                    "correlation_id": message.correlation_id,
                },
                priority=ContextPriority.MEDIUM,
                tags=["agent_communication", "response"],
            )
            self.mcp.add_context(context, self.current_session_id)

    def chat(self, message: str, use_context: bool = True) -> str:
        """Chat com suporte a contexto MCP"""
        try:
            # Adiciona mensagem do usuário ao contexto
            if self.mcp_enabled and use_context:
                user_context = MCPContext.create(
                    context_type=ContextType.CONVERSATION,
                    content={
                        "type": "user_message",
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                    },
                    priority=ContextPriority.HIGH,
                    tags=["user_input", "conversation"],
                )
                self.mcp.add_context(user_context, self.current_session_id)

                # Busca contexto relevante
                relevant_contexts = self.mcp.get_relevant_contexts(
                    message, max_results=5
                )
                if relevant_contexts:
                    context_info = "\n".join(
                        [f"- {ctx.content}" for ctx in relevant_contexts[:3]]
                    )
                    enhanced_message = f"Contexto relevante:\n{context_info}\n\nPergunta atual: {message}"
                else:
                    enhanced_message = message
            else:
                enhanced_message = message

            # Gera resposta
            result = self.llm.generate_text(enhanced_message)

            # Adiciona resposta ao contexto
            if self.mcp_enabled and use_context:
                ai_context = MCPContext.create(
                    context_type=ContextType.CONVERSATION,
                    content={
                        "type": "ai_response",
                        "message": result,
                        "original_query": message,
                    },
                    priority=ContextPriority.HIGH,
                    tags=["ai_response", "conversation"],
                )
                self.mcp.add_context(ai_context, self.current_session_id)

            self.logger.info(f"💬 Chat: {message[:50]}... → {result[:50]}...")
            return result

        except Exception as e:
            self.logger.error(f"❌ Erro no chat: {e}")
            return f"Erro: {str(e)}"

    def analyze_text(self, text: str, instruction: str = "Analise este texto") -> str:
        """Analisa texto com instrução específica"""
        try:
            prompt = f"{instruction}:\n\n{text}"
            result = self.llm.generate_text(prompt)

            # Adiciona ao contexto MCP se habilitado
            if self.mcp_enabled:
                analysis_context = MCPContext.create(
                    context_type=ContextType.TASK,
                    content={
                        "type": "text_analysis",
                        "original_text": text,
                        "instruction": instruction,
                        "analysis": result,
                    },
                    priority=ContextPriority.MEDIUM,
                    tags=["analysis", "task"],
                )
                self.mcp.add_context(analysis_context, self.current_session_id)

            self.logger.info(f"🔍 Análise: {text[:30]}... → {result[:50]}...")
            return result

        except Exception as e:
            self.logger.error(f"❌ Erro na análise: {e}")
            return f"Erro na análise: {str(e)}"

    def translate(self, text: str, target_language: str = "português") -> str:
        """Traduz texto para idioma específico"""
        try:
            prompt = f"Traduza o seguinte texto para {target_language}:\n\n{text}"
            result = self.llm.generate_text(prompt)

            # Adiciona ao contexto MCP se habilitado
            if self.mcp_enabled:
                translation_context = MCPContext.create(
                    context_type=ContextType.TASK,
                    content={
                        "type": "translation",
                        "original_text": text,
                        "target_language": target_language,
                        "translation": result,
                    },
                    priority=ContextPriority.LOW,
                    tags=["translation", "task"],
                )
                self.mcp.add_context(translation_context, self.current_session_id)

            self.logger.info(f"🌐 Tradução: {text[:30]}... → {target_language}")
            return result

        except Exception as e:
            self.logger.error(f"❌ Erro na tradução: {e}")
            return f"Erro na tradução: {str(e)}"

    def get_context_summary(self) -> str:
        """Retorna resumo do contexto atual da sessão MCP"""
        if not self.mcp_enabled:
            return "Contexto MCP não está habilitado"

        try:
            # Obter sessão atual
            session = self.mcp.sessions.get(self.current_session_id)
            if not session:
                return "Nenhuma sessão ativa encontrada"

            contexts = self.mcp.get_session_contexts(self.current_session_id)
            if not contexts:
                return "Nenhum contexto encontrado na sessão atual"

            # Agrupa contextos por tipo
            context_summary = {
                "conversation": [],
                "task": [],
                "memory": [],
                "system": [],
            }

            for ctx in contexts[-10:]:  # Últimos 10 contextos
                ctx_type = ctx.context_type.value
                if ctx_type in context_summary:
                    context_summary[ctx_type].append(
                        {
                            "content": str(ctx.content)[:100] + "..."
                            if len(str(ctx.content)) > 100
                            else str(ctx.content),
                            "priority": ctx.priority.value,
                            "tags": ctx.tags,
                        }
                    )

            summary_parts = []
            for ctx_type, items in context_summary.items():
                if items:
                    summary_parts.append(f"**{ctx_type.title()}** ({len(items)} itens)")
                    for item in items[:3]:  # Máximo 3 itens por tipo
                        summary_parts.append(
                            f"  - {item['content']} [Prioridade: {item['priority']}]"
                        )

            if not summary_parts:
                return "Contexto vazio"

            return "\n".join(summary_parts)

        except Exception as e:
            self.logger.error(f"❌ Erro ao obter resumo do contexto: {e}")
            return f"Erro ao obter contexto: {str(e)}"

    def send_agent_request(
        self, target_agent_id: str, action: str, params: dict = None
    ) -> str:
        """Envia requisição para outro agente via A2A"""
        try:
            if params is None:
                params = {}

            request = self.a2a_protocol.create_request(target_agent_id, action, params)

            self.a2a_protocol.send_message(request)
            self.logger.info(f"📤 Requisição enviada para {target_agent_id}: {action}")

            return f"Requisição '{action}' enviada para agente {target_agent_id}"

        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar requisição: {e}")
            return f"Erro ao enviar requisição: {str(e)}"

    def broadcast_message(self, message: str, tags: list = None) -> str:
        """Envia broadcast para todos os agentes conectados"""
        try:
            if tags is None:
                tags = ["general"]

            self.a2a_protocol.broadcast(
                {
                    "message": message,
                    "tags": tags,
                    "sender_info": {
                        "agent_id": self.agent_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                }
            )

            self.logger.info(f"📢 Broadcast enviado: {message[:50]}...")

            return "Broadcast enviado com sucesso"

        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar broadcast: {e}")
            return f"Erro ao enviar broadcast: {str(e)}"

    def chat_with_context(self, context: str, message: str) -> str:
        """Chat com contexto específico."""
        full_prompt = f"Contexto: {context}\n\nUsuário: {message}"
        return self.chat(full_prompt)

    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """Resume texto em número específico de frases."""
        prompt = (
            f"Resuma o seguinte texto em no máximo {max_sentences} frases:\n\n{text}"
        )
        return self.chat(prompt)

    def code_review(self, code: str, language: str = "Python") -> str:
        """Revisa código e sugere melhorias."""
        prompt = f"Revise este código {language} e sugira melhorias:\n\n```{language.lower()}\n{code}\n```"
        return self.chat(prompt)

    def explain_code(self, code: str, language: str = "Python") -> str:
        """Explica o que o código faz."""
        prompt = f"Explique o que este código {language} faz:\n\n```{language.lower()}\n{code}\n```"
        return self.chat(prompt)
