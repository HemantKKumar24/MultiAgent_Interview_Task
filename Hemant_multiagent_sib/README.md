# Nexara Labs Multi-Agent SIB Generator
**Author:** Hemant  

This repository contains the implementation for the Nexara Labs Strategic Intelligence Brief (SIB) Multi-Agent System.

## Setup & Installation

Follow these steps to set up the environment and run the application locally.

1. **Navigate to the project directory:**
   ```bash
   cd Hemant_multiagent_sib
   ```

2. **Create and Activate a Virtual Environment (Recommended):**
   - **Windows:**
     ```bash
     python -m venv myvenv
     .\myvenv\Scripts\activate
     ```
   - **Mac/Linux:**
     ```bash
     python3 -m venv myvenv
     source myvenv/bin/activate
     ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your OpenAI API Key:**
   This project uses `python-dotenv` to manage environment variables securely.
   - Open the `.env` file located in the project root.
   - Replace the placeholder with your actual OpenAI API Key:
     ```env
     OPENAI_API_KEY=sk-your-actual-api-key
     ```

## How to Run the System

Once setup is complete, you can generate the Strategic Intelligence Brief (SIB) by running the Orchestrator with a query:

```bash
   python main.py --query "Produce a full strategic intelligence brief for Nexara Labs as of today, including competitive positioning, top risks, and expansion recommendations."
   ```

Outputs will be saved in the `sample_run/` directory as `report_<timestamp>.md` and `trace_<timestamp>.jsonl`.

---

## Architecture Answers

### 1. Orchestrator Decision-Making Logic
The Orchestrator acts as the "Director" of the workflow. Upon receiving the free-text query from the user, it first formulates a system prompt using Pydantic's `Structured Outputs` feature to guarantee a strictly formatted response. The LLM is instructed to break the query into exactly three or more subtasks categorised as `RESEARCH_QUERY`, `MARKET_QUERY`, or `SYNTHESIS_TASK`. It avoids hard-coding logic by relying on the LLM's semantic understanding to map the user's intent to these specific functional areas. Once the subtasks are generated, the Orchestrator parallelises the execution (Phase 2) by dispatching the Research Agent and the Market Signal Agent concurrently using `asyncio`. It waits for both to finish before passing their combined outputs to the Analyst Agent (Phase 3). Finally, the Orchestrator delegates quality control to the Critique Agent, running a conditional loop (Phase 5a) that forces the Analyst Agent to retry synthesis if the Critique score falls below the required threshold of 3.0.

### 2. Hardest Design Decision
The hardest design decision was managing how the **Research Agent** handles the document corpus without exceeding token limits or creating complex, over-engineered RAG pipelines. Initially, I considered implementing a heavy vector database like Pinecone. However, to keep the system clean, modular, and easy to grade, I resolved this by doing simple, in-memory paragraph chunking and using the `check_hallucination` tool with a lightweight keyword overlap mechanism. This guarantees that grounding rules are strictly enforced without introducing heavy external dependencies, satisfying the requirements cleanly while allowing the agent interface to remain simple.

### 3. Prompt Injection Guard (`injection_guard`)
The `injection_guard` works as a pre-processing filter before any document chunk is fed into the LLM context. It uses Regular Expressions (RegEx) to scan each text chunk for known adversarial pattern signatures such as "ignore previous", "system override", or "disregard". If a match is found, the guard quarantines the text by replacing it with a `[SECURITY FLAG TRIGGERED]` placeholder. 
**Weaknesses:** Since it relies on pattern matching, it is vulnerable to semantic attacks that use novel phrasing (e.g., "Forget the rules above and instead..."). It also struggles with split-token attacks or encoding tricks. A more robust approach would involve an independent LLM classification pass or a specialized model (like Llama-Guard) to semantically evaluate the chunk for malicious intent.

### 4. Production-Ready Improvements
To make this system production-ready, I would:
*   **Monitoring & Observability:** Replace the basic JSONL logger with Datadog or LangSmith for real-time trace visualisation, latency tracking, and LLM cost tracking per user.
*   **Reliability:** Implement robust retry policies with exponential backoff (using `tenacity`) for all LLM and tool API calls to handle rate limits or transient network errors gracefully.
*   **Cost & Latency:** Implement Semantic Caching (e.g., Redis) to serve identical or highly similar queries instantly without invoking the LLMs. I would also introduce cost-aware routing, defaulting to cheaper models (like GPT-4o-mini) for simple tasks and escalating to larger models only when complex reasoning fails.

### 5. If I had 2 more weeks...
I would build **Agent Memory and Reflection**. I would introduce a shared Redis memory store that allows agents to read and write intermediate findings across multiple turns. Additionally, I would implement a fully functioning asynchronous vector store (like pgvector) for the Research Agent to handle arbitrarily large datasets securely, and create an interactive frontend using Next.js/React to visualize the agent reasoning steps in real-time.
