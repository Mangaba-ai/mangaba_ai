#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Análise de Texto com Mangaba Agent
Demonstra como usar o agente para análise avançada de textos
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba_agent import MangabaAgent


def analyze_sentiment():
    """Exemplo de análise de sentimento"""
    agent = MangabaAgent()

    texts = [
        "Estou muito feliz com os resultados do projeto!",
        "Que dia terrível, nada deu certo hoje.",
        "O produto é bom, mas poderia ser melhor.",
        "Excelente atendimento, recomendo a todos!",
    ]

    print("🎭 Análise de Sentimento")
    print("=" * 50)

    for i, text in enumerate(texts, 1):
        print(f"\n📝 Texto {i}: {text}")

        analysis = agent.analyze_text(
            text,
            "Analise o sentimento deste texto e classifique como positivo, negativo ou neutro. Explique brevemente.",
        )

        print(f"🔍 Análise: {analysis}")
        print("-" * 30)


def analyze_keywords():
    """Exemplo de extração de palavras-chave"""
    agent = MangabaAgent()

    article = """
    A inteligência artificial está revolucionando diversos setores da economia. 
    Machine learning e deep learning são tecnologias que permitem aos computadores 
    aprender padrões complexos em grandes volumes de dados. Empresas de tecnologia 
    investem bilhões em pesquisa e desenvolvimento de IA para criar soluções 
    inovadoras que automatizam processos e melhoram a eficiência operacional.
    """

    print("\n🔑 Extração de Palavras-chave")
    print("=" * 50)
    print(f"📄 Artigo: {article.strip()}")

    keywords = agent.analyze_text(
        article,
        "Extraia as 10 palavras-chave mais importantes deste texto e liste-as em ordem de relevância.",
    )

    print(f"\n🎯 Palavras-chave: {keywords}")


def analyze_structure():
    """Exemplo de análise estrutural de texto"""
    agent = MangabaAgent()

    document = """
    Introdução: Este relatório apresenta os resultados da pesquisa.
    
    Metodologia: Utilizamos uma abordagem quantitativa com 500 participantes.
    
    Resultados: Os dados mostram uma correlação positiva significativa.
    
    Conclusão: Os objetivos da pesquisa foram alcançados com sucesso.
    """

    print("\n📊 Análise Estrutural")
    print("=" * 50)
    print(f"📋 Documento: {document.strip()}")

    structure = agent.analyze_text(
        document,
        "Analise a estrutura deste documento e identifique as seções principais, avaliando se segue uma organização lógica.",
    )

    print(f"\n🏗️ Estrutura: {structure}")


def main():
    """Executa todos os exemplos de análise"""
    print("🤖 Mangaba Agent - Exemplos de Análise de Texto")
    print("=" * 60)

    try:
        analyze_sentiment()
        analyze_keywords()
        analyze_structure()

        print("\n✅ Todos os exemplos de análise foram executados com sucesso!")

    except Exception as e:
        print(f"❌ Erro durante a análise: {e}")


if __name__ == "__main__":
    main()
