"""
Ferramentas de manipulação de arquivos
"""

import os
from typing import Optional
from mangaba.tools.base import BaseTool


class FileReaderTool(BaseTool):
    """Ferramenta para ler arquivos de texto.

    Exemplo:
        tool = FileReaderTool()
        content = tool.run("document.txt")
    """

    name = "file_reader"
    description = "Lê arquivos de texto e retorna seu conteúdo"

    def _run(self, file_path: str, encoding: str = "utf-8") -> str:
        """Lê o conteúdo de um arquivo.

        Args:
            file_path: Caminho para o arquivo.
            encoding: Codificação do arquivo (padrão: utf-8).

        Returns:
            O conteúdo do arquivo.
        """
        try:
            if not os.path.exists(file_path):
                return f"Error: File '{file_path}' not found"

            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            return content

        except Exception as e:
            return f"Error reading file: {str(e)}"


class FileWriterTool(BaseTool):
    """Ferramenta para escrever em arquivos.

    Exemplo:
        tool = FileWriterTool()
        tool.run("output.txt", "Conteúdo para escrever")
    """

    name = "file_writer"
    description = "Escreve conteúdo em arquivos de texto"

    def _run(
        self, file_path: str, content: str, mode: str = "w", encoding: str = "utf-8"
    ) -> str:
        """Escreve conteúdo em um arquivo.

        Args:
            file_path: Caminho para o arquivo.
            content: Conteúdo para escrever.
            mode: Modo de escrita ('w' para escrever ou 'a' para anexar).
            encoding: Codificação do arquivo (padrão: utf-8).

        Returns:
            Mensagem de sucesso ou mensagem de erro.
        """
        try:
            # Criar diretório se não existir
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)

            return f"Successfully wrote to '{file_path}'"

        except Exception as e:
            return f"Error writing file: {str(e)}"


class DirectoryListTool(BaseTool):
    """Ferramenta para listar o conteúdo de diretórios.

    Exemplo:
        tool = DirectoryListTool()
        files = tool.run("./documents")
    """

    name = "directory_list"
    description = "Lista arquivos e diretórios em um caminho fornecido"

    def _run(self, directory_path: str, pattern: Optional[str] = None) -> str:
        """Lista o conteúdo de um diretório.

        Args:
            directory_path: Caminho para o diretório.
            pattern: Padrão de filtro (por exemplo, "*.txt").

        Returns:
            Lista formatada de arquivos e pastas.
        """
        try:
            if not os.path.exists(directory_path):
                return f"Error: Directory '{directory_path}' not found"

            if not os.path.isdir(directory_path):
                return f"Error: '{directory_path}' is not a directory"

            items = os.listdir(directory_path)

            # Aplicar filtro se especificado
            if pattern:
                import fnmatch

                items = [item for item in items if fnmatch.fnmatch(item, pattern)]

            if not items:
                return "Directory is empty or no files match the pattern"

            # Separar arquivos e diretórios
            files = []
            directories = []

            for item in sorted(items):
                full_path = os.path.join(directory_path, item)
                if os.path.isdir(full_path):
                    directories.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(full_path)
                    files.append(f"📄 {item} ({size} bytes)")

            result = []
            if directories:
                result.append("Directories:")
                result.extend(directories)
            if files:
                result.append("\nFiles:")
                result.extend(files)

            return "\n".join(result)

        except Exception as e:
            return f"Error listing directory: {str(e)}"
