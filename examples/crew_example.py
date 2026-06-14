#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de uso do Mangaba AI com Crew, Agents e Tasks
Demonstra orquestração de múltiplos agentes trabalhando em equipe.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangaba import Agent, Task, Crew, Process


def example_research_crew():
    """
    Exemplo: Crew de pesquisa com 3 agentes especializados
    """
    print("=" * 80)
    print("🔬 EXAMPLE: Research Crew - AI Trends Analysis")
    print("=" * 80)

    # 1. Definir Agentes Especializados
    researcher = Agent(
        role="Senior Research Analyst",
        goal="Uncover cutting-edge developments in artificial intelligence",
        backstory="""You are an expert AI researcher with 10+ years of experience.
        You excel at finding the most relevant and recent information about AI trends,
        breakthroughs, and industry developments. You have a keen eye for distinguishing
        hype from genuine innovation.""",
        verbose=True,
    )

    analyst = Agent(
        role="Data Analysis Expert",
        goal="Analyze research findings and extract key insights",
        backstory="""You are a data analyst specialized in AI and technology trends.
        You can identify patterns, correlations, and meaningful insights from research data.
        Your analytical skills help transform raw information into actionable intelligence.""",
        verbose=True,
    )

    writer = Agent(
        role="Technical Content Writer",
        goal="Create comprehensive and engaging reports",
        backstory="""You are a technical writer with expertise in AI and technology.
        You can take complex technical information and transform it into clear,
        well-structured reports that are both informative and accessible.""",
        verbose=True,
    )

    # 2. Definir Tasks
    research_task = Task(
        description="""Research the latest developments in {topic} for 2024-2025.
        Focus on:
        - Major breakthroughs and innovations
        - Key players and companies
        - Emerging trends and patterns
        - Potential impact on the industry
        
        Gather information from reliable sources and provide comprehensive findings.""",
        expected_output="""A detailed research summary with:
        - 10 key findings about {topic}
        - Sources and references
        - Timeline of major developments""",
        agent=researcher,
    )

    analysis_task = Task(
        description="""Analyze the research findings about {topic}.
        
        Focus on:
        - Identify the 3 most significant trends
        - Analyze potential business impacts
        - Find connections between different developments
        - Assess future implications
        
        Provide data-driven insights.""",
        expected_output="""An analytical report containing:
        - Top 3 trends with supporting evidence
        - Business impact assessment
        - Future outlook and predictions""",
        agent=analyst,
        context=[research_task],  # Depende da task de pesquisa
    )

    writing_task = Task(
        description="""Create a comprehensive report about {topic} based on the research and analysis.
        
        The report should:
        - Have a clear executive summary
        - Present findings in an organized manner
        - Include insights from the analysis
        - Conclude with actionable recommendations
        - Be professional and well-formatted
        
        Target audience: Tech executives and decision-makers.""",
        expected_output="""A complete report in markdown format with:
        - Executive Summary
        - Key Findings (from research)
        - Analysis & Insights
        - Recommendations
        - Conclusion""",
        agent=writer,
        context=[research_task, analysis_task],  # Depende de ambas
        output_file="ai_trends_report.md",
    )

    # 3. Criar Crew com processo Sequential
    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, writing_task],
        process=Process.SEQUENTIAL,
        verbose=True,
    )

    # 4. Executar o Crew
    print("\n🚀 Starting crew execution...\n")

    result = crew.kickoff(inputs={"topic": "Generative AI and Large Language Models"})

    print("\n" + "=" * 80)
    print("✅ CREW EXECUTION COMPLETED")
    print("=" * 80)
    print(f"\n📊 Duration: {result.duration:.2f} seconds")
    print(f"📝 Tasks completed: {len(result.tasks_outputs)}")
    print("\n📄 Final Report Preview:")
    print("-" * 80)
    print(result.final_output[:500] + "...")
    print("\n💾 Full report saved to: ai_trends_report.md")


def example_hierarchical_crew():
    """
    Exemplo: Crew hierárquico com gerente delegando tarefas
    """
    print("\n" + "=" * 80)
    print("👔 EXAMPLE: Hierarchical Crew - Product Launch Campaign")
    print("=" * 80)

    # 1. Definir Agentes (primeiro é o gerente)
    manager = Agent(
        role="Marketing Campaign Manager",
        goal="Coordinate and oversee successful product launch campaign",
        backstory="""You are an experienced marketing manager with a track record
        of successful product launches. You excel at coordinating teams, ensuring
        quality, and keeping projects on track.""",
        verbose=True,
        allow_delegation=True,
    )

    market_researcher = Agent(
        role="Market Research Specialist",
        goal="Understand target market and competition",
        backstory="""You specialize in market analysis and competitive intelligence.
        You can quickly identify market opportunities and threats.""",
        verbose=True,
    )

    copywriter = Agent(
        role="Creative Copywriter",
        goal="Create compelling marketing copy",
        backstory="""You are a creative copywriter who can craft messages that
        resonate with audiences and drive action.""",
        verbose=True,
    )

    # 2. Definir Tasks
    market_research = Task(
        description="""Research the market for {product}.
        Identify target audience, competitors, and market positioning opportunities.""",
        expected_output="""Market research report with target audience profile,
        competitor analysis, and recommended positioning strategy.""",
        agent=market_researcher,
    )

    copy_creation = Task(
        description="""Create marketing copy for {product} launch campaign.
        Include tagline, product description, and key messaging points.""",
        expected_output="""Complete marketing copy package with tagline,
        descriptions, and messaging framework.""",
        agent=copywriter,
        context=[market_research],
    )

    # 3. Criar Crew Hierárquico
    crew = Crew(
        agents=[manager, market_researcher, copywriter],  # Manager é o primeiro
        tasks=[market_research, copy_creation],
        process=Process.HIERARCHICAL,
        verbose=True,
    )

    # 4. Executar
    print("\n🚀 Starting hierarchical crew execution...\n")

    result = crew.kickoff(inputs={"product": "AI-Powered Project Management Tool"})

    print("\n" + "=" * 80)
    print("✅ HIERARCHICAL CREW COMPLETED")
    print("=" * 80)
    print(f"\n⏱️  Duration: {result.duration:.2f} seconds")
    print("\n📋 Final Output:")
    print("-" * 80)
    print(result.final_output)


def main():
    """Executa os exemplos"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                        🥭 MANGABA AI - CREW EXAMPLES                        ║
║                                                                              ║
║         Demonstração de orquestração de múltiplos agentes                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        # Exemplo 1: Crew Sequential
        example_research_crew()

        # Exemplo 2: Crew Hierarchical
        input("\n\nPress ENTER to continue to Hierarchical Crew example...")
        example_hierarchical_crew()

        print("\n" + "=" * 80)
        print("🎉 All examples completed successfully!")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
