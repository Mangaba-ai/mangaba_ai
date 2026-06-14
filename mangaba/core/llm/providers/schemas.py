"""Esquemas para declarações de ferramentas de provedores LLM"""

from pydantic import BaseModel
from typing import Any, Dict, List
import json


class GoogleToolSchemaDeclaration(BaseModel):
    name: str
    description: str
    parameters: dict


class OpenAIToolSchemaDeclaration(BaseModel):
    type: str
    function: dict


class AnthropicToolSchemaDeclaration(BaseModel):
    name: str
    description: str
    input_schema: dict


def _tool_to_google_declaration(tool: Any) -> Dict[str, Any]:
    """Converte um BaseTool para o formato de declaração de função Google.

    Args:
        tool: Uma instância BaseTool com método get_function_schema().

    Returns:
        Dicionário no formato de declaração de função Google.
    """
    schema = tool.get_function_schema()
    return GoogleToolSchemaDeclaration(**schema).model_dump()


def _tool_to_openai_schema(tool: Any) -> Dict[str, Any]:
    """Converte um BaseTool para o formato de chamada de função OpenAI.

    Args:
        tool: Uma instância BaseTool com método get_function_schema().

    Returns:
        Dicionário no formato de chamada de função OpenAI.
    """
    schema = tool.get_function_schema()
    return OpenAIToolSchemaDeclaration(**schema).model_dump()


def _tool_to_anthropic_schema(tool: Any) -> Dict[str, Any]:
    """Converte um BaseTool para o formato de uso de ferramenta Anthropic.

    Args:
        tool: Uma instância BaseTool com método get_function_schema().

    Returns:
        Dicionário no formato de uso de ferramenta Anthropic.
    """
    schema = tool.get_function_schema()
    return AnthropicToolSchemaDeclaration(**schema).model_dump()


def _tools_to_hf_prompt_section(tools: List[Any]) -> str:
    """Renderiza ferramentas disponíveis como uma seção de prompt de sistema para Hugging Face.

    Cria uma seção de texto formatada descrevendo ferramentas disponíveis e seus
    parâmetros para modelos Hugging Face que usam chamada de ferramenta baseada em prompt.

    Args:
        tools: Lista de instâncias BaseTool com método get_function_schema().

    Returns:
        String formatada descrevendo ferramentas disponíveis, ou string vazia se não houver ferramentas.
    """
    if not tools:
        return ""
    lines = ["You have access to the following tools:\n"]
    for t in tools:
        schema = t.get_function_schema()
        params = json.dumps(schema.get("parameters", {}), indent=2)
        lines.append(
            f"### {schema['name']}\n{schema['description']}\nParameters: {params}\n"
        )
    lines.append(
        "To use a tool, respond ONLY with a JSON block:\n"
        '```json\n{"tool_calls": [{"tool_name": "<name>", "arguments": {<args>}}]}\n```\n'
        "If no tool is needed, respond normally."
    )
    return "\n".join(lines)
