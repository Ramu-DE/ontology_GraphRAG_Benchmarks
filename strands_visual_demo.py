#!/usr/bin/env python3
"""
AWS Strands Multi-Agent Framework - Visual Demo
Generates interactive HTML visualization of agent workflow
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum


# ============================================================================
# SIMULATED DATA
# ============================================================================

SIMULATED_DATA = {
    "Pembrolizumab": {
        "mechanism": "PD-1 inhibitor - blocks programmed death receptor-1",
        "targets": ["PD-1", "PD-L1"],
        "adverse_events": [
            {"event": "Immune-related pneumonitis", "severity": "high", "frequency": "10%"},
            {"event": "Colitis", "severity": "moderate", "frequency": "8%"},
            {"event": "Hepatitis", "severity": "moderate", "frequency": "5%"},
            {"event": "Thyroid dysfunction", "severity": "low", "frequency": "12%"},
            {"event": "Skin reactions", "severity": "low", "frequency": "15%"},
        ],
        "genetic_validation": {
            "EGFR": {
                "validated": True,
                "evidence": [
                    {"gene": "EGFR", "disease": "Non-Small Cell Lung Cancer", "status": "validated"}
                ]
            }
        }
    }
}


# ============================================================================
# VISUALIZATION DATA TRACKING
# ============================================================================

@dataclass
class VisualHop:
    """Track each hop for visualization"""
    hop_number: int
    timestamp: str
    from_agent: str
    to_agent: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    duration_ms: float


class VisualizationTracker:
    """Tracks workflow execution for visualization"""

    def __init__(self):
        self.hops: List[VisualHop] = []
        self.agents = {}
        self.start_time = datetime.now()

    def register_agent(self, name: str, role: str):
        self.agents[name] = {"name": name, "role": role, "tools_called": 0}

    def record_hop(self, from_agent: str, to_agent: str, tool_name: str,
                   parameters: Dict, result: Any, duration_ms: float):
        hop = VisualHop(
            hop_number=len(self.hops) + 1,
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            from_agent=from_agent,
            to_agent=to_agent,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            duration_ms=duration_ms
        )
        self.hops.append(hop)
        self.agents[to_agent]["tools_called"] += 1

    def to_dict(self):
        return {
            "workflow_name": "Clinical Safety Assessment",
            "start_time": self.start_time.isoformat(),
            "agents": list(self.agents.values()),
            "hops": [asdict(hop) for hop in self.hops],
            "total_hops": len(self.hops),
            "total_duration_ms": sum(hop.duration_ms for hop in self.hops)
        }


# ============================================================================
# SIMPLIFIED AGENT SYSTEM WITH VISUALIZATION
# ============================================================================

class VisualAgent:
    """Agent that tracks execution for visualization"""

    def __init__(self, name: str, role: str, tracker: VisualizationTracker):
        self.name = name
        self.role = role
        self.tracker = tracker
        tracker.register_agent(name, role)

    def call_tool(self, tool_name: str, tool_func: Callable, parameters: Dict) -> Any:
        """Execute tool and track for visualization"""
        import time
        start = time.time()
        result = tool_func(**parameters)
        duration = (time.time() - start) * 1000

        self.tracker.record_hop(
            from_agent="Orchestrator",
            to_agent=self.name,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            duration_ms=duration
        )

        return result


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

def execute_visual_workflow():
    """Execute workflow with visualization tracking"""

    tracker = VisualizationTracker()

    # Create agents
    pharma_agent = VisualAgent("PharmacologyAgent", "Drug Mechanisms", tracker)
    safety_agent = VisualAgent("ClinicalSafetyAgent", "Safety Assessment", tracker)
    genetics_agent = VisualAgent("GeneticsAgent", "Genetic Validation", tracker)

    drug = "Pembrolizumab"

    # Step 1: Get mechanism
    def get_mechanism(drug_name: str):
        return SIMULATED_DATA[drug_name]

    mechanism = pharma_agent.call_tool("get_drug_mechanism", get_mechanism, {"drug_name": drug})

    # Step 2: Get adverse events
    def get_adverse_events(drug_name: str):
        return SIMULATED_DATA[drug_name]["adverse_events"]

    adverse_events = safety_agent.call_tool("get_adverse_events", get_adverse_events, {"drug_name": drug})

    # Step 3: Validate genetics
    def validate_genetics(gene: str, drug_name: str):
        return SIMULATED_DATA[drug_name]["genetic_validation"].get(gene, {})

    genetic_result = genetics_agent.call_tool("validate_genetic_contraindication",
                                              validate_genetics,
                                              {"gene": "EGFR", "drug_name": drug})

    # Calculate result
    risk_score = min(len(adverse_events) * 0.05, 1.0)
    result = {
        "risk_score": risk_score,
        "risk_level": "low" if risk_score < 0.3 else "moderate",
        "adverse_events": [ae["event"] for ae in adverse_events],
        "genetic_validation": genetic_result,
        "mechanism": mechanism["mechanism"],
        "targets": mechanism["targets"]
    }

    return tracker, result


# ============================================================================
# HTML GENERATION
# ============================================================================

def generate_html(tracker: VisualizationTracker, result: Dict):
    """Generate interactive HTML visualization"""

    trace_data = json.dumps(tracker.to_dict(), indent=2)
    result_data = json.dumps(result, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Strands - Clinical Safety Workflow</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-5px);
        }}

        .card h3 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}

        .card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}

        .card .label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}

        .agents-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .agents-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}

        .agent-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }}

        .agent-card::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 3s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 0.8; }}
        }}

        .agent-name {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .agent-role {{
            opacity: 0.9;
            margin-bottom: 15px;
        }}

        .agent-stats {{
            background: rgba(255,255,255,0.2);
            padding: 10px;
            border-radius: 8px;
            font-size: 0.9em;
        }}

        .workflow-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .hop {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            position: relative;
            animation: slideIn 0.5s ease;
        }}

        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(-20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        .hop-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .hop-number {{
            background: #667eea;
            color: white;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }}

        .hop-title {{
            flex: 1;
            margin-left: 15px;
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
        }}

        .hop-time {{
            color: #666;
            font-size: 0.9em;
        }}

        .hop-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}

        .detail-box {{
            background: white;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }}

        .detail-label {{
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
            font-weight: 600;
        }}

        .detail-value {{
            color: #333;
            font-size: 0.95em;
        }}

        .result-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .risk-indicator {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.2em;
            margin: 15px 0;
        }}

        .risk-low {{
            background: #d4edda;
            color: #155724;
        }}

        .risk-moderate {{
            background: #fff3cd;
            color: #856404;
        }}

        .risk-high {{
            background: #f8d7da;
            color: #721c24;
        }}

        .adverse-events {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}

        .adverse-event {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #dc3545;
        }}

        .json-view {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin-top: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        .toggle-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 10px;
            transition: background 0.3s ease;
        }}

        .toggle-btn:hover {{
            background: #5568d3;
        }}

        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 AWS Strands Multi-Agent Framework</h1>
            <p>Clinical Safety Workflow Visualization</p>
        </div>

        <div class="dashboard">
            <div class="card">
                <h3>Total Hops</h3>
                <div class="value">{len(tracker.hops)}</div>
                <div class="label">Agent interactions</div>
            </div>
            <div class="card">
                <h3>Active Agents</h3>
                <div class="value">{len(tracker.agents)}</div>
                <div class="label">Specialized agents</div>
            </div>
            <div class="card">
                <h3>Total Duration</h3>
                <div class="value">{sum(hop.duration_ms for hop in tracker.hops):.1f}ms</div>
                <div class="label">Execution time</div>
            </div>
            <div class="card">
                <h3>Risk Score</h3>
                <div class="value">{result['risk_score']:.2f}</div>
                <div class="label">Safety assessment</div>
            </div>
        </div>

        <div class="agents-section">
            <h2 class="section-title">🤖 Active Agents</h2>
            <div class="agents-grid">
"""

    for agent in tracker.agents.values():
        html += f"""
                <div class="agent-card">
                    <div class="agent-name">{agent['name']}</div>
                    <div class="agent-role">{agent['role']}</div>
                    <div class="agent-stats">
                        Tools Called: {agent['tools_called']}<br>
                        Status: ✓ Active
                    </div>
                </div>
"""

    html += """
            </div>
        </div>

        <div class="workflow-section">
            <h2 class="section-title">🔄 Workflow Execution (Hop-by-Hop)</h2>
"""

    for hop in tracker.hops:
        params_str = json.dumps(hop.parameters, indent=2)
        html += f"""
            <div class="hop">
                <div class="hop-header">
                    <div class="hop-number">{hop.hop_number}</div>
                    <div class="hop-title">{hop.to_agent} → {hop.tool_name}</div>
                    <div class="hop-time">{hop.timestamp} ({hop.duration_ms:.2f}ms)</div>
                </div>
                <div class="hop-details">
                    <div class="detail-box">
                        <div class="detail-label">From Agent</div>
                        <div class="detail-value">{hop.from_agent}</div>
                    </div>
                    <div class="detail-box">
                        <div class="detail-label">To Agent</div>
                        <div class="detail-value">{hop.to_agent}</div>
                    </div>
                    <div class="detail-box">
                        <div class="detail-label">Tool</div>
                        <div class="detail-value">{hop.tool_name}</div>
                    </div>
                    <div class="detail-box">
                        <div class="detail-label">Duration</div>
                        <div class="detail-value">{hop.duration_ms:.2f}ms</div>
                    </div>
                </div>
                <button class="toggle-btn" onclick="toggleDetails('hop{hop.hop_number}')">
                    Show Details
                </button>
                <div id="hop{hop.hop_number}" class="json-view hidden">
                    <strong>Parameters:</strong><br>{params_str}
                </div>
            </div>
"""

    html += f"""
        </div>

        <div class="result-section">
            <h2 class="section-title">📊 Clinical Safety Assessment Result</h2>

            <div style="margin: 20px 0;">
                <strong style="font-size: 1.2em;">Risk Level:</strong>
                <span class="risk-indicator risk-{result['risk_level']}">{result['risk_level'].upper()}</span>
            </div>

            <div style="margin: 20px 0;">
                <strong style="font-size: 1.1em;">Risk Score:</strong> {result['risk_score']:.2f}/1.00
            </div>

            <div style="margin: 20px 0;">
                <strong style="font-size: 1.1em;">Drug Mechanism:</strong>
                <p style="margin-top: 10px; color: #666;">{result['mechanism']}</p>
            </div>

            <div style="margin: 20px 0;">
                <strong style="font-size: 1.1em;">Protein Targets:</strong>
                <p style="margin-top: 10px; color: #666;">{', '.join(result['targets'])}</p>
            </div>

            <div style="margin: 20px 0;">
                <strong style="font-size: 1.1em;">Adverse Events Identified:</strong>
                <div class="adverse-events">
"""

    for event in result['adverse_events']:
        html += f"""
                    <div class="adverse-event">{event}</div>
"""

    html += f"""
                </div>
            </div>

            <div style="margin: 20px 0;">
                <strong style="font-size: 1.1em;">Genetic Validation:</strong>
                <p style="margin-top: 10px; color: #666;">
                    Status: {'✓ Validated' if result['genetic_validation'].get('validated') else '✗ Not Validated'}
                </p>
            </div>

            <button class="toggle-btn" onclick="toggleDetails('fullResult')">
                Show Full JSON Result
            </button>
            <div id="fullResult" class="json-view hidden">{result_data}</div>

            <button class="toggle-btn" onclick="toggleDetails('traceData')">
                Show Full Trace Data
            </button>
            <div id="traceData" class="json-view hidden">{trace_data}</div>
        </div>
    </div>

    <script>
        function toggleDetails(id) {{
            const element = document.getElementById(id);
            const button = event.target;
            if (element.classList.contains('hidden')) {{
                element.classList.remove('hidden');
                button.textContent = button.textContent.replace('Show', 'Hide');
            }} else {{
                element.classList.add('hidden');
                button.textContent = button.textContent.replace('Hide', 'Show');
            }}
        }}
    </script>
</body>
</html>
"""

    return html


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("Executing AWS Strands workflow with visualization tracking...")

    # Execute workflow
    tracker, result = execute_visual_workflow()

    # Generate HTML
    html = generate_html(tracker, result)

    # Save HTML
    filename = "strands_visualization.html"
    with open(filename, "w") as f:
        f.write(html)

    print(f"\n✓ Workflow complete!")
    print(f"✓ Generated visual report: {filename}")
    print(f"\nTo view the visualization:")
    print(f"  1. Open {filename} in your web browser")
    print(f"  2. Or run: xdg-open {filename}  (Linux)")
    print(f"  3. Or run: open {filename}  (Mac)")
    print(f"\nWorkflow Summary:")
    print(f"  - Total Hops: {len(tracker.hops)}")
    print(f"  - Active Agents: {len(tracker.agents)}")
    print(f"  - Risk Score: {result['risk_score']:.2f}")
    print(f"  - Risk Level: {result['risk_level'].upper()}")
    print(f"  - Adverse Events: {len(result['adverse_events'])}")


if __name__ == "__main__":
    main()
