#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Administração com Mangaba Agent
Demonstra aplicações de IA em gestão empresarial, recursos humanos e operações
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba_agent import MangabaAgent
import json


class AdministrationDataGenerator:
    """Gerador de dados administrativos sintéticos"""

    @staticmethod
    def generate_employee_data():
        """Gera dados de funcionários"""
        employees = [
            {
                "employee_id": "EMP_001",
                "name": "Ana Silva",
                "position": "Gerente de Vendas",
                "department": "Comercial",
                "hire_date": "2020-03-15",
                "salary": 8500.00,
                "performance_score": 4.2,
                "skills": ["Liderança", "Negociação", "CRM", "Excel Avançado"],
                "certifications": ["MBA em Gestão", "Certificação em Vendas"],
                "training_hours": 45,
                "absences_last_year": 3,
                "overtime_hours": 25,
                "team_size": 8,
                "goals_achievement": 115,
                "customer_satisfaction": 4.5,
            },
            {
                "employee_id": "EMP_002",
                "name": "Carlos Santos",
                "position": "Analista de TI",
                "department": "Tecnologia",
                "hire_date": "2021-07-20",
                "salary": 6500.00,
                "performance_score": 4.0,
                "skills": ["Python", "SQL", "Cloud Computing", "DevOps"],
                "certifications": ["AWS Solutions Architect", "Scrum Master"],
                "training_hours": 60,
                "absences_last_year": 2,
                "overtime_hours": 40,
                "projects_completed": 12,
                "code_quality_score": 4.3,
                "innovation_contributions": 3,
            },
            {
                "employee_id": "EMP_003",
                "name": "Maria Oliveira",
                "position": "Coordenadora de RH",
                "department": "Recursos Humanos",
                "hire_date": "2019-01-10",
                "salary": 7200.00,
                "performance_score": 4.4,
                "skills": [
                    "Gestão de Pessoas",
                    "Recrutamento",
                    "Legislação Trabalhista",
                    "Psicologia Organizacional",
                ],
                "certifications": ["Especialização em RH", "Coach Profissional"],
                "training_hours": 38,
                "absences_last_year": 1,
                "overtime_hours": 15,
                "recruitment_success_rate": 85,
                "employee_satisfaction_score": 4.1,
                "retention_rate": 92,
            },
            {
                "employee_id": "EMP_004",
                "name": "João Costa",
                "position": "Assistente Administrativo",
                "department": "Administrativo",
                "hire_date": "2022-05-03",
                "salary": 3200.00,
                "performance_score": 3.8,
                "skills": [
                    "Excel",
                    "Atendimento ao Cliente",
                    "Organização",
                    "Comunicação",
                ],
                "certifications": ["Curso de Administração"],
                "training_hours": 25,
                "absences_last_year": 4,
                "overtime_hours": 10,
                "task_completion_rate": 95,
                "accuracy_score": 4.0,
                "customer_feedback": 4.2,
            },
        ]
        return employees

    @staticmethod
    def generate_project_data():
        """Gera dados de projetos"""
        projects = [
            {
                "project_id": "PROJ_001",
                "name": "Implementação CRM",
                "description": "Implementação de sistema CRM para melhorar gestão de clientes",
                "status": "Em andamento",
                "priority": "Alta",
                "start_date": "2024-09-01",
                "end_date": "2024-12-31",
                "budget": 150000.00,
                "spent": 85000.00,
                "progress": 65,
                "team_members": ["EMP_001", "EMP_002", "EMP_005"],
                "milestones": [
                    {
                        "name": "Análise de Requisitos",
                        "status": "Concluído",
                        "date": "2024-09-30",
                    },
                    {
                        "name": "Desenvolvimento",
                        "status": "Em andamento",
                        "date": "2024-11-30",
                    },
                    {"name": "Testes", "status": "Pendente", "date": "2024-12-15"},
                    {"name": "Go-live", "status": "Pendente", "date": "2024-12-31"},
                ],
                "risks": ["Atraso na integração", "Resistência dos usuários"],
                "stakeholders": ["Diretoria Comercial", "TI", "Usuários finais"],
            },
            {
                "project_id": "PROJ_002",
                "name": "Reestruturação Organizacional",
                "description": "Reorganização da estrutura departamental",
                "status": "Planejamento",
                "priority": "Média",
                "start_date": "2024-11-15",
                "end_date": "2025-03-31",
                "budget": 80000.00,
                "spent": 5000.00,
                "progress": 10,
                "team_members": ["EMP_003", "EMP_006"],
                "milestones": [
                    {
                        "name": "Diagnóstico Atual",
                        "status": "Em andamento",
                        "date": "2024-12-15",
                    },
                    {
                        "name": "Proposta Nova Estrutura",
                        "status": "Pendente",
                        "date": "2025-01-31",
                    },
                    {
                        "name": "Aprovação Diretoria",
                        "status": "Pendente",
                        "date": "2025-02-15",
                    },
                    {
                        "name": "Implementação",
                        "status": "Pendente",
                        "date": "2025-03-31",
                    },
                ],
                "risks": ["Resistência à mudança", "Impacto na produtividade"],
                "stakeholders": ["Diretoria", "Gerentes", "Todos os funcionários"],
            },
            {
                "project_id": "PROJ_003",
                "name": "Programa de Treinamento",
                "description": "Desenvolvimento de programa de capacitação",
                "status": "Concluído",
                "priority": "Baixa",
                "start_date": "2024-06-01",
                "end_date": "2024-10-31",
                "budget": 45000.00,
                "spent": 42000.00,
                "progress": 100,
                "team_members": ["EMP_003", "EMP_007"],
                "milestones": [
                    {
                        "name": "Levantamento de Necessidades",
                        "status": "Concluído",
                        "date": "2024-06-30",
                    },
                    {
                        "name": "Desenvolvimento Conteúdo",
                        "status": "Concluído",
                        "date": "2024-08-31",
                    },
                    {
                        "name": "Execução Treinamentos",
                        "status": "Concluído",
                        "date": "2024-10-15",
                    },
                    {
                        "name": "Avaliação Resultados",
                        "status": "Concluído",
                        "date": "2024-10-31",
                    },
                ],
                "risks": [],
                "stakeholders": ["RH", "Todos os departamentos"],
            },
        ]
        return projects

    @staticmethod
    def generate_operational_data():
        """Gera dados operacionais"""
        operations = {
            "departments": [
                {
                    "name": "Comercial",
                    "employees": 15,
                    "budget": 500000.00,
                    "revenue_target": 2000000.00,
                    "revenue_achieved": 1850000.00,
                    "efficiency_score": 4.1,
                    "customer_satisfaction": 4.3,
                    "key_metrics": {
                        "sales_conversion": 18.5,
                        "average_deal_size": 12500.00,
                        "customer_retention": 85.2,
                    },
                },
                {
                    "name": "Tecnologia",
                    "employees": 8,
                    "budget": 300000.00,
                    "projects_completed": 12,
                    "uptime_percentage": 99.2,
                    "efficiency_score": 4.4,
                    "innovation_index": 4.0,
                    "key_metrics": {
                        "bug_resolution_time": 2.5,
                        "deployment_frequency": 24,
                        "security_incidents": 0,
                    },
                },
                {
                    "name": "Recursos Humanos",
                    "employees": 4,
                    "budget": 150000.00,
                    "recruitment_success": 88,
                    "employee_satisfaction": 4.2,
                    "efficiency_score": 4.0,
                    "retention_rate": 92,
                    "key_metrics": {
                        "time_to_hire": 25,
                        "training_completion": 95,
                        "performance_reviews": 100,
                    },
                },
                {
                    "name": "Administrativo",
                    "employees": 6,
                    "budget": 120000.00,
                    "process_efficiency": 85,
                    "cost_reduction": 12,
                    "efficiency_score": 3.8,
                    "compliance_score": 98,
                    "key_metrics": {
                        "document_processing_time": 1.5,
                        "error_rate": 2.1,
                        "automation_level": 65,
                    },
                },
            ],
            "kpis": {
                "overall_productivity": 87.5,
                "employee_engagement": 4.1,
                "operational_efficiency": 82.3,
                "cost_per_employee": 4500.00,
                "revenue_per_employee": 125000.00,
                "absenteeism_rate": 3.2,
                "turnover_rate": 8.5,
            },
        }
        return operations


def demo_hr_management():
    """Demonstra gestão de recursos humanos"""
    print("👥 Gestão de Recursos Humanos")
    print("=" * 50)

    agent = MangabaAgent(agent_id="hr_manager")

    # Gera dados de funcionários
    employees = AdministrationDataGenerator.generate_employee_data()

    print(f"👤 Analisando {len(employees)} funcionários...")

    # Análise de performance
    performance_analysis_prompt = f"""
    Analise a performance dos funcionários:
    
    {json.dumps(employees, indent=2)}
    
    Para cada funcionário, avalie:
    1. Performance atual vs. expectativas
    2. Pontos fortes e áreas de melhoria
    3. Potencial de crescimento
    4. Necessidades de treinamento
    5. Adequação ao cargo atual
    6. Recomendações de desenvolvimento
    """

    performance_analysis = agent.chat(performance_analysis_prompt, use_context=True)
    print(f"📊 Análise de Performance: {performance_analysis}")

    # Planejamento de carreira
    career_planning_prompt = """
    Desenvolva planos de carreira personalizados:
    
    1. Trajetórias de crescimento possíveis
    2. Competências a desenvolver
    3. Cronograma de progressão
    4. Programas de mentoria
    5. Oportunidades internas
    6. Metas de desenvolvimento
    """

    career_planning = agent.chat(career_planning_prompt, use_context=True)
    print(f"🚀 Planejamento de Carreira: {career_planning}")

    # Gestão de talentos
    talent_management_prompt = """
    Implemente estratégias de gestão de talentos:
    
    1. Identificação de high performers
    2. Planos de retenção
    3. Sucessão de liderança
    4. Programas de reconhecimento
    5. Desenvolvimento de líderes
    6. Cultura organizacional
    """

    talent_management = agent.chat(talent_management_prompt, use_context=True)
    print(f"\n⭐ Gestão de Talentos: {talent_management}")

    return {
        "employees_analyzed": len(employees),
        "performance_analysis": performance_analysis,
        "career_planning": career_planning,
        "talent_management": talent_management,
    }


def demo_project_management():
    """Demonstra gestão de projetos"""
    print("\n📋 Gestão de Projetos")
    print("=" * 50)

    agent = MangabaAgent(agent_id="project_manager")

    # Gera dados de projetos
    projects = AdministrationDataGenerator.generate_project_data()

    print(f"📁 Gerenciando {len(projects)} projetos...")

    # Análise de status dos projetos
    project_status_prompt = f"""
    Analise o status dos projetos:
    
    {json.dumps(projects, indent=2)}
    
    Para cada projeto, avalie:
    1. Progresso vs. cronograma
    2. Orçamento vs. gastos
    3. Qualidade das entregas
    4. Riscos identificados
    5. Performance da equipe
    6. Ações corretivas necessárias
    """

    project_status = agent.chat(project_status_prompt, use_context=True)
    print(f"📊 Status dos Projetos: {project_status}")

    # Otimização de recursos
    resource_optimization_prompt = """
    Otimize a alocação de recursos:
    
    1. Distribuição de equipes
    2. Balanceamento de carga
    3. Identificação de gargalos
    4. Realocação de recursos
    5. Priorização de projetos
    6. Eficiência operacional
    """

    resource_optimization = agent.chat(resource_optimization_prompt, use_context=True)
    print(f"⚙️ Otimização de Recursos: {resource_optimization}")

    # Gestão de riscos
    risk_management_prompt = """
    Desenvolva estratégias de gestão de riscos:
    
    1. Identificação de novos riscos
    2. Avaliação de impacto e probabilidade
    3. Planos de mitigação
    4. Contingências
    5. Monitoramento contínuo
    6. Comunicação de riscos
    """

    risk_management = agent.chat(risk_management_prompt, use_context=True)
    print(f"⚠️ Gestão de Riscos: {risk_management}")

    # Metodologias ágeis
    agile_implementation_prompt = """
    Implemente metodologias ágeis:
    
    1. Adaptação do Scrum/Kanban
    2. Sprints e iterações
    3. Cerimônias ágeis
    4. Métricas de agilidade
    5. Melhoria contínua
    6. Cultura ágil
    """

    agile_implementation = agent.chat(agile_implementation_prompt, use_context=True)
    print(f"\n🔄 Implementação Ágil: {agile_implementation}")

    return {
        "projects_managed": len(projects),
        "project_status": project_status,
        "resource_optimization": resource_optimization,
        "risk_management": risk_management,
        "agile_implementation": agile_implementation,
    }


def demo_operational_efficiency():
    """Demonstra otimização de eficiência operacional"""
    print("\n⚙️ Eficiência Operacional")
    print("=" * 50)

    agent = MangabaAgent(agent_id="operations_optimizer")

    # Gera dados operacionais
    operations = AdministrationDataGenerator.generate_operational_data()

    print(f"🏢 Analisando {len(operations['departments'])} departamentos...")

    # Análise de eficiência
    efficiency_analysis_prompt = f"""
    Analise a eficiência operacional:
    
    {json.dumps(operations, indent=2)}
    
    Avalie:
    1. Performance por departamento
    2. Indicadores de produtividade
    3. Gargalos operacionais
    4. Oportunidades de melhoria
    5. Benchmarking interno
    6. ROI por área
    """

    efficiency_analysis = agent.chat(efficiency_analysis_prompt, use_context=True)
    print(f"📈 Análise de Eficiência: {efficiency_analysis}")

    # Automação de processos
    process_automation_prompt = """
    Identifique oportunidades de automação:
    
    1. Processos manuais repetitivos
    2. Tecnologias aplicáveis
    3. ROI da automação
    4. Cronograma de implementação
    5. Impacto nos funcionários
    6. Métricas de sucesso
    """

    process_automation = agent.chat(process_automation_prompt, use_context=True)
    print(f"🤖 Automação de Processos: {process_automation}")

    # Melhoria contínua
    continuous_improvement_prompt = """
    Implemente programa de melhoria contínua:
    
    1. Metodologia Lean/Six Sigma
    2. Identificação de desperdícios
    3. Padronização de processos
    4. Cultura de melhoria
    5. Indicadores de performance
    6. Ciclos de melhoria
    """

    continuous_improvement = agent.chat(continuous_improvement_prompt, use_context=True)
    print(f"🔄 Melhoria Contínua: {continuous_improvement}")

    # Dashboard executivo
    executive_dashboard_prompt = """
    Crie dashboard executivo:
    
    1. KPIs principais
    2. Visualizações interativas
    3. Alertas automáticos
    4. Relatórios personalizados
    5. Análise de tendências
    6. Suporte à decisão
    """

    executive_dashboard = agent.chat(executive_dashboard_prompt, use_context=True)
    print(f"\n📊 Dashboard Executivo: {executive_dashboard}")

    return {
        "departments_analyzed": len(operations["departments"]),
        "efficiency_analysis": efficiency_analysis,
        "process_automation": process_automation,
        "continuous_improvement": continuous_improvement,
        "executive_dashboard": executive_dashboard,
    }


def demo_strategic_planning():
    """Demonstra planejamento estratégico"""
    print("\n🎯 Planejamento Estratégico")
    print("=" * 50)

    agent = MangabaAgent(agent_id="strategic_planner")

    # Simula dados estratégicos
    strategic_data = {
        "company_overview": {
            "revenue_current": 5000000.00,
            "revenue_target": 7500000.00,
            "employees": 45,
            "market_share": 12.5,
            "growth_rate": 15.2,
            "profit_margin": 18.5,
        },
        "swot_analysis": {
            "strengths": [
                "Equipe qualificada",
                "Tecnologia avançada",
                "Relacionamento com clientes",
            ],
            "weaknesses": [
                "Processos manuais",
                "Dependência de poucos clientes",
                "Capacidade limitada",
            ],
            "opportunities": [
                "Expansão geográfica",
                "Novos produtos",
                "Parcerias estratégicas",
            ],
            "threats": [
                "Concorrência acirrada",
                "Mudanças regulatórias",
                "Crise econômica",
            ],
        },
        "strategic_objectives": [
            {
                "objective": "Aumentar receita em 50%",
                "timeline": "2 anos",
                "owner": "Diretoria Comercial",
            },
            {
                "objective": "Expandir para 3 novos mercados",
                "timeline": "18 meses",
                "owner": "Diretoria Geral",
            },
            {
                "objective": "Automatizar 70% dos processos",
                "timeline": "1 ano",
                "owner": "Diretoria de TI",
            },
            {
                "objective": "Reduzir turnover para 5%",
                "timeline": "1 ano",
                "owner": "Diretoria de RH",
            },
        ],
    }

    print("🎯 Desenvolvendo planejamento estratégico...")

    # Análise estratégica
    strategic_analysis_prompt = f"""
    Realize análise estratégica completa:
    
    {json.dumps(strategic_data, indent=2)}
    
    Analise:
    1. Posicionamento competitivo
    2. Viabilidade dos objetivos
    3. Recursos necessários
    4. Riscos estratégicos
    5. Sinergias entre objetivos
    6. Cronograma de execução
    """

    strategic_analysis = agent.chat(strategic_analysis_prompt, use_context=True)
    print(f"🔍 Análise Estratégica: {strategic_analysis}")

    # Plano de ação
    action_plan_prompt = """
    Desenvolva plano de ação detalhado:
    
    1. Iniciativas estratégicas
    2. Marcos e entregas
    3. Responsabilidades
    4. Orçamento necessário
    5. Métricas de acompanhamento
    6. Revisões periódicas
    """

    action_plan = agent.chat(action_plan_prompt, use_context=True)
    print(f"📋 Plano de Ação: {action_plan}")

    # Balanced Scorecard
    balanced_scorecard_prompt = """
    Crie Balanced Scorecard:
    
    1. Perspectiva Financeira
    2. Perspectiva do Cliente
    3. Perspectiva dos Processos Internos
    4. Perspectiva de Aprendizado e Crescimento
    5. Indicadores por perspectiva
    6. Metas e iniciativas
    """

    balanced_scorecard = agent.chat(balanced_scorecard_prompt, use_context=True)
    print(f"\n⚖️ Balanced Scorecard: {balanced_scorecard}")

    return {
        "strategic_objectives": len(strategic_data["strategic_objectives"]),
        "strategic_analysis": strategic_analysis,
        "action_plan": action_plan,
        "balanced_scorecard": balanced_scorecard,
    }


def demo_change_management():
    """Demonstra gestão de mudanças"""
    print("\n🔄 Gestão de Mudanças")
    print("=" * 50)

    agent = MangabaAgent(agent_id="change_manager")

    # Simula cenário de mudança
    change_scenario = {
        "change_type": "Transformação Digital",
        "scope": "Toda a organização",
        "timeline": "12 meses",
        "budget": 500000.00,
        "affected_employees": 45,
        "key_changes": [
            "Implementação de ERP",
            "Automação de processos",
            "Trabalho remoto híbrido",
            "Nova estrutura organizacional",
        ],
        "stakeholders": [
            {"group": "Diretoria", "influence": "Alto", "support": "Alto"},
            {"group": "Gerentes", "influence": "Médio", "support": "Médio"},
            {"group": "Funcionários", "influence": "Baixo", "support": "Baixo"},
            {"group": "Clientes", "influence": "Médio", "support": "Neutro"},
        ],
        "resistance_factors": [
            "Medo do desconhecido",
            "Perda de controle",
            "Sobrecarga de trabalho",
            "Falta de habilidades",
        ],
    }

    print("🔄 Planejando gestão de mudanças...")

    # Análise de impacto
    impact_analysis_prompt = f"""
    Analise o impacto da mudança:
    
    {json.dumps(change_scenario, indent=2)}
    
    Avalie:
    1. Impacto por stakeholder
    2. Riscos de resistência
    3. Benefícios esperados
    4. Recursos necessários
    5. Cronograma de implementação
    6. Fatores críticos de sucesso
    """

    impact_analysis = agent.chat(impact_analysis_prompt, use_context=True)
    print(f"📊 Análise de Impacto: {impact_analysis}")

    # Estratégia de comunicação
    communication_strategy_prompt = """
    Desenvolva estratégia de comunicação:
    
    1. Mensagens-chave por audiência
    2. Canais de comunicação
    3. Cronograma de comunicação
    4. Feedback e escuta ativa
    5. Gestão de rumores
    6. Celebração de marcos
    """

    communication_strategy = agent.chat(communication_strategy_prompt, use_context=True)
    print(f"📢 Estratégia de Comunicação: {communication_strategy}")

    # Plano de capacitação
    training_plan_prompt = """
    Crie plano de capacitação:
    
    1. Levantamento de gaps de competência
    2. Programas de treinamento
    3. Metodologias de ensino
    4. Cronograma de capacitação
    5. Avaliação de eficácia
    6. Suporte pós-treinamento
    """

    training_plan = agent.chat(training_plan_prompt, use_context=True)
    print(f"🎓 Plano de Capacitação: {training_plan}")

    # Monitoramento da mudança
    change_monitoring_prompt = """
    Implemente monitoramento da mudança:
    
    1. Indicadores de adoção
    2. Métricas de resistência
    3. Feedback contínuo
    4. Ajustes necessários
    5. Sustentabilidade da mudança
    6. Lições aprendidas
    """

    change_monitoring = agent.chat(change_monitoring_prompt, use_context=True)
    print(f"\n📈 Monitoramento da Mudança: {change_monitoring}")

    return {
        "stakeholder_groups": len(change_scenario["stakeholders"]),
        "impact_analysis": impact_analysis,
        "communication_strategy": communication_strategy,
        "training_plan": training_plan,
        "change_monitoring": change_monitoring,
    }


def main():
    """Executa demonstração completa de soluções administrativas"""
    print("🏢 Mangaba Agent - Soluções Administrativas")
    print("=" * 80)

    try:
        # Demonstrações de diferentes áreas administrativas
        hr_result = demo_hr_management()
        project_result = demo_project_management()
        operations_result = demo_operational_efficiency()
        strategic_result = demo_strategic_planning()
        change_result = demo_change_management()

        print("\n🎉 DEMONSTRAÇÃO ADMINISTRATIVA COMPLETA!")
        print("=" * 70)

        print("\n📊 Resumo dos Resultados:")
        print(f"   👥 Funcionários analisados: {hr_result['employees_analyzed']}")
        print(f"   📋 Projetos gerenciados: {project_result['projects_managed']}")
        print(
            f"   🏢 Departamentos analisados: {operations_result['departments_analyzed']}"
        )
        print(
            f"   🎯 Objetivos estratégicos: {strategic_result['strategic_objectives']}"
        )
        print(f"   🔄 Grupos de stakeholders: {change_result['stakeholder_groups']}")

        print("\n🏢 Capacidades Demonstradas:")
        print("   • Gestão de recursos humanos")
        print("   • Análise de performance de funcionários")
        print("   • Planejamento de carreira")
        print("   • Gestão de talentos")
        print("   • Gerenciamento de projetos")
        print("   • Otimização de recursos")
        print("   • Gestão de riscos")
        print("   • Metodologias ágeis")
        print("   • Eficiência operacional")
        print("   • Automação de processos")
        print("   • Melhoria contínua")
        print("   • Dashboard executivo")
        print("   • Planejamento estratégico")
        print("   • Balanced Scorecard")
        print("   • Gestão de mudanças")
        print("   • Análise de stakeholders")

    except Exception as e:
        print(f"❌ Erro durante demonstração administrativa: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
