"""
Sistema de modelo de prompt para construção de prompt estruturada.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """Um modelo de string com espaços reservados nomeados ``{variable}``."""

    template: str
    input_variables: Set[str] = Field(default_factory=set)

    def model_post_init(self, __context: Any) -> None:
        """Detecta automaticamente variáveis de entrada da string do modelo.

        Valida que variáveis declaradas estão presentes no modelo.

        Args:
            __context: Contexto Pydantic (não usado).

        Raises:
            ValueError: Se variáveis declaradas não forem encontradas no modelo.
        """
        # Detectar automaticamente variáveis do modelo
        detected = set(re.findall(r"\{(\w+)\}", self.template))
        if self.input_variables:
            missing = self.input_variables - detected
            if missing:
                raise ValueError(f"Declared variables not in template: {missing}")
        else:
            self.input_variables = detected

    def format(self, **kwargs: Any) -> str:
        """Formata o modelo com os valores de variáveis fornecidos.

        Args:
            **kwargs: Nomes de variáveis e seus valores para substituir no modelo.

        Returns:
            A string do modelo formatada com todos os espaços reservados substituídos.

        Raises:
            ValueError: Se variáveis de modelo necessárias estiverem faltando em kwargs.
        """
        missing = self.input_variables - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing template variables: {missing}")
        return self.template.format(**{k: str(v) for k, v in kwargs.items()})

    def partial(self, **kwargs: Any) -> PromptTemplate:
        """Retorna um novo modelo com algumas variáveis já preenchidas.

        Args:
            **kwargs: Nomes de variáveis e seus valores para preencher antecipadamente.

        Returns:
            Um novo PromptTemplate com as variáveis especificadas substituídas.
        """
        new_template = self.template
        for k, v in kwargs.items():
            new_template = new_template.replace(f"{{{k}}}", str(v))
        return PromptTemplate(template=new_template)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatPromptTemplate(BaseModel):
    """Um modelo que produz uma lista de mensagens de chat."""

    messages: List[ChatMessage] = Field(default_factory=list)

    def format(self, **kwargs: Any) -> List[Dict[str, str]]:
        """Formata todos os modelos de mensagem com os valores de variáveis fornecidos.

        Args:
            **kwargs: Nomes de variáveis e seus valores para substituir nos modelos.

        Returns:
            Uma lista de dicionários de mensagem com chaves 'role' e 'content'.
        """
        result = []
        for msg in self.messages:
            tpl = PromptTemplate(template=msg.content)
            formatted = tpl.format(**kwargs) if tpl.input_variables else msg.content
            result.append({"role": msg.role, "content": formatted})
        return result

    @classmethod
    def from_messages(cls, messages: List[tuple[str, str]]) -> ChatPromptTemplate:
        """Cria um ChatPromptTemplate a partir de uma lista de tuplas (role, content).

        Args:
            messages: Lista de tuplas (role, content) definindo as mensagens de chat.

        Returns:
            Uma instância ChatPromptTemplate com as mensagens especificadas.
        """
        return cls(messages=[ChatMessage(role=r, content=c) for r, c in messages])


class SystemPromptBuilder:
    """Compõe um prompt de sistema a partir de papel, ferramentas, contexto e guardrails."""

    def __init__(self) -> None:
        """Inicializa o construtor de prompt de sistema.

        Attributes:
            _sections: Lista de seções de prompt a serem unidas na construção final.
        """
        self._sections: List[str] = []

    def add_role(self, role: str, goal: str, backstory: str) -> SystemPromptBuilder:
        """Adiciona uma seção de definição de papel ao prompt de sistema.

        Args:
            role: O nome do papel (ex: "Desenvolvedor Sênior").
            goal: O objetivo ou meta do papel.
            backstory: Informações de contexto sobre o papel.

        Returns:
            Self para encadeamento de métodos.
        """
        self._sections.append(
            f"You are: {role}\n\nYour goal: {goal}\n\nBackground: {backstory}"
        )
        return self

    def add_tools_section(self, tools: List[Any]) -> SystemPromptBuilder:
        """Adiciona uma seção de ferramentas descrevendo funções disponíveis.

        Args:
            tools: Lista de objetos de ferramenta com método get_function_schema().

        Returns:
            Self para encadeamento de métodos.
        """
        if not tools:
            return self
        lines = ["You have access to the following tools:"]
        for t in tools:
            schema = t.get_function_schema()
            lines.append(f"- **{schema['name']}**: {schema['description']}")
        lines.append(
            "\nCall tools when needed. The framework will execute them and "
            "provide the results back to you."
        )
        self._sections.append("\n".join(lines))
        return self

    def add_context(self, context: str) -> SystemPromptBuilder:
        """Adiciona uma seção de contexto ao prompt de sistema.

        Args:
            context: Informações de contexto para fornecer ao LLM.

        Returns:
            Self para encadeamento de métodos.
        """
        if context:
            self._sections.append(f"Context:\n{context}")
        return self

    def add_guardrails(self, rules: List[str]) -> SystemPromptBuilder:
        """Adiciona uma seção de guardrails/regras ao prompt de sistema.

        Args:
            rules: Lista de regras ou restrições que o LLM deve seguir.

        Returns:
            Self para encadeamento de métodos.
        """
        if rules:
            lines = ["IMPORTANT RULES:"] + [f"- {r}" for r in rules]
            self._sections.append("\n".join(lines))
        return self

    def add_output_format(self, instructions: str) -> SystemPromptBuilder:
        """Adiciona instruções de formato de saída ao prompt de sistema.

        Args:
            instructions: Instruções para como a saída deve ser formatada.

        Returns:
            Self para encadeamento de métodos.
        """
        if instructions:
            self._sections.append(f"Output Format:\n{instructions}")
        return self

    def add_section(self, title: str, content: str) -> SystemPromptBuilder:
        """Adiciona uma seção personalizada ao prompt de sistema.

        Args:
            title: Título da seção.
            content: Conteúdo da seção.

        Returns:
            Self para encadeamento de métodos.
        """
        self._sections.append(f"{title}:\n{content}")
        return self

    def build(self) -> str:
        """Constrói o prompt de sistema final a partir de todas as seções adicionadas.

        Returns:
            A string completa do prompt de sistema com seções unidas por novas linhas duplas.
        """
        return "\n\n".join(self._sections)
