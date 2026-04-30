import asyncio
import argparse
from logger import AgentLogger
from agents import Orchestrator, ResearchAgent, MarketSignalAgent, AnalystAgent, CritiqueAgent, ReportGenerator

async def run_parallel_phase(research_agent, market_agent, query, security_flags):
    # Phase 2: Parallel dispatch
    # Using asyncio.to_thread because our mock agents currently use synchronous OpenAI calls
    # In a fully async app, we would use AsyncOpenAI
    research_task = asyncio.to_thread(research_agent.retrieve, query, security_flags)
    market_task = asyncio.to_thread(market_agent.gather, query)
    
    evidence, market_data = await asyncio.gather(research_task, market_task)
    return evidence, market_data

async def main(query: str):
    print(f"Starting analysis for query: {query}")
    logger = AgentLogger(output_dir="sample_run")
    security_flags = []
    
    # Initialize agents
    orchestrator = Orchestrator(logger)
    research_agent = ResearchAgent(logger, corpus_dir="../nexara_multiagent_starter")
    market_agent = MarketSignalAgent(logger)
    analyst_agent = AnalystAgent(logger)
    critique_agent = CritiqueAgent(logger)
    
    # Phase 1: Decompose
    print("Phase 1: Decomposing query...")
    sub_tasks = orchestrator.decompose(query)
    
    # Phase 2: Parallel dispatch
    print("Phase 2: Gathering research and market data in parallel...")
    evidence, market_data = await run_parallel_phase(research_agent, market_agent, query, security_flags)
    
    # Phase 3: Synthesize
    print("Phase 3: Synthesizing data...")
    analysis = analyst_agent.synthesize(evidence, market_data)
    
    if not analysis:
        print("\n❌ Error: Synthesis failed. This is usually due to an invalid OpenAI API Key.")
        print("Please check your .env file and ensure OPENAI_API_KEY is set correctly.")
        return

    # Phase 4: Critique
    print("Phase 4: Critiquing analysis...")
    critique = critique_agent.critique(analysis)
    
    # Phase 5a: Conditional retry
    if critique and critique.verdict.lower() == "fail" and critique.overall_score < 3.0:
        print("Critique failed. Retrying synthesis (Phase 5a)...")
        analysis = analyst_agent.synthesize(evidence, market_data, critique_notes=critique.notes)
        # Recritique after retry to ensure trace completeness
        critique = critique_agent.critique(analysis)
        
    # Phase 5b: Report
    print("Phase 5b: Generating report...")
    report = ReportGenerator(query, analysis, critique, evidence, logger, security_flags)
    
    print("Analysis complete. Reports saved to sample_run/ directory.")
    print(f"Security Flags Detected: {len(security_flags)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexara Labs Multi-Agent SIB Generator")
    parser.add_argument("--query", type=str, nargs='?', help="The analyst query to process")
    args = parser.parse_args()
    
    query = args.query
    if not query:
        print("\nNexara Labs - Multi-Agent Strategic Intelligence Platform")
        print("-" * 55)
        query = input("Enter your query: ")
        
    if query.strip():
        asyncio.run(main(query))
    else:
        print("Query cannot be empty.")
