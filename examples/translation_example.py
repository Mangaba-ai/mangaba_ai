#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Tradução com Mangaba Agent
Demonstra capacidades de tradução multilíngue
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba_agent import MangabaAgent


def translate_basic():
    """Exemplo de tradução básica"""
    agent = MangabaAgent()

    texts = {
        "português": "Olá, como você está hoje?",
        "inglês": "Hello, how are you today?",
        "espanhol": "Hola, ¿cómo estás hoy?",
        "francês": "Bonjour, comment allez-vous aujourd'hui?",
    }

    target_languages = ["inglês", "espanhol", "francês", "alemão", "italiano"]

    print("🌍 Tradução Básica")
    print("=" * 50)

    for source_lang, text in texts.items():
        print(f"\n📝 Texto original ({source_lang}): {text}")

        for target_lang in target_languages:
            if target_lang != source_lang:
                translation = agent.translate(text, f"Traduza para {target_lang}")
                print(f"🔄 {target_lang}: {translation}")

        print("-" * 40)


def translate_technical():
    """Exemplo de tradução técnica"""
    agent = MangabaAgent()

    technical_texts = {
        "Machine learning algorithms can process vast amounts of data to identify patterns and make predictions.": "inglês",
        "Les algorithmes d'apprentissage automatique peuvent traiter de grandes quantités de données.": "francês",
        "Los algoritmos de aprendizaje automático pueden procesar grandes cantidades de datos.": "espanhol",
    }

    print("\n🔬 Tradução Técnica")
    print("=" * 50)

    for text, source_lang in technical_texts.items():
        print(f"\n📄 Texto técnico ({source_lang}):")
        print(f"   {text}")

        # Traduz para português mantendo termos técnicos
        translation = agent.translate(
            text,
            "Traduza para português brasileiro, mantendo a precisão dos termos técnicos",
        )

        print(f"🇧🇷 Português: {translation}")
        print("-" * 40)


def translate_context_aware():
    """Exemplo de tradução com contexto"""
    agent = MangabaAgent()

    contexts = [
        {
            "context": "Contexto médico",
            "text": "The patient presents acute symptoms and requires immediate intervention.",
            "instruction": "Traduza para português usando terminologia médica apropriada",
        },
        {
            "context": "Contexto jurídico",
            "text": "The contract stipulates the terms and conditions for both parties.",
            "instruction": "Traduza para português usando linguagem jurídica formal",
        },
        {
            "context": "Contexto informal",
            "text": "Hey, what's up? Want to grab some coffee later?",
            "instruction": "Traduza para português brasileiro informal",
        },
    ]

    print("\n🎯 Tradução Contextual")
    print("=" * 50)

    for item in contexts:
        print(f"\n📋 {item['context']}:")
        print(f"📝 Original: {item['text']}")

        translation = agent.translate(item["text"], item["instruction"])
        print(f"🔄 Tradução: {translation}")
        print("-" * 40)


def translate_batch():
    """Exemplo de tradução em lote"""
    agent = MangabaAgent()

    batch_texts = [
        "Good morning!",
        "Thank you very much.",
        "See you later.",
        "Have a great day!",
        "Nice to meet you.",
    ]

    print("\n📦 Tradução em Lote")
    print("=" * 50)

    print("🔄 Traduzindo frases do inglês para português...")

    for i, text in enumerate(batch_texts, 1):
        translation = agent.translate(text, "Traduza para português brasileiro")
        print(f"{i}. {text} → {translation}")


def main():
    """Executa todos os exemplos de tradução"""
    print("🤖 Mangaba Agent - Exemplos de Tradução")
    print("=" * 60)

    try:
        translate_basic()
        translate_technical()
        translate_context_aware()
        translate_batch()

        print("\n✅ Todos os exemplos de tradução foram executados com sucesso!")
        print(
            "\n💡 Dica: O agente mantém contexto das traduções para melhorar a consistência."
        )

    except Exception as e:
        print(f"❌ Erro durante a tradução: {e}")


if __name__ == "__main__":
    main()
