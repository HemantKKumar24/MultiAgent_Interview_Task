import json
import os
import time

class AgentLogger:
    def __init__(self, output_dir: str = "sample_run"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.output_dir, f"trace_{timestamp}.jsonl")
        self.traces = []

    def log_call(self, agent_name: str, input_tokens: int, output_tokens: int, latency_ms: float, tool_calls: list = None, error: str = None):
        """Logs an agent call to the JSONL trace file."""
        if tool_calls is None:
            tool_calls = []
            
        entry = {
            "agent_name": agent_name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
            "tool_calls_made": tool_calls,
            "latency_ms": latency_ms,
            "error": error
        }
        
        self.traces.append(entry)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
            
    def get_all_traces(self) -> list:
        return self.traces
