"""
Carregadores de documentos para pipeline RAG do Mangaba AI.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

from mangaba.rag.document import Document


class TextLoader:
    """Carrega um arquivo de texto simples como um único Document.

    Attributes:
        file_path: O caminho para o arquivo de texto para carregar.
        encoding: A codificação do arquivo (padrão: "utf-8").
    """

    def __init__(self, file_path: str, encoding: str = "utf-8") -> None:
        """Inicializa o TextLoader.

        Args:
            file_path: O caminho para o arquivo de texto para carregar.
            encoding: A codificação do arquivo (padrão: "utf-8").
        """
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> List[Document]:
        """Carrega o arquivo de texto como um Document.

        Returns:
            Uma lista contendo um único Document com o conteúdo do arquivo.
        """
        path = Path(self.file_path)
        text = path.read_text(encoding=self.encoding)
        return [Document(content=text, metadata={"source": str(path)})]


class CSVLoader:
    """Carrega um arquivo CSV, criando um Document para cada linha.

    Attributes:
        file_path: O caminho para o arquivo CSV para carregar.
        content_columns: Lista opcional de nomes de colunas para usar como conteúdo.
            Se não fornecido, todas as colunas são unidas.
        encoding: A codificação do arquivo (padrão: "utf-8").
    """

    def __init__(
        self,
        file_path: str,
        content_columns: Optional[List[str]] = None,
        encoding: str = "utf-8",
    ) -> None:
        """Inicializa o CSVLoader.

        Args:
            file_path: O caminho para o arquivo CSV para carregar.
            content_columns: Lista opcional de nomes de colunas para usar como conteúdo.
                Se não fornecido, todas as colunas são unidas.
            encoding: A codificação do arquivo (padrão: "utf-8").
        """
        self.file_path = file_path
        self.content_columns = content_columns
        self.encoding = encoding

    def load(self) -> List[Document]:
        """Carrega o arquivo CSV como Documents.

        Returns:
            Uma lista de Documents, um para cada linha no arquivo CSV.
        """
        path = Path(self.file_path)
        docs: List[Document] = []
        with path.open(encoding=self.encoding, newline="") as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                if self.content_columns:
                    text = " | ".join(str(row.get(c, "")) for c in self.content_columns)
                else:
                    text = " | ".join(str(v) for v in row.values())
                meta: Dict[str, str] = {"source": str(path), "row": str(i)}
                docs.append(Document(content=text, metadata=meta))
        return docs


class WebPageLoader:
    """Carrega uma página web como um Document.

    Este carregador requer os pacotes requests e beautifulsoup4.

    Attributes:
        url: A URL da página web para carregar.
    """

    def __init__(self, url: str) -> None:
        """Inicializa o WebPageLoader.

        Args:
            url: A URL da página web para carregar.
        """
        self.url = url

    def load(self) -> List[Document]:
        """Carrega a página web como um Document.

        Returns:
            Uma lista contendo um único Document com o conteúdo da página web.

        Raises:
            requests.HTTPError: Se a solicitação HTTP falhar.
        """
        import requests  # already in dependencies

        resp = requests.get(self.url, timeout=15)
        resp.raise_for_status()
        try:
            from bs4 import BeautifulSoup  # type: ignore

            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove script/style
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        except ImportError:
            text = resp.text
        return [Document(content=text, metadata={"source": self.url})]
