#!/usr/bin/env python3
"""Busca web e leitura de páginas via Parallel Search MCP, sem chave de API.

Uso (na raiz do checkout, após `pip install -e .`):
    python examples/parallel_search_mcp.py "Python asyncio TaskGroup"
    python examples/parallel_search_mcp.py "Python asyncio TaskGroup" \
        --url https://docs.python.org/3/library/asyncio-task.html

Usa o transporte HTTP do MCPClient e as ferramentas BaseTool do Mangaba.
Não chama um LLM; inferência com Agent/Crew é configurada separadamente.
"""

import argparse
import json
from uuid import uuid4

from mangaba import MCPClient


PARALLEL_MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "mangaba-ai/4.0.0 (Parallel Search MCP example)"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="Python asyncio TaskGroup", help="Consulta de busca")
    parser.add_argument("--url", action="append", help="URL para ler após a busca (pode repetir, até 20 URLs)")
    args = parser.parse_args()
    if args.url and len(args.url) > 20:
        parser.error("--url aceita no máximo 20 URLs por chamada")

    # Uma sessão por execução, compartilhada entre busca e leitura.
    session_id = str(uuid4())
    with MCPClient(
        url=PARALLEL_MCP_URL,
        headers={"User-Agent": USER_AGENT},
        name="parallel-search",
        tool_prefix="parallel_",
    ) as mcp:
        tools = {tool.name: tool for tool in mcp.get_tools(include=["web_search", "web_fetch"])}
        result = tools["parallel_web_search"].run(
            objective=args.query,
            search_queries=[args.query],
            session_id=session_id,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.url:
            result = tools["parallel_web_fetch"].run(
                urls=args.url,
                objective=args.query[:200],
                search_queries=[args.query],
                session_id=session_id,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
