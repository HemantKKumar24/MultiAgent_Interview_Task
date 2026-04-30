from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class TaskType(str, Enum):
    RESEARCH_QUERY = "RESEARCH_QUERY"
    MARKET_QUERY = "MARKET_QUERY"
    SYNTHESIS_TASK = "SYNTHESIS_TASK"

class SubTask(BaseModel):
    id: str
    type: TaskType
    query_text: str
    assigned_agent: str
    priority: int

class EvidenceItem(BaseModel):
    claim: str
    source_file: str
    chunk_text: str
    confidence: float

class MarketSnapshot(BaseModel):
    sector: str
    retrieved_at: str
    competitor_prices: List[Dict[str, Any]]
    headlines: List[str]
    macro_indicators: Dict[str, Any]

class SWOT(BaseModel):
    S: List[str]
    W: List[str]
    O: List[str]
    T: List[str]

class Risk(BaseModel):
    description: str
    severity: str
    risk_score: float

class Recommendation(BaseModel):
    title: str
    rationale: str
    priority: str

class AnalysisOutput(BaseModel):
    swot: SWOT
    risks: List[Risk]
    recommendations: List[Recommendation]

class CritiqueScores(BaseModel):
    grounding: int
    consistency: int
    actionability: int

class CritiqueReport(BaseModel):
    scores: CritiqueScores
    overall_score: float
    verdict: str  # "pass" or "fail"
    flags: List[str]
    notes: str

class SIBReport(BaseModel):
    query: str
    generated_at: str
    executive_summary: str
    analysis: AnalysisOutput
    critique: CritiqueReport
    sources: List[EvidenceItem]
    agent_trace: List[Dict[str, Any]]
    security_flags: List[str] = Field(default_factory=list)
