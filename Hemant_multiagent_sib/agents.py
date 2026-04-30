import os
import json
import time
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel
from openai import OpenAI
import schemas
import tools
import security
from logger import AgentLogger
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "dummy-key-for-now"))

MODEL = "gpt-4o-mini" # Using gpt-4o-mini to be fast and cost effective

class SubTaskList(BaseModel):
    tasks: List[schemas.SubTask]

class EvidenceList(BaseModel):
    items: List[schemas.EvidenceItem]

def run_agent_call(logger: AgentLogger, agent_name: str, system_prompt: str, user_prompt: str, response_format=None, max_tokens=1000):
    start_time = time.time()
    error = None
    tool_calls = []
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        if response_format:
            response = client.beta.chat.completions.parse(
                model=MODEL,
                messages=messages,
                response_format=response_format,
                max_tokens=max_tokens
            )
            parsed_content = response.choices[0].message.parsed
        else:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=max_tokens
            )
            parsed_content = response.choices[0].message.content
            
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
    except Exception as e:
        error = str(e)
        print(f"\n⚠️ API Error in {agent_name}: {error}")
        parsed_content = None
        input_tokens = 0
        output_tokens = 0
        
    latency_ms = (time.time() - start_time) * 1000
    logger.log_call(agent_name, input_tokens, output_tokens, latency_ms, tool_calls, error)
    
    return parsed_content

class Orchestrator:
    def __init__(self, logger: AgentLogger):
        self.logger = logger
        
    def decompose(self, query: str) -> List[schemas.SubTask]:
        system_prompt = "You are the Director Orchestrator. Break down the user's query into exactly >=3 subtasks: RESEARCH_QUERY, MARKET_QUERY, SYNTHESIS_TASK."
        result = run_agent_call(self.logger, "Orchestrator_Decompose", system_prompt, query, response_format=SubTaskList)
        if result:
            return result.tasks
        return []

class ResearchAgent:
    def __init__(self, logger: AgentLogger, corpus_dir: str):
        self.logger = logger
        self.corpus_dir = corpus_dir
        
    def retrieve(self, query: str, security_flags: list) -> List[schemas.EvidenceItem]:
        # Read and chunk corpus
        corpus_text = ""
        chunks = []
        if os.path.exists(self.corpus_dir):
            for filename in os.listdir(self.corpus_dir):
                if filename.endswith(".txt"):
                    filepath = os.path.join(self.corpus_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Simple chunking by paragraph
                        paragraphs = content.split("\n\n")
                        for p in paragraphs:
                            if p.strip():
                                is_flagged, clean_p = security.injection_guard(p)
                                if is_flagged:
                                    security_flags.append(f"Security Flag Triggered in {filename}")
                                chunks.append(f"File: {filename}\nContent: {clean_p}")
        
        # Use LLM to extract evidence
        system_prompt = f"You are a Research Agent. Find facts from the following corpus to answer the query.\n\nCorpus:\n{' '.join(chunks)}"
        result = run_agent_call(self.logger, "ResearchAgent", system_prompt, query, response_format=EvidenceList)
        
        valid_evidence = []
        if result:
            for item in result.items:
                # Check grounding
                hallucination_check = tools.check_hallucination(item.claim, chunks)
                if not hallucination_check["supported"]:
                    item.confidence = 0.0
                    security_flags.append(f"Ungrounded claim flagged: {item.claim}")
                valid_evidence.append(item)
                
        return valid_evidence

class MarketSignalAgent:
    def __init__(self, logger: AgentLogger):
        self.logger = logger
        
    def gather(self, query: str) -> schemas.MarketSnapshot:
        # Simulate LLM deciding what sector to look at, then calling tool.
        # For simplicity, we directly call the tool
        start_time = time.time()
        try:
            data = tools.fetch_market_snapshot("Enterprise AI")
            snapshot = schemas.MarketSnapshot(**data)
            error = None
        except Exception as e:
            error = str(e)
            snapshot = schemas.MarketSnapshot(sector="Unknown", retrieved_at="", competitor_prices=[], headlines=[], macro_indicators={})
            
        latency = (time.time() - start_time) * 1000
        self.logger.log_call("MarketSignalAgent", 0, 0, latency, tool_calls=["fetch_market_snapshot"], error=error)
        return snapshot

class AnalystAgent:
    def __init__(self, logger: AgentLogger):
        self.logger = logger
        
    def synthesize(self, evidence: List[schemas.EvidenceItem], market: schemas.MarketSnapshot, critique_notes: str = None) -> schemas.AnalysisOutput:
        evidence_text = "\n".join([e.claim for e in evidence])
        market_text = json.dumps(market.model_dump(), indent=2)
        
        system_prompt = "You are an Analyst. Synthesize the provided evidence and market data into a SWOT analysis, risks, and recommendations."
        if critique_notes:
            system_prompt += f"\n\nRefine based on previous critique:\n{critique_notes}"
            
        user_prompt = f"Evidence:\n{evidence_text}\n\nMarket Data:\n{market_text}"
        
        result = run_agent_call(self.logger, "AnalystAgent", system_prompt, user_prompt, response_format=schemas.AnalysisOutput)
        
        # We manually call the risk tool to demonstrate tool use wiring
        if result:
            for risk in result.risks:
                # Mock risk score calculation tool usage
                # We assume severity implies a generic probability/impact
                prob, impact = 0.5, 0.8 
                risk.risk_score = tools.calculate_risk_score(prob, impact)
                self.logger.log_call("AnalystAgent_Tool", 0, 0, 0, tool_calls=["calculate_risk_score"])
                
        return result

class CritiqueAgent:
    def __init__(self, logger: AgentLogger):
        self.logger = logger
        
    def critique(self, analysis: schemas.AnalysisOutput) -> schemas.CritiqueReport:
        system_prompt = "You are a Critique Agent. Review the Analyst's output. Score grounding, consistency, and actionability 1-5. Verdict must be 'pass' or 'fail'. If overall score < 3.0, it must be 'fail'."
        user_prompt = json.dumps(analysis.model_dump(), indent=2)
        
        result = run_agent_call(self.logger, "CritiqueAgent", system_prompt, user_prompt, response_format=schemas.CritiqueReport)
        return result

def ReportGenerator(query: str, analysis: schemas.AnalysisOutput, critique: schemas.CritiqueReport, evidence: List[schemas.EvidenceItem], logger: AgentLogger, security_flags: List[str]) -> schemas.SIBReport:
    report = schemas.SIBReport(
        query=query,
        generated_at=tools.get_current_datetime(),
        executive_summary="Strategic Intelligence Brief automatically generated.",
        analysis=analysis,
        critique=critique,
        sources=evidence,
        agent_trace=logger.get_all_traces(),
        security_flags=security_flags
    )
    
    # Generate markdown
    md = f"# Strategic Intelligence Brief\n\n"
    md += f"**Generated At:** {report.generated_at}\n"
    md += f"**Query:** {report.query}\n\n"
    
    if security_flags:
        md += f"## ⚠️ SECURITY FLAGS\n"
        for flag in set(security_flags):
            md += f"- {flag}\n"
        md += "\n"
        
    md += f"## Executive Summary\n{report.executive_summary}\n\n"
    
    if analysis:
        md += f"## SWOT Analysis\n"
        md += f"**Strengths:** {', '.join(analysis.swot.S)}\n"
        md += f"**Weaknesses:** {', '.join(analysis.swot.W)}\n"
        md += f"**Opportunities:** {', '.join(analysis.swot.O)}\n"
        md += f"**Threats:** {', '.join(analysis.swot.T)}\n\n"
        
        md += f"## Risks\n"
        for r in analysis.risks:
            md += f"- **{r.severity}** (Score {r.risk_score}): {r.description}\n"
            
        md += f"\n## Recommendations\n"
        for r in analysis.recommendations:
            md += f"- **{r.priority}** - {r.title}: {r.rationale}\n"
            
    if critique:
        md += f"\n## Critique\n"
        md += f"**Verdict:** {critique.verdict.upper()} (Score: {critique.overall_score})\n"
        md += f"**Notes:** {critique.notes}\n"
        
    md += f"\n## Sources\n"
    for e in evidence:
        md += f"- [{e.confidence:.2f}] {e.source_file}: {e.claim}\n"
        
    # Save markdown report
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(logger.output_dir, f"report_{timestamp}.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md)
        
    return report
