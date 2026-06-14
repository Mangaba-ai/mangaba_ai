#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Machine Learning e Análise Preditiva com Mangaba Agent
Demonstra análise de dados, modelagem preditiva e insights de ML
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba_agent import MangabaAgent
import json
import random
import math
from datetime import datetime, timedelta


class DataGenerator:
    """Gerador de dados sintéticos para demonstração"""

    @staticmethod
    def generate_sales_data(days=365):
        """Gera dados de vendas sintéticos"""
        base_date = datetime.now() - timedelta(days=days)
        sales_data = []

        for i in range(days):
            date = base_date + timedelta(days=i)

            # Simula sazonalidade e tendência
            trend = i * 0.1
            seasonal = 50 * math.sin(2 * math.pi * i / 365) + 50 * math.sin(
                2 * math.pi * i / 7
            )
            noise = random.gauss(0, 20)

            sales = max(0, 100 + trend + seasonal + noise)

            sales_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "sales": round(sales, 2),
                    "day_of_week": date.weekday(),
                    "month": date.month,
                    "is_weekend": date.weekday() >= 5,
                }
            )

        return sales_data

    @staticmethod
    def generate_customer_data(count=1000):
        """Gera dados de clientes sintéticos"""
        customers = []

        for i in range(count):
            age = random.randint(18, 80)
            income = random.randint(20000, 150000)

            # Correlação entre idade, renda e comportamento
            purchase_frequency = max(1, int(income / 10000) + random.randint(-2, 2))
            avg_order_value = max(10, income / 1000 + random.gauss(0, 20))

            customers.append(
                {
                    "customer_id": f"CUST_{i:04d}",
                    "age": age,
                    "income": income,
                    "purchase_frequency": purchase_frequency,
                    "avg_order_value": round(avg_order_value, 2),
                    "total_spent": round(purchase_frequency * avg_order_value, 2),
                    "registration_date": (
                        datetime.now() - timedelta(days=random.randint(1, 730))
                    ).strftime("%Y-%m-%d"),
                    "segment": "high_value"
                    if income > 100000
                    else "medium_value"
                    if income > 50000
                    else "low_value",
                }
            )

        return customers

    @staticmethod
    def generate_product_data(count=100):
        """Gera dados de produtos sintéticos"""
        categories = ["Electronics", "Clothing", "Books", "Home", "Sports", "Beauty"]
        products = []

        for i in range(count):
            category = random.choice(categories)
            base_price = random.uniform(10, 500)

            # Simula diferentes métricas por categoria
            if category == "Electronics":
                margin = random.uniform(0.15, 0.25)
                return_rate = random.uniform(0.02, 0.08)
            elif category == "Clothing":
                margin = random.uniform(0.40, 0.60)
                return_rate = random.uniform(0.10, 0.20)
            else:
                margin = random.uniform(0.20, 0.40)
                return_rate = random.uniform(0.05, 0.15)

            products.append(
                {
                    "product_id": f"PROD_{i:03d}",
                    "name": f"{category} Product {i}",
                    "category": category,
                    "price": round(base_price, 2),
                    "cost": round(base_price * (1 - margin), 2),
                    "margin": round(margin * 100, 1),
                    "monthly_sales": random.randint(10, 500),
                    "return_rate": round(return_rate * 100, 2),
                    "rating": round(random.uniform(3.0, 5.0), 1),
                    "stock_level": random.randint(0, 200),
                }
            )

        return products


def demo_sales_forecasting():
    """Demonstra previsão de vendas"""
    print("📈 Previsão de Vendas")
    print("=" * 40)

    agent = MangabaAgent(agent_id="sales_forecaster")

    # Gera dados históricos de vendas
    sales_data = DataGenerator.generate_sales_data(365)

    print(f"📊 Analisando {len(sales_data)} dias de dados de vendas...")

    # Análise de tendências
    trend_analysis_prompt = f"""
    Analise os seguintes dados de vendas históricos:
    
    Período: {sales_data[0]["date"]} a {sales_data[-1]["date"]}
    Total de registros: {len(sales_data)}
    
    Amostra dos dados:
    {json.dumps(sales_data[:10], indent=2)}
    
    Identifique:
    1. Tendências de crescimento/declínio
    2. Padrões sazonais
    3. Influência do dia da semana
    4. Anomalias ou outliers
    5. Fatores que afetam as vendas
    """

    trend_analysis = agent.chat(trend_analysis_prompt, use_context=True)
    print(f"📊 Análise de Tendências: {trend_analysis}")

    # Previsão para próximos 30 dias
    forecasting_prompt = """
    Com base na análise de tendências dos dados históricos, faça uma previsão de vendas para os próximos 30 dias:
    
    Considere:
    1. Tendências identificadas
    2. Sazonalidade
    3. Padrões de fim de semana
    4. Possíveis eventos externos
    5. Intervalos de confiança
    
    Forneça previsões diárias e totais mensais.
    """

    forecast = agent.chat(forecasting_prompt, use_context=True)
    print(f"🔮 Previsão: {forecast}")

    # Recomendações estratégicas
    strategy_prompt = """
    Com base na análise e previsão, desenvolva recomendações estratégicas:
    
    1. Estratégias para maximizar vendas
    2. Gestão de estoque otimizada
    3. Campanhas de marketing direcionadas
    4. Preparação para sazonalidade
    5. KPIs para monitoramento
    """

    strategy = agent.chat(strategy_prompt, use_context=True)
    print(f"\n🎯 Estratégias: {strategy}")

    return {
        "data_points": len(sales_data),
        "trend_analysis": trend_analysis,
        "forecast": forecast,
        "strategy": strategy,
    }


def demo_customer_segmentation():
    """Demonstra segmentação de clientes"""
    print("\n👥 Segmentação de Clientes")
    print("=" * 40)

    agent = MangabaAgent(agent_id="customer_analyst")

    # Gera dados de clientes
    customer_data = DataGenerator.generate_customer_data(1000)

    print(f"👤 Analisando {len(customer_data)} clientes...")

    # Análise de segmentação
    segmentation_prompt = f"""
    Analise os seguintes dados de clientes para segmentação:
    
    Total de clientes: {len(customer_data)}
    
    Amostra dos dados:
    {json.dumps(customer_data[:10], indent=2)}
    
    Realize segmentação baseada em:
    1. Valor do cliente (CLV)
    2. Frequência de compra
    3. Valor médio do pedido
    4. Demografia (idade, renda)
    5. Comportamento de compra
    
    Identifique segmentos distintos e suas características.
    """

    segmentation = agent.chat(segmentation_prompt, use_context=True)
    print(f"🎯 Segmentação: {segmentation}")

    # Análise de valor do cliente
    clv_analysis_prompt = """
    Com base na segmentação, analise o valor vitalício do cliente (CLV):
    
    1. Calcule CLV por segmento
    2. Identifique clientes de alto valor
    3. Clientes em risco de churn
    4. Oportunidades de upsell/cross-sell
    5. Estratégias de retenção
    """

    clv_analysis = agent.chat(clv_analysis_prompt, use_context=True)
    print(f"💰 Análise CLV: {clv_analysis}")

    # Personalização de marketing
    personalization_prompt = """
    Desenvolva estratégias de marketing personalizadas para cada segmento:
    
    1. Mensagens personalizadas
    2. Canais de comunicação preferidos
    3. Ofertas e promoções direcionadas
    4. Timing de campanhas
    5. Métricas de sucesso
    """

    personalization = agent.chat(personalization_prompt, use_context=True)
    print(f"\n📧 Personalização: {personalization}")

    return {
        "customers_analyzed": len(customer_data),
        "segmentation": segmentation,
        "clv_analysis": clv_analysis,
        "personalization": personalization,
    }


def demo_product_analytics():
    """Demonstra análise de produtos"""
    print("\n📦 Análise de Produtos")
    print("=" * 40)

    agent = MangabaAgent(agent_id="product_analyst")

    # Gera dados de produtos
    product_data = DataGenerator.generate_product_data(100)

    print(f"🛍️ Analisando {len(product_data)} produtos...")

    # Análise de performance
    performance_prompt = f"""
    Analise a performance dos seguintes produtos:
    
    Total de produtos: {len(product_data)}
    
    Amostra dos dados:
    {json.dumps(product_data[:10], indent=2)}
    
    Analise:
    1. Produtos mais rentáveis
    2. Produtos com melhor giro
    3. Produtos com alta taxa de devolução
    4. Performance por categoria
    5. Oportunidades de otimização
    """

    performance = agent.chat(performance_prompt, use_context=True)
    print(f"📊 Performance: {performance}")

    # Análise de precificação
    pricing_prompt = """
    Com base na análise de performance, sugira estratégias de precificação:
    
    1. Produtos subprecificados
    2. Produtos com preço alto demais
    3. Oportunidades de bundling
    4. Precificação dinâmica
    5. Estratégias competitivas
    """

    pricing = agent.chat(pricing_prompt, use_context=True)
    print(f"💲 Precificação: {pricing}")

    # Recomendações de estoque
    inventory_prompt = """
    Desenvolva recomendações de gestão de estoque:
    
    1. Produtos para aumentar estoque
    2. Produtos para reduzir estoque
    3. Produtos descontinuar
    4. Novos produtos a introduzir
    5. Otimização de mix de produtos
    """

    inventory = agent.chat(inventory_prompt, use_context=True)
    print(f"\n📦 Gestão de Estoque: {inventory}")

    return {
        "products_analyzed": len(product_data),
        "performance": performance,
        "pricing": pricing,
        "inventory": inventory,
    }


def demo_predictive_maintenance():
    """Demonstra manutenção preditiva"""
    print("\n🔧 Manutenção Preditiva")
    print("=" * 40)

    agent = MangabaAgent(agent_id="maintenance_predictor")

    # Simula dados de equipamentos
    equipment_data = [
        {
            "equipment_id": "EQ001",
            "type": "Motor",
            "age_months": 36,
            "usage_hours": 8760,
            "temperature": 75.5,
            "vibration": 2.3,
            "last_maintenance": "2023-10-15",
            "failure_history": 2,
            "efficiency": 87.2,
        },
        {
            "equipment_id": "EQ002",
            "type": "Pump",
            "age_months": 18,
            "usage_hours": 4380,
            "temperature": 68.2,
            "vibration": 1.8,
            "last_maintenance": "2023-11-20",
            "failure_history": 0,
            "efficiency": 92.5,
        },
        {
            "equipment_id": "EQ003",
            "type": "Compressor",
            "age_months": 60,
            "usage_hours": 15000,
            "temperature": 82.1,
            "vibration": 3.1,
            "last_maintenance": "2023-08-10",
            "failure_history": 5,
            "efficiency": 78.9,
        },
    ]

    print(f"⚙️ Analisando {len(equipment_data)} equipamentos...")

    # Análise de condição
    condition_prompt = f"""
    Analise a condição dos seguintes equipamentos:
    
    {json.dumps(equipment_data, indent=2)}
    
    Para cada equipamento, avalie:
    1. Estado atual de saúde
    2. Indicadores de desgaste
    3. Risco de falha
    4. Eficiência operacional
    5. Necessidade de manutenção
    """

    condition_analysis = agent.chat(condition_prompt, use_context=True)
    print(f"🔍 Análise de Condição: {condition_analysis}")

    # Previsão de falhas
    failure_prediction_prompt = """
    Com base na análise de condição, preveja possíveis falhas:
    
    1. Probabilidade de falha nos próximos 30 dias
    2. Componentes mais propensos a falhar
    3. Impacto operacional de cada falha
    4. Janelas ideais para manutenção
    5. Custos de manutenção vs. substituição
    """

    failure_prediction = agent.chat(failure_prediction_prompt, use_context=True)
    print(f"⚠️ Previsão de Falhas: {failure_prediction}")

    # Plano de manutenção
    maintenance_plan_prompt = """
    Desenvolva um plano de manutenção otimizado:
    
    1. Cronograma de manutenções preventivas
    2. Priorização por criticidade
    3. Recursos necessários
    4. Peças de reposição
    5. Minimização de downtime
    """

    maintenance_plan = agent.chat(maintenance_plan_prompt, use_context=True)
    print(f"\n📅 Plano de Manutenção: {maintenance_plan}")

    return {
        "equipment_analyzed": len(equipment_data),
        "condition_analysis": condition_analysis,
        "failure_prediction": failure_prediction,
        "maintenance_plan": maintenance_plan,
    }


def demo_anomaly_detection():
    """Demonstra detecção de anomalias"""
    print("\n🚨 Detecção de Anomalias")
    print("=" * 40)

    agent = MangabaAgent(agent_id="anomaly_detector")

    # Simula dados de transações com anomalias
    transaction_data = []

    # Transações normais
    for i in range(100):
        transaction_data.append(
            {
                "transaction_id": f"TXN_{i:04d}",
                "amount": round(random.uniform(10, 500), 2),
                "timestamp": (
                    datetime.now() - timedelta(hours=random.randint(1, 168))
                ).isoformat(),
                "merchant": random.choice(
                    ["Store A", "Store B", "Store C", "Online Shop"]
                ),
                "location": random.choice(
                    ["São Paulo", "Rio de Janeiro", "Belo Horizonte"]
                ),
                "card_type": random.choice(["credit", "debit"]),
                "is_anomaly": False,
            }
        )

    # Adiciona algumas anomalias
    anomalies = [
        {
            "transaction_id": "TXN_ANOM1",
            "amount": 15000.00,  # Valor muito alto
            "timestamp": datetime.now().isoformat(),
            "merchant": "Unknown Merchant",
            "location": "International",
            "card_type": "credit",
            "is_anomaly": True,
        },
        {
            "transaction_id": "TXN_ANOM2",
            "amount": 0.01,  # Valor muito baixo
            "timestamp": (datetime.now() - timedelta(minutes=1)).isoformat(),
            "merchant": "Test Merchant",
            "location": "São Paulo",
            "card_type": "credit",
            "is_anomaly": True,
        },
    ]

    transaction_data.extend(anomalies)
    random.shuffle(transaction_data)

    print(f"💳 Analisando {len(transaction_data)} transações...")

    # Análise de padrões
    pattern_analysis_prompt = f"""
    Analise os seguintes dados de transações para identificar padrões e anomalias:
    
    Total de transações: {len(transaction_data)}
    
    Amostra dos dados:
    {json.dumps(transaction_data[:15], indent=2)}
    
    Identifique:
    1. Padrões normais de transação
    2. Transações suspeitas
    3. Indicadores de fraude
    4. Comportamentos anômalos
    5. Fatores de risco
    """

    pattern_analysis = agent.chat(pattern_analysis_prompt, use_context=True)
    print(f"🔍 Análise de Padrões: {pattern_analysis}")

    # Detecção de anomalias
    anomaly_detection_prompt = """
    Com base na análise de padrões, identifique anomalias específicas:
    
    1. Transações com valores atípicos
    2. Localizações suspeitas
    3. Horários incomuns
    4. Frequência anormal
    5. Score de risco para cada transação suspeita
    """

    anomaly_detection = agent.chat(anomaly_detection_prompt, use_context=True)
    print(f"🚨 Detecção de Anomalias: {anomaly_detection}")

    # Sistema de alertas
    alert_system_prompt = """
    Desenvolva um sistema de alertas para anomalias:
    
    1. Critérios para alertas automáticos
    2. Níveis de severidade
    3. Ações recomendadas para cada tipo
    4. Processo de investigação
    5. Prevenção de falsos positivos
    """

    alert_system = agent.chat(alert_system_prompt, use_context=True)
    print(f"\n📢 Sistema de Alertas: {alert_system}")

    return {
        "transactions_analyzed": len(transaction_data),
        "pattern_analysis": pattern_analysis,
        "anomaly_detection": anomaly_detection,
        "alert_system": alert_system,
    }


def demo_ml_model_evaluation():
    """Demonstra avaliação de modelos de ML"""
    print("\n🤖 Avaliação de Modelos de ML")
    print("=" * 40)

    agent = MangabaAgent(agent_id="ml_evaluator")

    # Simula resultados de diferentes modelos
    model_results = {
        "linear_regression": {
            "accuracy": 0.78,
            "precision": 0.75,
            "recall": 0.82,
            "f1_score": 0.78,
            "training_time": "2.3 minutes",
            "prediction_time": "0.1 seconds",
            "complexity": "low",
        },
        "random_forest": {
            "accuracy": 0.85,
            "precision": 0.83,
            "recall": 0.87,
            "f1_score": 0.85,
            "training_time": "8.7 minutes",
            "prediction_time": "0.3 seconds",
            "complexity": "medium",
        },
        "neural_network": {
            "accuracy": 0.91,
            "precision": 0.89,
            "recall": 0.93,
            "f1_score": 0.91,
            "training_time": "45.2 minutes",
            "prediction_time": "0.5 seconds",
            "complexity": "high",
        },
        "gradient_boosting": {
            "accuracy": 0.88,
            "precision": 0.86,
            "recall": 0.90,
            "f1_score": 0.88,
            "training_time": "15.1 minutes",
            "prediction_time": "0.2 seconds",
            "complexity": "medium-high",
        },
    }

    print(f"🔬 Avaliando {len(model_results)} modelos de ML...")

    # Comparação de modelos
    model_comparison_prompt = f"""
    Compare os seguintes modelos de machine learning:
    
    {json.dumps(model_results, indent=2)}
    
    Analise:
    1. Performance preditiva (accuracy, precision, recall, F1)
    2. Eficiência computacional
    3. Complexidade e interpretabilidade
    4. Trade-offs entre métricas
    5. Adequação para diferentes cenários
    """

    model_comparison = agent.chat(model_comparison_prompt, use_context=True)
    print(f"⚖️ Comparação de Modelos: {model_comparison}")

    # Recomendação de modelo
    recommendation_prompt = """
    Com base na comparação, recomende o melhor modelo para diferentes cenários:
    
    1. Produção com alta demanda (velocidade crítica)
    2. Análise exploratória (interpretabilidade importante)
    3. Máxima precisão (performance crítica)
    4. Recursos limitados (eficiência importante)
    5. Prototipagem rápida (simplicidade importante)
    """

    recommendation = agent.chat(recommendation_prompt, use_context=True)
    print(f"🎯 Recomendações: {recommendation}")

    # Estratégia de deployment
    deployment_prompt = """
    Desenvolva estratégias de deployment para os modelos:
    
    1. Arquitetura de produção
    2. Monitoramento de performance
    3. Estratégias de retreinamento
    4. A/B testing de modelos
    5. Rollback e contingência
    """

    deployment = agent.chat(deployment_prompt, use_context=True)
    print(f"\n🚀 Estratégia de Deployment: {deployment}")

    return {
        "models_evaluated": len(model_results),
        "model_comparison": model_comparison,
        "recommendation": recommendation,
        "deployment": deployment,
    }


def main():
    """Executa demonstração completa de ML e analytics"""
    print("🤖 Mangaba Agent - Machine Learning e Análise Preditiva")
    print("=" * 80)

    try:
        # Demonstrações de diferentes áreas de ML
        sales_result = demo_sales_forecasting()
        customer_result = demo_customer_segmentation()
        product_result = demo_product_analytics()
        maintenance_result = demo_predictive_maintenance()
        anomaly_result = demo_anomaly_detection()
        ml_result = demo_ml_model_evaluation()

        print("\n🎉 DEMONSTRAÇÃO DE ML E ANALYTICS COMPLETA!")
        print("=" * 70)

        print("\n📊 Resumo dos Resultados:")
        print(f"   📈 Dados de vendas analisados: {sales_result['data_points']} pontos")
        print(f"   👥 Clientes segmentados: {customer_result['customers_analyzed']}")
        print(f"   📦 Produtos analisados: {product_result['products_analyzed']}")
        print(
            f"   🔧 Equipamentos monitorados: {maintenance_result['equipment_analyzed']}"
        )
        print(
            f"   💳 Transações verificadas: {anomaly_result['transactions_analyzed']}"
        )
        print(f"   🤖 Modelos avaliados: {ml_result['models_evaluated']}")

        total_data_points = (
            sales_result["data_points"]
            + customer_result["customers_analyzed"]
            + product_result["products_analyzed"]
            + maintenance_result["equipment_analyzed"]
            + anomaly_result["transactions_analyzed"]
            + ml_result["models_evaluated"]
        )

        print("\n📈 Estatísticas Gerais:")
        print(f"   Total de pontos de dados analisados: {total_data_points}")
        print("   Áreas de aplicação: 6")
        print("   Modelos e análises geradas: 20+")
        print("   Insights preditivos: Múltiplos")

        print("\n🚀 Capacidades Demonstradas:")
        print("   • Previsão de vendas com sazonalidade")
        print("   • Segmentação inteligente de clientes")
        print("   • Análise de performance de produtos")
        print("   • Manutenção preditiva de equipamentos")
        print("   • Detecção de anomalias em tempo real")
        print("   • Avaliação e comparação de modelos ML")
        print("   • Geração de insights acionáveis")
        print("   • Estratégias baseadas em dados")
        print("   • Otimização de processos de negócio")
        print("   • Tomada de decisão orientada por IA")

    except Exception as e:
        print(f"❌ Erro durante demonstração de ML: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
