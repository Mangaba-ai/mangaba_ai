"""
Módulo de compatibilidade para manter suporte a `from mangaba_agent import MangabaAgent`.

Este arquivo re-exporta a classe MangabaAgent do pacote mangaba.api
para manter compatibilidade com código existente.

Uso recomendado:
    from mangaba.api import MangabaAgent  # Novo (recomendado)
    from mangaba_agent import MangabaAgent  # Antigo (ainda suportado)
"""

from mangaba.api import MangabaAgent

__all__ = ["MangabaAgent"]