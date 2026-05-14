#!/usr/bin/env python3
"""
Strands Multi-Agent Framework - Hop-by-Hop Traversal Visualizer

Provides real-time animated visualization of:
- Agent-to-agent communication
- Graph query execution
- Data flow between agents
- Reasoning steps
"""

import os
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# Terminal colors
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


@dataclass
class Hop:
    """Represents one hop in the agent traversal"""
    hop_number: int
    timestamp: datetime
    from_agent: str
    to_agent: str
    action: str
    cypher_query: Optional[str]
    parameters: Dict[str, Any]
    results: List[Dict[str, Any]]
    processing_time_ms: float
    data_transferred: Dict[str, Any]
    reasoning: str


@dataclass
class AgentNode:
    """Represents an agent in the visualization"""
    name: str
    role: str
    status: str  # "idle", "thinking", "querying", "sending", "complete"
    current_task: str = ""
    messages_sent: int = 0
    messages_received: int = 0
    queries_executed: int = 0


class StrandsVisualizer:
    """
    Animated hop-by-hop visualization of multi-agent workflow

    Shows:
    - Agent communication flow
    - Graph query execution
    - Data transfer between agents
    - Real-time progress
    """

    def __init__(self):
        self.hops: List[Hop] = []
        self.agents: Dict[str, AgentNode] = {}
        self.current_workflow = ""
        self.start_time = None

    def register_agent(self, name: str, role: str):
        """Register an agent for visualization"""
        self.agents[name] = AgentNode(name=name, role=role, status="idle")

    def start_workflow(self, workflow_name: str):
        """Start tracking a new workflow"""
        self.current_workflow = workflow_name
        self.start_time = datetime.now()
        self.hops = []

        # Reset all agents to idle
        for agent in self.agents.values():
            agent.status = "idle"
            agent.current_task = ""

        self._clear_screen()
        self._print_header()
        print(f"\n{Color.BOLD}{Color.CYAN}Starting Workflow: {workflow_name}{Color.END}\n")
        time.sleep(1)

    def record_hop(self, hop: Hop):
        """Record a new hop in the traversal"""
        self.hops.append(hop)

        # Update agent statuses
        if hop.from_agent in self.agents:
            self.agents[hop.from_agent].messages_sent += 1
        if hop.to_agent in self.agents:
            self.agents[hop.to_agent].messages_received += 1
            self.agents[hop.to_agent].queries_executed += 1

        # Animate this hop
        self._animate_hop(hop)

    def _animate_hop(self, hop: Hop):
        """Animate a single hop with graph traversal"""

        # Step 1: Show agent thinking
        self._update_agent_status(hop.from_agent, "thinking", f"Planning: {hop.action}")
        self._render_current_state()
        time.sleep(0.5)

        # Step 2: Show message being sent
        self._update_agent_status(hop.from_agent, "sending", f"→ {hop.to_agent}")
        self._render_current_state()
        self._draw_message_arrow(hop.from_agent, hop.to_agent, "Sending task")
        time.sleep(0.5)

        # Step 3: Show agent receiving
        self._update_agent_status(hop.to_agent, "querying", hop.action)
        self._render_current_state()
        time.sleep(0.3)

        # Step 4: Show Cypher query execution
        if hop.cypher_query:
            self._show_graph_query(hop)
            time.sleep(1.0)

        # Step 5: Show results
        self._show_hop_results(hop)
        time.sleep(0.5)

        # Step 6: Show data transfer back
        self._update_agent_status(hop.to_agent, "sending", f"→ {hop.from_agent}")
        self._render_current_state()
        self._draw_message_arrow(hop.to_agent, hop.from_agent, f"Returning {len(hop.results)} results")
        time.sleep(0.5)

        # Step 7: Mark as complete
        self._update_agent_status(hop.to_agent, "complete", "Task complete")
        self._update_agent_status(hop.from_agent, "thinking", "Processing results")
        self._render_current_state()
        time.sleep(0.3)

    def _show_graph_query(self, hop: Hop):
        """Show the graph query being executed with animation"""
        print(f"\n{Color.BOLD}{Color.YELLOW}{'='*80}{Color.END}")
        print(f"{Color.BOLD}{Color.YELLOW}HOP {hop.hop_number}: GRAPH TRAVERSAL{Color.END}")
        print(f"{Color.YELLOW}{'='*80}{Color.END}")

        print(f"\n{Color.CYAN}Agent:{Color.END} {hop.to_agent}")
        print(f"{Color.CYAN}Action:{Color.END} {hop.action}")

        # Show Cypher query with syntax highlighting
        print(f"\n{Color.BOLD}{Color.GREEN}Cypher Query:{Color.END}")
        self._print_cypher_with_highlighting(hop.cypher_query)

        # Show parameters
        if hop.parameters:
            print(f"\n{Color.BOLD}{Color.GREEN}Parameters:{Color.END}")
            for key, value in hop.parameters.items():
                print(f"  {Color.CYAN}${key}{Color.END} = {Color.YELLOW}{value}{Color.END}")

        # Animate query execution
        print(f"\n{Color.CYAN}Executing query", end="", flush=True)
        for _ in range(3):
            time.sleep(0.3)
            print(".", end="", flush=True)
        print(f" {Color.GREEN}✓{Color.END}")

        # Show execution time
        print(f"\n{Color.CYAN}Execution time:{Color.END} {hop.processing_time_ms:.2f}ms")

    def _print_cypher_with_highlighting(self, query: str):
        """Print Cypher query with syntax highlighting"""
        lines = query.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Highlight keywords
            keywords = ['MATCH', 'WHERE', 'RETURN', 'WITH', 'ORDER BY', 'LIMIT',
                       'CREATE', 'MERGE', 'DELETE', 'SET', 'OPTIONAL']
            for keyword in keywords:
                line = line.replace(keyword, f"{Color.BOLD}{Color.BLUE}{keyword}{Color.END}")

            # Highlight strings
            import re
            line = re.sub(r'"([^"]*)"', f'{Color.YELLOW}"\g<1>"{Color.END}', line)
            line = re.sub(r"'([^']*)'", f"{Color.YELLOW}'\g<1>'{Color.END}", line)

            print(f"  {line}")

    def _show_hop_results(self, hop: Hop):
        """Show results from the hop"""
        print(f"\n{Color.BOLD}{Color.GREEN}Results:{Color.END} Found {len(hop.results)} records")

        if hop.results:
            # Show first few results
            display_count = min(3, len(hop.results))
            for i, result in enumerate(hop.results[:display_count]):
                print(f"\n{Color.CYAN}Record {i+1}:{Color.END}")
                for key, value in result.items():
                    value_str = str(value)
                    if len(value_str) > 60:
                        value_str = value_str[:60] + "..."
                    print(f"  {Color.YELLOW}{key}:{Color.END} {value_str}")

            if len(hop.results) > display_count:
                print(f"\n  {Color.CYAN}... and {len(hop.results) - display_count} more records{Color.END}")

    def _render_current_state(self):
        """Render the current state of all agents"""
        self._clear_screen()
        self._print_header()

        # Show workflow progress
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{Color.BOLD}Workflow:{Color.END} {self.current_workflow}")
        print(f"{Color.BOLD}Elapsed:{Color.END} {elapsed:.1f}s | {Color.BOLD}Hops:{Color.END} {len(self.hops)}")

        # Show agent states
        print(f"\n{Color.BOLD}{Color.UNDERLINE}Agent States:{Color.END}")
        self._draw_agent_grid()

        print()

    def _draw_agent_grid(self):
        """Draw a grid showing all agents and their status"""
        agents_list = list(self.agents.values())

        for agent in agents_list:
            status_symbol = self._get_status_symbol(agent.status)
            status_color = self._get_status_color(agent.status)

            print(f"\n{status_color}{status_symbol}{Color.END} {Color.BOLD}{agent.name}{Color.END}")
            print(f"   Role: {Color.CYAN}{agent.role}{Color.END}")
            print(f"   Status: {status_color}{agent.status}{Color.END}")
            if agent.current_task:
                print(f"   Task: {Color.YELLOW}{agent.current_task}{Color.END}")
            print(f"   Stats: {Color.GREEN}↑{agent.messages_sent} ↓{agent.messages_received} ⚡{agent.queries_executed}{Color.END}")

    def _draw_message_arrow(self, from_agent: str, to_agent: str, message: str):
        """Draw an animated arrow showing message flow"""
        print(f"\n{Color.CYAN}{'─'*80}{Color.END}")
        print(f"{Color.BOLD}{from_agent}{Color.END} {Color.YELLOW}─→{Color.END} {Color.BOLD}{to_agent}{Color.END}")
        print(f"{Color.CYAN}Message:{Color.END} {message}")
        print(f"{Color.CYAN}{'─'*80}{Color.END}")

    def _get_status_symbol(self, status: str) -> str:
        """Get emoji/symbol for status"""
        symbols = {
            "idle": "⚪",
            "thinking": "🤔",
            "querying": "🔍",
            "sending": "📤",
            "complete": "✅"
        }
        return symbols.get(status, "⚪")

    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        colors = {
            "idle": Color.END,
            "thinking": Color.YELLOW,
            "querying": Color.CYAN,
            "sending": Color.BLUE,
            "complete": Color.GREEN
        }
        return colors.get(status, Color.END)

    def _update_agent_status(self, agent_name: str, status: str, task: str = ""):
        """Update agent status"""
        if agent_name in self.agents:
            self.agents[agent_name].status = status
            self.agents[agent_name].current_task = task

    def _clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')

    def _print_header(self):
        """Print visualization header"""
        print(f"{Color.BOLD}{Color.HEADER}{'='*80}{Color.END}")
        print(f"{Color.BOLD}{Color.HEADER}STRANDS MULTI-AGENT FRAMEWORK - HOP-BY-HOP VISUALIZATION{Color.END}")
        print(f"{Color.BOLD}{Color.HEADER}{'='*80}{Color.END}")

    def generate_summary(self):
        """Generate workflow summary"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        self._clear_screen()
        print(f"\n{Color.BOLD}{Color.GREEN}{'='*80}{Color.END}")
        print(f"{Color.BOLD}{Color.GREEN}WORKFLOW COMPLETE: {self.current_workflow}{Color.END}")
        print(f"{Color.BOLD}{Color.GREEN}{'='*80}{Color.END}\n")

        print(f"{Color.BOLD}Total Time:{Color.END} {elapsed:.2f}s")
        print(f"{Color.BOLD}Total Hops:{Color.END} {len(self.hops)}")

        # Calculate statistics
        total_queries = sum(a.queries_executed for a in self.agents.values())
        total_messages = sum(a.messages_sent for a in self.agents.values())

        print(f"{Color.BOLD}Graph Queries:{Color.END} {total_queries}")
        print(f"{Color.BOLD}Messages Exchanged:{Color.END} {total_messages}")

        # Show hop sequence
        print(f"\n{Color.BOLD}{Color.UNDERLINE}Hop Sequence:{Color.END}\n")
        for hop in self.hops:
            print(f"{Color.CYAN}Hop {hop.hop_number}:{Color.END} "
                  f"{hop.from_agent} → {hop.to_agent} | "
                  f"{Color.YELLOW}{hop.action}{Color.END} | "
                  f"{len(hop.results)} results | "
                  f"{hop.processing_time_ms:.2f}ms")

        # Show agent performance
        print(f"\n{Color.BOLD}{Color.UNDERLINE}Agent Performance:{Color.END}\n")
        for agent in self.agents.values():
            if agent.queries_executed > 0:
                print(f"{Color.BOLD}{agent.name}:{Color.END} "
                      f"{agent.queries_executed} queries | "
                      f"{agent.messages_sent} sent | "
                      f"{agent.messages_received} received")

    def export_trace(self, filename: str = "strands_trace.json"):
        """Export complete trace to JSON"""
        trace = {
            "workflow": self.current_workflow,
            "start_time": self.start_time.isoformat(),
            "total_hops": len(self.hops),
            "agents": {name: {
                "role": agent.role,
                "queries_executed": agent.queries_executed,
                "messages_sent": agent.messages_sent,
                "messages_received": agent.messages_received
            } for name, agent in self.agents.items()},
            "hops": [{
                "hop_number": hop.hop_number,
                "timestamp": hop.timestamp.isoformat(),
                "from_agent": hop.from_agent,
                "to_agent": hop.to_agent,
                "action": hop.action,
                "cypher_query": hop.cypher_query,
                "parameters": hop.parameters,
                "results_count": len(hop.results),
                "processing_time_ms": hop.processing_time_ms,
                "reasoning": hop.reasoning
            } for hop in self.hops]
        }

        with open(filename, 'w') as f:
            json.dump(trace, f, indent=2)

        print(f"\n{Color.GREEN}✓ Trace exported to: {filename}{Color.END}")


class GraphPathVisualizer:
    """
    Visualizes the actual graph paths traversed during queries
    Shows nodes and relationships visited
    """

    @staticmethod
    def visualize_path(query_result: List[Dict], query_type: str):
        """Visualize the graph path from query results"""
        print(f"\n{Color.BOLD}{Color.BLUE}Graph Path Visualization:{Color.END}\n")

        if query_type == "drug_to_disease":
            GraphPathVisualizer._draw_drug_disease_path(query_result)
        elif query_type == "gene_to_treatment":
            GraphPathVisualizer._draw_gene_treatment_path(query_result)
        elif query_type == "trial_network":
            GraphPathVisualizer._draw_trial_network(query_result)
        else:
            GraphPathVisualizer._draw_generic_path(query_result)

    @staticmethod
    def _draw_drug_disease_path(results: List[Dict]):
        """Draw drug → protein → disease path"""
        for i, result in enumerate(results[:3], 1):
            print(f"{Color.CYAN}Path {i}:{Color.END}")

            drug = result.get('drug', result.get('drugName', 'Drug'))
            protein = result.get('protein', result.get('proteinName', 'Protein'))
            disease = result.get('disease', result.get('diseaseName', 'Disease'))

            print(f"  ({Color.GREEN}Drug{Color.END}) {Color.BOLD}{drug}{Color.END}")
            print(f"       │")
            print(f"       │ {Color.YELLOW}TARGETS{Color.END}")
            print(f"       ↓")
            print(f"  ({Color.BLUE}Protein{Color.END}) {Color.BOLD}{protein}{Color.END}")
            print(f"       │")
            print(f"       │ {Color.YELLOW}RELEVANT_TO{Color.END}")
            print(f"       ↓")
            print(f"  ({Color.RED}Disease{Color.END}) {Color.BOLD}{disease}{Color.END}")
            print()

    @staticmethod
    def _draw_gene_treatment_path(results: List[Dict]):
        """Draw gene → disease → drug path"""
        for i, result in enumerate(results[:3], 1):
            print(f"{Color.CYAN}Path {i}:{Color.END}")

            gene = result.get('gene', result.get('geneSymbol', 'Gene'))
            disease = result.get('disease', result.get('diseaseName', 'Disease'))
            drug = result.get('drug', result.get('drugName', 'Drug'))
            efficacy = result.get('efficacy', 0)

            print(f"  ({Color.YELLOW}Gene{Color.END}) {Color.BOLD}{gene}{Color.END}")
            print(f"       │")
            print(f"       │ {Color.YELLOW}ASSOCIATED_WITH{Color.END}")
            print(f"       ↓")
            print(f"  ({Color.RED}Disease{Color.END}) {Color.BOLD}{disease}{Color.END}")
            print(f"       │")
            print(f"       │ {Color.YELLOW}TREATED_BY{Color.END}")
            print(f"       ↓")
            print(f"  ({Color.GREEN}Drug{Color.END}) {Color.BOLD}{drug}{Color.END} "
                  f"({Color.CYAN}{efficacy:.1%} efficacy{Color.END})")
            print()

    @staticmethod
    def _draw_trial_network(results: List[Dict]):
        """Draw trial network"""
        print(f"{Color.CYAN}Trial Network:{Color.END}\n")

        for result in results[:5]:
            trial = result.get('trial', result.get('trialTitle', 'Trial'))
            drug = result.get('drug', result.get('drugName', ''))
            disease = result.get('disease', result.get('diseaseName', ''))

            print(f"  ({Color.BLUE}Trial{Color.END}) {trial[:50]}...")
            if drug:
                print(f"       ├─ {Color.YELLOW}INVESTIGATES{Color.END} → ({Color.GREEN}Drug{Color.END}) {drug}")
            if disease:
                print(f"       └─ {Color.YELLOW}STUDIES{Color.END} → ({Color.RED}Disease{Color.END}) {disease}")
            print()

    @staticmethod
    def _draw_generic_path(results: List[Dict]):
        """Draw generic path"""
        for i, result in enumerate(results[:5], 1):
            print(f"{Color.CYAN}Record {i}:{Color.END}")
            for key, value in result.items():
                print(f"  {Color.YELLOW}{key}:{Color.END} {value}")
            print()


def create_test_visualization():
    """Create a test visualization"""
    visualizer = StrandsVisualizer()

    # Register agents
    visualizer.register_agent("ClinicalSafetyAgent", "Clinical Safety Specialist")
    visualizer.register_agent("PharmacologyAgent", "Pharmacology Specialist")
    visualizer.register_agent("GeneticsAgent", "Genetics Specialist")
    visualizer.register_agent("TrialDataAgent", "Clinical Trial Specialist")

    # Start workflow
    visualizer.start_workflow("Clinical Safety Analysis - Pembrolizumab")

    # Simulate hops
    hop1 = Hop(
        hop_number=1,
        timestamp=datetime.now(),
        from_agent="ClinicalSafetyAgent",
        to_agent="PharmacologyAgent",
        action="Get drug mechanism and targets",
        cypher_query="""
        MATCH (d:Drug {name: $drug_name})-[t:TARGETS]->(p:Protein)
        RETURN d.mechanism as mechanism,
               collect(p.name) as targets
        """,
        parameters={"drug_name": "Pembrolizumab"},
        results=[{
            "mechanism": "PD-1 inhibitor",
            "targets": ["PD-1"]
        }],
        processing_time_ms=45.2,
        data_transferred={"mechanism": "PD-1 inhibitor"},
        reasoning="Need to understand drug mechanism before safety analysis"
    )
    visualizer.record_hop(hop1)

    hop2 = Hop(
        hop_number=2,
        timestamp=datetime.now(),
        from_agent="ClinicalSafetyAgent",
        to_agent="TrialDataAgent",
        action="Get adverse events from trials",
        cypher_query="""
        MATCH (d:Drug {name: $drug_name})<-[:INVESTIGATES]-(t:ClinicalTrial)
              -[:REPORTS]->(e:AdverseEvent)
        RETURN e.name as event, e.severity as severity
        ORDER BY e.severity DESC
        """,
        parameters={"drug_name": "Pembrolizumab"},
        results=[
            {"event": "Immune-related pneumonitis", "severity": "Severe"},
            {"event": "Immune-related colitis", "severity": "Moderate"}
        ],
        processing_time_ms=62.8,
        data_transferred={"adverse_events": 2},
        reasoning="Assess safety profile from clinical trials"
    )
    visualizer.record_hop(hop2)

    hop3 = Hop(
        hop_number=3,
        timestamp=datetime.now(),
        from_agent="ClinicalSafetyAgent",
        to_agent="GeneticsAgent",
        action="Validate genetic evidence",
        cypher_query="""
        MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(d:Disease)
              <-[tr:TREATS]-(drug:Drug {name: $drug_name})
        RETURN g.symbol as gene, d.name as disease, tr.efficacyRate as efficacy
        """,
        parameters={"gene": "EGFR", "drug_name": "Pembrolizumab"},
        results=[{
            "gene": "EGFR",
            "disease": "Non-Small Cell Lung Cancer",
            "efficacy": 0.45
        }],
        processing_time_ms=38.5,
        data_transferred={"genetic_match": True, "efficacy": 0.45},
        reasoning="Validate drug efficacy for patient's genetic profile"
    )
    visualizer.record_hop(hop3)

    # Generate summary
    time.sleep(1)
    visualizer.generate_summary()

    # Export trace
    visualizer.export_trace()

    return visualizer


if __name__ == "__main__":
    print(f"\n{Color.BOLD}{Color.CYAN}Testing Strands Hop-by-Hop Visualizer{Color.END}\n")
    visualizer = create_test_visualization()
    print(f"\n{Color.GREEN}✓ Visualization test complete!{Color.END}\n")
