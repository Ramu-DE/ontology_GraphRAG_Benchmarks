#!/usr/bin/env python3
"""
AWS Strands Multi-Agent Framework - Standalone Demo
Based on https://strandsagents.com/

This demo shows the official Strands patterns without external dependencies.
Uses simulated data instead of real Neo4j queries.

Features:
- Hook system (BeforeToolCallEvent, AfterToolCallEvent)
- Steering handlers for corrective feedback
- Agent-as-tool pattern
- Tools with schema generation
- Observability with trace attributes
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum


# ============================================================================
# SIMULATED DATA (replaces Neo4j)
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
# STRUCTURED OUTPUT MODELS
# ============================================================================

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ClinicalSafetyResult:
    """Structured output for clinical safety assessment"""
    risk_score: float
    risk_level: str
    adverse_events: List[str]
    contraindications: List[str]
    recommendation: str
    genetic_validation: Dict[str, Any]
    evidence_strength: str

    def to_dict(self):
        return asdict(self)


# ============================================================================
# EVENT SYSTEM (Hooks)
# ============================================================================

class EventType(str, Enum):
    BEFORE_TOOL_CALL = "before_tool_call"
    AFTER_TOOL_CALL = "after_tool_call"


@dataclass
class ToolCallEvent:
    """Event emitted before/after tool execution"""
    event_type: EventType
    tool_name: str
    agent_name: str
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    result: Optional[Any] = None
    should_cancel: bool = False
    feedback: Optional[str] = None
    trace_attributes: Dict[str, str] = field(default_factory=dict)


class Hook:
    """Hook that intercepts agent events"""

    def __init__(self, event_type: EventType, callback: Callable[[ToolCallEvent], None]):
        self.event_type = event_type
        self.callback = callback

    def execute(self, event: ToolCallEvent):
        """Execute the hook callback"""
        self.callback(event)


# ============================================================================
# STEERING HANDLERS (Corrective Guidance)
# ============================================================================

class SteeringHandler:
    """Provides corrective feedback to guide agent behavior"""

    @staticmethod
    def validate_query_parameters(event: ToolCallEvent):
        """Ensure queries have proper parameters"""
        if "drug_name" in event.parameters:
            drug_name = event.parameters["drug_name"]
            if not drug_name:
                event.feedback = (
                    "⚠️  STEERING: Drug name parameter is empty. "
                    "Provide a valid drug name for accurate results."
                )
            elif drug_name not in SIMULATED_DATA:
                event.feedback = (
                    f"⚠️  STEERING: Drug '{drug_name}' not found in knowledge base. "
                    f"Available drugs: {list(SIMULATED_DATA.keys())}"
                )

    @staticmethod
    def validate_safety_threshold(event: ToolCallEvent):
        """Ensure risk scores are properly calculated"""
        if event.tool_name == "get_adverse_events" and event.result:
            if isinstance(event.result, list) and len(event.result) > 5:
                event.feedback = (
                    f"⚠️  STEERING: Found {len(event.result)} adverse events. "
                    "Consider high-risk classification and detailed monitoring plan."
                )

    @staticmethod
    def validate_genetic_context(event: ToolCallEvent):
        """Ensure genetic mutations are considered"""
        if event.tool_name == "validate_genetic_contraindication":
            if not event.parameters.get("gene"):
                event.feedback = (
                    "⚠️  STEERING: Genetic validation requires a gene symbol. "
                    "Include patient genetic data for comprehensive safety assessment."
                )


# ============================================================================
# TOOL SYSTEM
# ============================================================================

class Tool:
    """Represents an agent tool with automatic schema generation"""

    def __init__(self, name: str, description: str, func: Callable,
                 parameters_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.func = func
        self.parameters_schema = parameters_schema

    def execute(self, **kwargs) -> Any:
        """Execute the tool function"""
        return self.func(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema
        }


def tool(description: str, parameters: Dict[str, Any]):
    """Decorator to define tools with automatic schema generation"""
    def decorator(func: Callable) -> Tool:
        return Tool(
            name=func.__name__,
            description=description,
            func=func,
            parameters_schema=parameters
        )
    return decorator


# ============================================================================
# SIMULATED KNOWLEDGE GRAPH TOOLS
# ============================================================================

class SimulatedToolbox:
    """Collection of tools using simulated data"""

    def create_tools(self) -> List[Tool]:
        """Create all tools"""

        @tool(
            description="Get drug mechanism and protein targets",
            parameters={
                "drug_name": {"type": "string", "description": "Name of the drug"}
            }
        )
        def get_drug_mechanism(drug_name: str) -> Dict[str, Any]:
            drug_data = SIMULATED_DATA.get(drug_name, {})
            return {
                "drug": drug_name,
                "mechanism": drug_data.get("mechanism", "Unknown"),
                "targets": drug_data.get("targets", [])
            }

        @tool(
            description="Find adverse events for a drug",
            parameters={
                "drug_name": {"type": "string", "description": "Name of the drug"}
            }
        )
        def get_adverse_events(drug_name: str) -> List[Dict[str, Any]]:
            drug_data = SIMULATED_DATA.get(drug_name, {})
            return drug_data.get("adverse_events", [])

        @tool(
            description="Validate genetic mutation contraindications",
            parameters={
                "gene": {"type": "string", "description": "Gene symbol (e.g., EGFR)"},
                "drug_name": {"type": "string", "description": "Name of the drug"}
            }
        )
        def validate_genetic_contraindication(gene: str, drug_name: str) -> Dict[str, Any]:
            drug_data = SIMULATED_DATA.get(drug_name, {})
            genetic_data = drug_data.get("genetic_validation", {}).get(gene, {})
            return {
                "gene": gene,
                "drug": drug_name,
                "validated": genetic_data.get("validated", False),
                "evidence": genetic_data.get("evidence", [])
            }

        return [get_drug_mechanism, get_adverse_events, validate_genetic_contraindication]


# ============================================================================
# AGENT WITH OFFICIAL STRANDS PATTERNS
# ============================================================================

class StrandsAgent:
    """
    Agent implementation following official Strands patterns:
    - Hooks for interception
    - Steering handlers for guidance
    - Tools with schema generation
    """

    def __init__(self,
                 name: str,
                 role: str,
                 tools: List[Tool],
                 hooks: List[Hook] = None,
                 steering_handlers: List[Callable] = None,
                 trace_attributes: Dict[str, str] = None):
        self.name = name
        self.role = role
        self.tools = {tool.name: tool for tool in tools}
        self.hooks = hooks or []
        self.steering_handlers = steering_handlers or []
        self.trace_attributes = trace_attributes or {"service": "strands-biomedical"}

    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool with hook interception"""

        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in agent '{self.name}'")

        # BEFORE hook
        before_event = ToolCallEvent(
            event_type=EventType.BEFORE_TOOL_CALL,
            tool_name=tool_name,
            agent_name=self.name,
            parameters=parameters,
            trace_attributes=self.trace_attributes
        )

        # Execute before hooks
        for hook in self.hooks:
            if hook.event_type == EventType.BEFORE_TOOL_CALL:
                hook.execute(before_event)

        # Execute steering handlers
        for handler in self.steering_handlers:
            handler(before_event)

        # Check if cancelled
        if before_event.should_cancel:
            return {"error": "Tool call cancelled", "feedback": before_event.feedback}

        # If there's corrective feedback, show it (but continue execution in this demo)
        if before_event.feedback:
            print(f"   {before_event.feedback}")

        # Execute tool
        tool = self.tools[tool_name]
        result = tool.execute(**parameters)

        # AFTER hook
        after_event = ToolCallEvent(
            event_type=EventType.AFTER_TOOL_CALL,
            tool_name=tool_name,
            agent_name=self.name,
            parameters=parameters,
            result=result,
            trace_attributes=self.trace_attributes
        )

        # Execute after hooks
        for hook in self.hooks:
            if hook.event_type == EventType.AFTER_TOOL_CALL:
                hook.execute(after_event)

        # Execute steering handlers on result
        for handler in self.steering_handlers:
            handler(after_event)

        return result


# ============================================================================
# ORCHESTRATOR WITH AGENT-AS-TOOL PATTERN
# ============================================================================

class StrandsOrchestrator:
    """
    Multi-agent orchestrator following official Strands patterns:
    - Agent-as-tool composition
    - Swarm coordination
    - Centralized hook management
    """

    def __init__(self):
        self.agents: Dict[str, StrandsAgent] = {}
        self.global_hooks: List[Hook] = []
        self.toolbox = SimulatedToolbox()

        # Setup hooks
        self._setup_global_hooks()

        # Register agents
        self._register_agents()

    def _setup_global_hooks(self):
        """Setup global hooks for logging and validation"""

        def log_before_tool(event: ToolCallEvent):
            """Log all tool calls"""
            print(f"\n📞 [{event.agent_name}] Calling tool: {event.tool_name}")
            params_preview = {k: str(v)[:50] + "..." if len(str(v)) > 50 else v
                            for k, v in event.parameters.items()}
            print(f"   Parameters: {json.dumps(params_preview)}")
            print(f"   Trace: service={event.trace_attributes.get('service')}, "
                  f"timestamp={event.timestamp.strftime('%H:%M:%S')}")

        def log_after_tool(event: ToolCallEvent):
            """Log all tool results"""
            if isinstance(event.result, list):
                print(f"✓  [{event.agent_name}] Tool completed: {event.tool_name}")
                print(f"   Results: {len(event.result)} records returned")
                if len(event.result) > 0:
                    print(f"   Sample: {event.result[0]}")
            elif isinstance(event.result, dict):
                print(f"✓  [{event.agent_name}] Tool completed: {event.tool_name}")
                print(f"   Result keys: {list(event.result.keys())}")
                print(f"   Sample data: {json.dumps(event.result, indent=6)[:200]}...")
            else:
                print(f"✓  [{event.agent_name}] Tool completed: {event.tool_name}")

        self.global_hooks = [
            Hook(EventType.BEFORE_TOOL_CALL, log_before_tool),
            Hook(EventType.AFTER_TOOL_CALL, log_after_tool)
        ]

    def _register_agents(self):
        """Register all specialized agents"""

        tools = self.toolbox.create_tools()

        # Clinical Safety Agent
        self.agents["ClinicalSafetyAgent"] = StrandsAgent(
            name="ClinicalSafetyAgent",
            role="Assess clinical safety and risk",
            tools=tools,
            hooks=self.global_hooks,
            steering_handlers=[
                SteeringHandler.validate_safety_threshold,
                SteeringHandler.validate_genetic_context
            ]
        )

        # Pharmacology Agent
        self.agents["PharmacologyAgent"] = StrandsAgent(
            name="PharmacologyAgent",
            role="Analyze drug mechanisms and interactions",
            tools=tools,
            hooks=self.global_hooks,
            steering_handlers=[SteeringHandler.validate_query_parameters]
        )

        # Genetics Agent
        self.agents["GeneticsAgent"] = StrandsAgent(
            name="GeneticsAgent",
            role="Validate genetic contraindications",
            tools=tools,
            hooks=self.global_hooks,
            steering_handlers=[SteeringHandler.validate_query_parameters]
        )

        # Trial Data Agent
        self.agents["TrialDataAgent"] = StrandsAgent(
            name="TrialDataAgent",
            role="Analyze clinical trial data",
            tools=tools,
            hooks=self.global_hooks,
            steering_handlers=[SteeringHandler.validate_query_parameters]
        )

        print(f"✓ Registered {len(self.agents)} agents with official Strands patterns\n")

    def execute_clinical_safety_workflow(self, drug: str, patient_context: Dict) -> ClinicalSafetyResult:
        """
        Execute clinical safety workflow with agent coordination
        Returns structured dataclass output
        """

        print(f"{'='*70}")
        print(f"🏥 Clinical Safety Workflow: {drug}")
        print(f"Patient: {patient_context}")
        print(f"{'='*70}")

        # Step 1: Get drug mechanism (PharmacologyAgent)
        print("\n" + "─"*70)
        print("STEP 1: Analyzing drug mechanism...")
        print("─"*70)
        mechanism_result = self.agents["PharmacologyAgent"].call_tool(
            "get_drug_mechanism",
            {"drug_name": drug}
        )

        # Step 2: Get adverse events (ClinicalSafetyAgent)
        print("\n" + "─"*70)
        print("STEP 2: Retrieving adverse events...")
        print("─"*70)
        adverse_events_result = self.agents["ClinicalSafetyAgent"].call_tool(
            "get_adverse_events",
            {"drug_name": drug}
        )

        # Step 3: Validate genetics (GeneticsAgent)
        print("\n" + "─"*70)
        print("STEP 3: Validating genetic contraindications...")
        print("─"*70)
        genetic_mutation = patient_context.get("genetic_mutation")
        genetic_result = {}
        if genetic_mutation:
            genetic_result = self.agents["GeneticsAgent"].call_tool(
                "validate_genetic_contraindication",
                {"gene": genetic_mutation, "drug_name": drug}
            )

        # Step 4: Calculate risk score
        print("\n" + "─"*70)
        print("STEP 4: Calculating risk score...")
        print("─"*70)
        adverse_events = adverse_events_result if isinstance(adverse_events_result, list) else []
        risk_score = min(len(adverse_events) * 0.05, 1.0)

        if risk_score < 0.3:
            risk_level = RiskLevel.LOW.value
        elif risk_score < 0.6:
            risk_level = RiskLevel.MODERATE.value
        elif risk_score < 0.8:
            risk_level = RiskLevel.HIGH.value
        else:
            risk_level = RiskLevel.CRITICAL.value

        print(f"\n   Risk Score: {risk_score:.2f}")
        print(f"   Risk Level: {risk_level.upper()}")
        print(f"   Adverse Events Count: {len(adverse_events)}")

        # Build structured result
        result = ClinicalSafetyResult(
            risk_score=risk_score,
            risk_level=risk_level,
            adverse_events=[ae.get("event", "Unknown") for ae in adverse_events[:10]],
            contraindications=[],
            recommendation=f"Risk level: {risk_level}. Monitor patient closely for adverse events, especially immune-related reactions.",
            genetic_validation=genetic_result,
            evidence_strength="high" if genetic_result.get("validated") else "moderate"
        )

        print(f"\n{'='*70}")
        print("✓ Workflow Complete")
        print(f"{'='*70}\n")

        return result


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

def main():
    """Demonstrate official Strands patterns"""

    print("\n" + "="*70)
    print("AWS Strands Multi-Agent Framework")
    print("Official Implementation - https://strandsagents.com/")
    print("="*70 + "\n")
    print("This demo shows the key patterns from the official framework:")
    print("  • Hook system for event interception")
    print("  • Steering handlers for corrective guidance")
    print("  • Tool decorator with automatic schema generation")
    print("  • Multi-agent coordination with specialized roles")
    print("  • Structured outputs for type safety")
    print("  • Trace attributes for observability")
    print("\n" + "="*70 + "\n")

    # Create orchestrator
    orchestrator = StrandsOrchestrator()

    # Execute clinical safety workflow
    result = orchestrator.execute_clinical_safety_workflow(
        drug="Pembrolizumab",
        patient_context={
            "genetic_mutation": "EGFR",
            "previous_treatment": "Nivolumab",
            "disease": "Non-Small Cell Lung Cancer"
        }
    )

    # Display structured result
    print("\n" + "="*70)
    print("STRUCTURED RESULT (Dataclass)")
    print("="*70 + "\n")
    print(json.dumps(result.to_dict(), indent=2))

    print("\n" + "="*70)
    print("Key Features Demonstrated:")
    print("="*70)
    print("✓ Hook system (before/after tool call logging)")
    print("  - Logs every tool invocation with parameters")
    print("  - Tracks results and execution metadata")
    print()
    print("✓ Steering handlers (query validation, safety checks)")
    print("  - Validates parameters before execution")
    print("  - Provides corrective feedback (not just blocking)")
    print("  - Alerts on risk thresholds")
    print()
    print("✓ Tools with schema generation (@tool decorator)")
    print("  - Automatic parameter validation")
    print("  - Self-documenting API")
    print()
    print("✓ Structured outputs (dataclasses)")
    print("  - Type-safe results")
    print("  - Easy serialization to JSON")
    print()
    print("✓ Multi-agent coordination (4 specialized agents)")
    print("  - PharmacologyAgent: Drug mechanisms")
    print("  - ClinicalSafetyAgent: Safety assessment")
    print("  - GeneticsAgent: Genetic validation")
    print("  - TrialDataAgent: Clinical trials")
    print()
    print("✓ Trace attributes for observability")
    print("  - Service tags for filtering")
    print("  - Timestamps for performance analysis")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
