#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Direito com Mangaba Agent
Demonstra aplicações de IA em análise jurídica, contratos e compliance
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba_agent import MangabaAgent
import json


class LegalDataGenerator:
    """Gerador de dados jurídicos sintéticos"""

    @staticmethod
    def generate_contract_data():
        """Gera dados de contratos para análise"""
        contracts = [
            {
                "contract_id": "CONT_001",
                "type": "Contrato de Prestação de Serviços",
                "parties": ["Empresa ABC Ltda.", "Fornecedor XYZ S.A."],
                "value": 150000.00,
                "duration": "12 meses",
                "start_date": "2024-01-15",
                "end_date": "2025-01-14",
                "key_clauses": [
                    "Cláusula de confidencialidade",
                    "Penalidades por atraso",
                    "Rescisão antecipada",
                    "Foro de eleição",
                ],
                "risk_level": "Médio",
                "compliance_status": "Conforme",
                "renewal_option": True,
                "governing_law": "Lei Brasileira",
            },
            {
                "contract_id": "CONT_002",
                "type": "Contrato de Compra e Venda",
                "parties": ["Comprador DEF Ltda.", "Vendedor GHI S.A."],
                "value": 500000.00,
                "duration": "Execução única",
                "start_date": "2024-03-01",
                "delivery_date": "2024-04-30",
                "key_clauses": [
                    "Garantia de qualidade",
                    "Condições de pagamento",
                    "Transferência de propriedade",
                    "Vícios redibitórios",
                ],
                "risk_level": "Alto",
                "compliance_status": "Pendente revisão",
                "warranty_period": "24 meses",
                "governing_law": "Lei Brasileira",
            },
            {
                "contract_id": "CONT_003",
                "type": "Contrato de Trabalho",
                "parties": ["Empresa JKL Ltda.", "Funcionário MNO"],
                "salary": 8500.00,
                "position": "Gerente de Vendas",
                "start_date": "2024-02-01",
                "probation_period": "90 dias",
                "key_clauses": [
                    "Jornada de trabalho",
                    "Benefícios",
                    "Cláusula de não-concorrência",
                    "Confidencialidade",
                ],
                "risk_level": "Baixo",
                "compliance_status": "Conforme CLT",
                "benefits": ["Vale refeição", "Plano de saúde", "Vale transporte"],
                "governing_law": "CLT",
            },
        ]
        return contracts

    @staticmethod
    def generate_litigation_data():
        """Gera dados de processos judiciais"""
        cases = [
            {
                "case_id": "PROC_001",
                "case_number": "1234567-89.2024.8.26.0100",
                "court": "1ª Vara Cível - SP",
                "case_type": "Ação de Cobrança",
                "plaintiff": "Empresa ABC Ltda.",
                "defendant": "Cliente Inadimplente XYZ",
                "claim_value": 75000.00,
                "filing_date": "2024-01-10",
                "status": "Em andamento",
                "last_update": "2024-11-15",
                "next_hearing": "2024-12-20",
                "lawyer": "Dr. João Silva - OAB/SP 123456",
                "probability_success": 85,
                "estimated_duration": "8-12 meses",
                "key_documents": ["Contrato", "Notas fiscais", "Correspondências"],
            },
            {
                "case_id": "PROC_002",
                "case_number": "9876543-21.2024.5.02.0001",
                "court": "2ª Vara do Trabalho - SP",
                "case_type": "Reclamação Trabalhista",
                "plaintiff": "Ex-funcionário DEF",
                "defendant": "Empresa GHI Ltda.",
                "claim_value": 45000.00,
                "filing_date": "2024-02-15",
                "status": "Aguardando perícia",
                "last_update": "2024-11-10",
                "next_hearing": "2024-12-15",
                "lawyer": "Dra. Maria Santos - OAB/SP 654321",
                "probability_success": 60,
                "estimated_duration": "6-10 meses",
                "key_documents": ["CTPS", "Holerites", "Testemunhas"],
            },
            {
                "case_id": "PROC_003",
                "case_number": "5555666-77.2024.4.03.6100",
                "court": "Justiça Federal - SP",
                "case_type": "Mandado de Segurança",
                "plaintiff": "Empresa JKL S.A.",
                "defendant": "Receita Federal",
                "claim_value": 200000.00,
                "filing_date": "2024-03-20",
                "status": "Liminar deferida",
                "last_update": "2024-11-20",
                "next_hearing": "2024-12-30",
                "lawyer": "Dr. Carlos Oliveira - OAB/SP 789012",
                "probability_success": 75,
                "estimated_duration": "12-18 meses",
                "key_documents": ["Auto de infração", "Defesa", "Jurisprudência"],
            },
        ]
        return cases

    @staticmethod
    def generate_compliance_data():
        """Gera dados de compliance"""
        compliance_areas = [
            {
                "area": "LGPD - Lei Geral de Proteção de Dados",
                "compliance_score": 85,
                "last_audit": "2024-06-15",
                "next_audit": "2024-12-15",
                "requirements": [
                    "Mapeamento de dados pessoais",
                    "Política de privacidade atualizada",
                    "Treinamento de funcionários",
                    "DPO nomeado",
                    "Procedimentos de resposta a incidentes",
                ],
                "gaps": ["Auditoria de fornecedores", "Testes de segurança"],
                "risk_level": "Baixo",
                "action_plan": "Implementar auditoria trimestral",
            },
            {
                "area": "Lei Anticorrupção (Lei 12.846/2013)",
                "compliance_score": 92,
                "last_audit": "2024-08-10",
                "next_audit": "2025-02-10",
                "requirements": [
                    "Código de conduta",
                    "Canal de denúncias",
                    "Due diligence de terceiros",
                    "Treinamentos periódicos",
                    "Monitoramento contínuo",
                ],
                "gaps": ["Atualização de políticas"],
                "risk_level": "Muito Baixo",
                "action_plan": "Revisão anual de políticas",
            },
            {
                "area": "Direito do Consumidor (CDC)",
                "compliance_score": 78,
                "last_audit": "2024-05-20",
                "next_audit": "2024-11-20",
                "requirements": [
                    "SAC estruturado",
                    "Política de trocas e devoluções",
                    "Informações claras sobre produtos",
                    "Contratos em linguagem simples",
                    "Respeito ao direito de arrependimento",
                ],
                "gaps": ["Melhoria no atendimento", "Revisão de contratos"],
                "risk_level": "Médio",
                "action_plan": "Treinamento da equipe de atendimento",
            },
        ]
        return compliance_areas


def demo_contract_analysis():
    """Demonstra análise de contratos"""
    print("📋 Análise de Contratos")
    print("=" * 50)

    agent = MangabaAgent(agent_id="contract_analyst")

    # Gera dados de contratos
    contracts = LegalDataGenerator.generate_contract_data()

    print(f"📄 Analisando {len(contracts)} contratos...")

    # Análise de riscos contratuais
    risk_analysis_prompt = f"""
    Analise os riscos dos seguintes contratos:
    
    {json.dumps(contracts, indent=2)}
    
    Para cada contrato, identifique:
    1. Principais riscos jurídicos
    2. Cláusulas problemáticas ou ausentes
    3. Nível de exposição financeira
    4. Recomendações de mitigação
    5. Necessidade de revisão ou renegociação
    """

    risk_analysis = agent.chat(risk_analysis_prompt, use_context=True)
    print(f"⚠️ Análise de Riscos: {risk_analysis}")

    # Revisão de cláusulas
    clause_review_prompt = """
    Revise as cláusulas contratuais e sugira melhorias:
    
    1. Cláusulas de força maior e caso fortuito
    2. Penalidades e multas
    3. Condições de rescisão
    4. Foro e lei aplicável
    5. Garantias e responsabilidades
    6. Confidencialidade e propriedade intelectual
    """

    clause_review = agent.chat(clause_review_prompt, use_context=True)
    print(f"📝 Revisão de Cláusulas: {clause_review}")

    # Compliance contratual
    compliance_check_prompt = """
    Verifique a conformidade dos contratos com:
    
    1. Legislação aplicável
    2. Normas regulamentares
    3. Boas práticas do setor
    4. Jurisprudência relevante
    5. Políticas internas da empresa
    """

    compliance_check = agent.chat(compliance_check_prompt, use_context=True)
    print(f"\n✅ Verificação de Compliance: {compliance_check}")

    return {
        "contracts_analyzed": len(contracts),
        "risk_analysis": risk_analysis,
        "clause_review": clause_review,
        "compliance_check": compliance_check,
    }


def demo_litigation_management():
    """Demonstra gestão de processos judiciais"""
    print("\n⚖️ Gestão de Processos Judiciais")
    print("=" * 50)

    agent = MangabaAgent(agent_id="litigation_manager")

    # Gera dados de processos
    cases = LegalDataGenerator.generate_litigation_data()

    print(f"📁 Gerenciando {len(cases)} processos...")

    # Análise de probabilidade de sucesso
    success_analysis_prompt = f"""
    Analise a probabilidade de sucesso dos processos:
    
    {json.dumps(cases, indent=2)}
    
    Para cada processo, avalie:
    1. Fundamentos jurídicos
    2. Qualidade das provas
    3. Jurisprudência aplicável
    4. Histórico do juízo
    5. Estratégia processual recomendada
    """

    success_analysis = agent.chat(success_analysis_prompt, use_context=True)
    print(f"🎯 Análise de Probabilidade: {success_analysis}")

    # Estratégia processual
    strategy_prompt = """
    Desenvolva estratégias processuais otimizadas:
    
    1. Linha de defesa/ataque principal
    2. Argumentos subsidiários
    3. Provas a serem produzidas
    4. Recursos cabíveis
    5. Possibilidades de acordo
    6. Cronograma de ações
    """

    strategy = agent.chat(strategy_prompt, use_context=True)
    print(f"📋 Estratégia Processual: {strategy}")

    # Gestão de prazos
    deadline_management_prompt = """
    Crie um sistema de gestão de prazos:
    
    1. Prazos críticos identificados
    2. Sistema de alertas
    3. Distribuição de responsabilidades
    4. Backup de advogados
    5. Controle de qualidade
    """

    deadline_management = agent.chat(deadline_management_prompt, use_context=True)
    print(f"⏰ Gestão de Prazos: {deadline_management}")

    # Análise de custos
    cost_analysis_prompt = """
    Analise os custos processuais:
    
    1. Honorários advocatícios
    2. Custas judiciais
    3. Perícias e diligências
    4. Provisões contábeis
    5. Análise custo-benefício
    """

    cost_analysis = agent.chat(cost_analysis_prompt, use_context=True)
    print(f"\n💰 Análise de Custos: {cost_analysis}")

    return {
        "cases_managed": len(cases),
        "success_analysis": success_analysis,
        "strategy": strategy,
        "deadline_management": deadline_management,
        "cost_analysis": cost_analysis,
    }


def demo_compliance_monitoring():
    """Demonstra monitoramento de compliance"""
    print("\n🛡️ Monitoramento de Compliance")
    print("=" * 50)

    agent = MangabaAgent(agent_id="compliance_officer")

    # Gera dados de compliance
    compliance_areas = LegalDataGenerator.generate_compliance_data()

    print(f"📊 Monitorando {len(compliance_areas)} áreas de compliance...")

    # Avaliação de riscos de compliance
    compliance_assessment_prompt = f"""
    Avalie o status de compliance nas seguintes áreas:
    
    {json.dumps(compliance_areas, indent=2)}
    
    Para cada área, analise:
    1. Nível atual de conformidade
    2. Gaps identificados
    3. Riscos de não conformidade
    4. Impacto potencial de violações
    5. Prioridades de ação
    """

    compliance_assessment = agent.chat(compliance_assessment_prompt, use_context=True)
    print(f"📋 Avaliação de Compliance: {compliance_assessment}")

    # Plano de ação
    action_plan_prompt = """
    Desenvolva um plano de ação para compliance:
    
    1. Ações corretivas imediatas
    2. Melhorias de médio prazo
    3. Investimentos necessários
    4. Cronograma de implementação
    5. Métricas de acompanhamento
    6. Responsáveis por cada ação
    """

    action_plan = agent.chat(action_plan_prompt, use_context=True)
    print(f"📅 Plano de Ação: {action_plan}")

    # Treinamento e conscientização
    training_program_prompt = """
    Crie um programa de treinamento em compliance:
    
    1. Público-alvo por área
    2. Conteúdo programático
    3. Metodologia de ensino
    4. Avaliação de eficácia
    5. Cronograma de treinamentos
    6. Certificações necessárias
    """

    training_program = agent.chat(training_program_prompt, use_context=True)
    print(f"🎓 Programa de Treinamento: {training_program}")

    # Monitoramento contínuo
    monitoring_system_prompt = """
    Implemente um sistema de monitoramento contínuo:
    
    1. KPIs de compliance
    2. Dashboards executivos
    3. Alertas automáticos
    4. Auditorias internas
    5. Relatórios periódicos
    6. Integração com sistemas existentes
    """

    monitoring_system = agent.chat(monitoring_system_prompt, use_context=True)
    print(f"\n📊 Sistema de Monitoramento: {monitoring_system}")

    return {
        "compliance_areas": len(compliance_areas),
        "compliance_assessment": compliance_assessment,
        "action_plan": action_plan,
        "training_program": training_program,
        "monitoring_system": monitoring_system,
    }


def demo_legal_research():
    """Demonstra pesquisa jurídica"""
    print("\n🔍 Pesquisa Jurídica")
    print("=" * 50)

    agent = MangabaAgent(agent_id="legal_researcher")

    # Simula temas de pesquisa
    research_topics = [
        {
            "topic": "Responsabilidade Civil por Danos Ambientais",
            "context": "Empresa de mineração com vazamento de rejeitos",
            "urgency": "Alta",
            "scope": "Jurisprudência STJ e STF",
        },
        {
            "topic": "Marco Civil da Internet - Responsabilidade de Provedores",
            "context": "Plataforma digital com conteúdo ofensivo",
            "urgency": "Média",
            "scope": "Doutrina e decisões recentes",
        },
        {
            "topic": "Lei de Recuperação Judicial - Sucessão de Empresas",
            "context": "Aquisição de empresa em recuperação",
            "urgency": "Alta",
            "scope": "Precedentes e súmulas",
        },
    ]

    print(f"📚 Pesquisando {len(research_topics)} temas jurídicos...")

    # Pesquisa jurisprudencial
    jurisprudence_research_prompt = f"""
    Realize pesquisa jurisprudencial sobre os seguintes temas:
    
    {json.dumps(research_topics, indent=2)}
    
    Para cada tema, forneça:
    1. Principais precedentes
    2. Tendências jurisprudenciais
    3. Divergências entre tribunais
    4. Súmulas aplicáveis
    5. Teses em repercussão geral
    """

    jurisprudence_research = agent.chat(jurisprudence_research_prompt, use_context=True)
    print(f"⚖️ Pesquisa Jurisprudencial: {jurisprudence_research}")

    # Análise doutrinária
    doctrine_analysis_prompt = """
    Analise a doutrina sobre os temas pesquisados:
    
    1. Principais autores e obras
    2. Correntes doutrinárias
    3. Debates acadêmicos atuais
    4. Propostas de reforma legislativa
    5. Direito comparado
    """

    doctrine_analysis = agent.chat(doctrine_analysis_prompt, use_context=True)
    print(f"📖 Análise Doutrinária: {doctrine_analysis}")

    # Monitoramento legislativo
    legislative_monitoring_prompt = """
    Monitore mudanças legislativas relevantes:
    
    1. Projetos de lei em tramitação
    2. Regulamentações em consulta pública
    3. Medidas provisórias
    4. Resoluções de órgãos reguladores
    5. Impacto nas práticas empresariais
    """

    legislative_monitoring = agent.chat(legislative_monitoring_prompt, use_context=True)
    print(f"\n🏛️ Monitoramento Legislativo: {legislative_monitoring}")

    return {
        "research_topics": len(research_topics),
        "jurisprudence_research": jurisprudence_research,
        "doctrine_analysis": doctrine_analysis,
        "legislative_monitoring": legislative_monitoring,
    }


def demo_document_automation():
    """Demonstra automação de documentos jurídicos"""
    print("\n📄 Automação de Documentos Jurídicos")
    print("=" * 50)

    agent = MangabaAgent(agent_id="document_automation")

    # Simula tipos de documentos
    document_types = [
        {
            "type": "Contrato de Prestação de Serviços",
            "complexity": "Média",
            "variables": ["Partes", "Objeto", "Valor", "Prazo", "Condições"],
            "clauses": 15,
            "review_time": "2 horas",
        },
        {
            "type": "Petição Inicial",
            "complexity": "Alta",
            "variables": ["Autor", "Réu", "Causa de Pedir", "Pedido", "Valor"],
            "sections": 8,
            "review_time": "4 horas",
        },
        {
            "type": "Parecer Jurídico",
            "complexity": "Alta",
            "variables": ["Consulente", "Questão", "Fundamentação", "Conclusão"],
            "pages": 12,
            "review_time": "6 horas",
        },
    ]

    print(f"🤖 Automatizando {len(document_types)} tipos de documentos...")

    # Análise de automação
    automation_analysis_prompt = f"""
    Analise as possibilidades de automação para os documentos:
    
    {json.dumps(document_types, indent=2)}
    
    Para cada tipo, avalie:
    1. Grau de padronização possível
    2. Variáveis que podem ser automatizadas
    3. Pontos que requerem revisão humana
    4. Economia de tempo estimada
    5. Riscos da automação
    """

    automation_analysis = agent.chat(automation_analysis_prompt, use_context=True)
    print(f"⚙️ Análise de Automação: {automation_analysis}")

    # Templates inteligentes
    smart_templates_prompt = """
    Desenvolva templates inteligentes:
    
    1. Estrutura modular de cláusulas
    2. Campos condicionais
    3. Validações automáticas
    4. Integração com bases de dados
    5. Versionamento de templates
    6. Controle de qualidade
    """

    smart_templates = agent.chat(smart_templates_prompt, use_context=True)
    print(f"📋 Templates Inteligentes: {smart_templates}")

    # Workflow de aprovação
    approval_workflow_prompt = """
    Crie workflows de aprovação de documentos:
    
    1. Níveis de aprovação por tipo
    2. Critérios de escalação
    3. Prazos de revisão
    4. Notificações automáticas
    5. Histórico de alterações
    6. Assinatura digital
    """

    approval_workflow = agent.chat(approval_workflow_prompt, use_context=True)
    print(f"\n✅ Workflow de Aprovação: {approval_workflow}")

    return {
        "document_types": len(document_types),
        "automation_analysis": automation_analysis,
        "smart_templates": smart_templates,
        "approval_workflow": approval_workflow,
    }


def main():
    """Executa demonstração completa de soluções jurídicas"""
    print("⚖️ Mangaba Agent - Soluções Jurídicas")
    print("=" * 80)

    try:
        # Demonstrações de diferentes áreas jurídicas
        contract_result = demo_contract_analysis()
        litigation_result = demo_litigation_management()
        compliance_result = demo_compliance_monitoring()
        research_result = demo_legal_research()
        automation_result = demo_document_automation()

        print("\n🎉 DEMONSTRAÇÃO JURÍDICA COMPLETA!")
        print("=" * 70)

        print("\n📊 Resumo dos Resultados:")
        print(f"   📋 Contratos analisados: {contract_result['contracts_analyzed']}")
        print(f"   ⚖️ Processos gerenciados: {litigation_result['cases_managed']}")
        print(f"   🛡️ Áreas de compliance: {compliance_result['compliance_areas']}")
        print(f"   🔍 Temas pesquisados: {research_result['research_topics']}")
        print(f"   📄 Tipos de documentos: {automation_result['document_types']}")

        print("\n⚖️ Capacidades Demonstradas:")
        print("   • Análise de riscos contratuais")
        print("   • Revisão de cláusulas e termos")
        print("   • Gestão de processos judiciais")
        print("   • Estratégia processual")
        print("   • Monitoramento de compliance")
        print("   • Avaliação de conformidade")
        print("   • Pesquisa jurisprudencial")
        print("   • Análise doutrinária")
        print("   • Monitoramento legislativo")
        print("   • Automação de documentos")
        print("   • Templates inteligentes")
        print("   • Workflows de aprovação")
        print("   • Due diligence automatizada")
        print("   • Gestão de prazos processuais")

    except Exception as e:
        print(f"❌ Erro durante demonstração jurídica: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
