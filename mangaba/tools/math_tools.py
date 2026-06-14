"""
Ferramentas matemáticas para Mangaba AI v3.0
"""

from __future__ import annotations

import ast
import operator
from typing import Any

from pydantic import BaseModel, Field

from mangaba.tools.base import BaseTool


class CalculatorInput(BaseModel):
    """Esquema de entrada para a ferramenta de calculadora."""

    expression: str = Field(
        ..., description="Expressão matemática para avaliar, por exemplo, '2 + 3 * 4'"
    )


class CalculatorTool(BaseTool):
    """Avalia expressões matemáticas com segurança.

    Suporta operações aritméticas básicas: adição, subtração, multiplicação,
    divisão, divisão inteira, módulo e exponenciação. Usa análise AST para
    garantir avaliação segura sem executar código arbitrário.
    """

    name = "calculator"
    description = "Avalia uma expressão matemática e retorna o resultado numérico"
    args_schema = CalculatorInput

    _SAFE_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _run(self, expression: str) -> str:
        """Avalia uma expressão matemática.

        Args:
            expression: A expressão matemática para avaliar.

        Returns:
            O resultado numérico como string ou uma mensagem de erro se a avaliação falhar.
        """
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._eval_node(tree.body)
            return str(result)
        except (ValueError, TypeError, ZeroDivisionError, SyntaxError) as exc:
            return f"Error: {exc}"

    def _eval_node(self, node: ast.AST) -> Any:
        """Avalia recursivamente um nó AST.

        Args:
            node: O nó AST para avaliar.

        Returns:
            O valor avaliado do nó.

        Raises:
            ValueError: Se o tipo ou valor do nó não for suportado.
        """
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, complex)):
                return node.value
            raise ValueError(f"Unsupported constant: {node.value!r}")
        if isinstance(node, ast.BinOp):
            op_fn = self._SAFE_OPS.get(type(node.op))
            if op_fn is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op_fn(self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op_fn = self._SAFE_OPS.get(type(node.op))
            if op_fn is None:
                raise ValueError(
                    f"Unsupported unary operator: {type(node.op).__name__}"
                )
            return op_fn(self._eval_node(node.operand))
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")
