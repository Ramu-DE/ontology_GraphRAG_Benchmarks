#!/usr/bin/env python3
"""
AWS Strands Multi-Agent Framework - Production-Grade Risk Assessment
Implements comprehensive clinical safety calculation with:
- Severity weighting
- Frequency factors
- Patient demographics (age, comorbidities)
- Genetic contraindications
- Drug-drug interactions
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum


# ============================================================================
# ENHANCED SIMULATED DATA (Production-Grade)
# ============================================================================

SIMULATED_DATA = {
    "Pembrolizumab": {
        "mechanism": "PD-1 inhibitor - blocks programmed death receptor-1",
        "targets": ["PD-1", "PD-L1"],
        "drug_class": "Immune checkpoint inhibitor",
        "adverse_events": [
            {"event": "Immune-related pneumonitis", "severity": "high", "frequency": 10.0},
            {"event": "Colitis", "severity": "moderate", "frequency": 8.0},
            {"event": "Hepatitis", "severity": "moderate", "frequency": 5.0},
            {"event": "Thyroid dysfunction", "severity": "low", "frequency": 12.0},
            {"event": "Skin reactions", "severity": "low", "frequency": 15.0},
        ],
        "genetic_validation": {
            "EGFR": {
                "validated": True,
                "confidence": 0.95,
                "evidence_count": 3,
                "evidence": [
                    {"gene": "EGFR", "disease": "Non-Small Cell Lung Cancer", "status": "validated"}
                ]
            }
        },
        "interactions": {
            "Nivolumab": {
                "severity": "moderate",
                "description": "Increased risk of immune-related adverse events when switching between checkpoint inhibitors",
                "risk_increase": 0.15
            }
        }
    }
}

# Drug interaction database
DRUG_INTERACTIONS = {
    ("Pembrolizumab", "Nivolumab"): {
        "severity": "moderate",
        "description": "Similar mechanisms - increased autoimmune risk",
        "risk_multiplier": 1.15
    },
    ("Pembrolizumab", "Warfarin"): {
        "severity": "high",
        "description": "Potential bleeding complications",
        "risk_multiplier": 1.25
    }
}


# ============================================================================
# PRODUCTION-GRADE RISK CALCULATOR
# ============================================================================

@dataclass
class RiskBreakdown:
    """Detailed risk calculation breakdown"""
    base_score: float
    severity_weighted_score: float
    frequency_adjusted_score: float
    age_multiplier: float
    comorbidity_multiplier: float
    genetic_multiplier: float
    interaction_multiplier: float
    final_score: float
    risk_level: str
    factors_applied: List[str]


class ProductionRiskCalculator:
    """Production-grade risk calculation engine"""

    # Severity weights
    SEVERITY_WEIGHTS = {
        "critical": 0.25,
        "high": 0.15,
        "moderate": 0.10,
        "low": 0.05
    }

    # Risk level thresholds
    RISK_THRESHOLDS = [
        (0.30, "low"),
        (0.60, "moderate"),
        (0.80, "high"),
        (float('inf'), "critical")
    ]

    @classmethod
    def calculate_comprehensive_risk(cls,
                                     drug_name: str,
                                     adverse_events: List[Dict],
                                     patient_context: Dict,
                                     genetic_validation: Dict,
                                     drug_interactions: List[Dict]) -> RiskBreakdown:
        """
        Calculate comprehensive risk score with all production factors
        """
        factors_applied = []

        # ===================================================================
        # STEP 1: Base Score (Simple Count)
        # ===================================================================
        base_score = len(adverse_events) * 0.05

        # ===================================================================
        # STEP 2: Severity-Weighted Score
        # ===================================================================
        severity_score = 0.0
        for ae in adverse_events:
            severity = ae.get("severity", "low")
            weight = cls.SEVERITY_WEIGHTS.get(severity, 0.05)
            severity_score += weight

        factors_applied.append(f"Severity weighting applied")

        # ===================================================================
        # STEP 3: Frequency Adjustment
        # ===================================================================
        frequency_score = 0.0
        for ae in adverse_events:
            severity = ae.get("severity", "low")
            weight = cls.SEVERITY_WEIGHTS.get(severity, 0.05)
            frequency_pct = ae.get("frequency", 5.0)  # Default 5%

            # Frequency factor: higher frequency = higher weight
            frequency_factor = 0.5 + (frequency_pct / 100)
            frequency_score += weight * frequency_factor

        factors_applied.append(f"Frequency weighting applied ({len(adverse_events)} events)")

        # ===================================================================
        # STEP 4: Age Factor
        # ===================================================================
        age_multiplier = 1.0
        age = patient_context.get("age", 50)

        if age > 75:
            age_multiplier = 1.30  # 30% increase for very elderly
            factors_applied.append(f"Elderly risk factor (age {age}): +30%")
        elif age > 65:
            age_multiplier = 1.20  # 20% increase for elderly
            factors_applied.append(f"Elderly risk factor (age {age}): +20%")
        elif age < 18:
            age_multiplier = 1.25  # 25% increase for pediatric
            factors_applied.append(f"Pediatric risk factor (age {age}): +25%")

        # ===================================================================
        # STEP 5: Comorbidity Factor
        # ===================================================================
        comorbidity_multiplier = 1.0
        comorbidities = patient_context.get("comorbidities", [])

        if len(comorbidities) > 0:
            # Each comorbidity adds 10%, max 50%
            comorbidity_increase = min(0.1 * len(comorbidities), 0.5)
            comorbidity_multiplier = 1.0 + comorbidity_increase
            factors_applied.append(
                f"Comorbidity factor ({len(comorbidities)} conditions): +{int(comorbidity_increase*100)}%"
            )

        # ===================================================================
        # STEP 6: Genetic Contraindication Factor
        # ===================================================================
        genetic_multiplier = 1.0

        if genetic_validation:
            validated = genetic_validation.get("validated", False)
            confidence = genetic_validation.get("confidence", 0.5)

            if not validated:
                genetic_multiplier = 1.50  # 50% increase if not validated
                factors_applied.append("Genetic validation FAILED: +50%")
            elif confidence < 0.7:
                genetic_multiplier = 1.15  # 15% increase for low confidence
                factors_applied.append(f"Genetic validation low confidence ({confidence:.2f}): +15%")
            else:
                factors_applied.append(f"Genetic validation PASSED (confidence: {confidence:.2f})")

        # ===================================================================
        # STEP 7: Drug-Drug Interaction Factor
        # ===================================================================
        interaction_multiplier = 1.0

        if drug_interactions:
            for interaction in drug_interactions:
                severity = interaction.get("severity", "low")
                multiplier = interaction.get("risk_multiplier", 1.0)

                interaction_multiplier *= multiplier
                factors_applied.append(
                    f"Drug interaction ({interaction.get('description', 'Unknown')}): +{int((multiplier-1)*100)}%"
                )

        # ===================================================================
        # STEP 8: Previous Treatment Factor
        # ===================================================================
        previous_treatment = patient_context.get("previous_treatment")
        if previous_treatment:
            # Switching treatments increases risk by 10%
            age_multiplier *= 1.10
            factors_applied.append(f"Treatment switch from {previous_treatment}: +10%")

        # ===================================================================
        # STEP 9: Calculate Final Score
        # ===================================================================
        final_score = (
            frequency_score *
            age_multiplier *
            comorbidity_multiplier *
            genetic_multiplier *
            interaction_multiplier
        )

        # Cap at 1.0
        final_score = min(final_score, 1.0)

        # Determine risk level
        risk_level = "critical"
        for threshold, level in cls.RISK_THRESHOLDS:
            if final_score < threshold:
                risk_level = level
                break

        return RiskBreakdown(
            base_score=round(base_score, 3),
            severity_weighted_score=round(severity_score, 3),
            frequency_adjusted_score=round(frequency_score, 3),
            age_multiplier=round(age_multiplier, 3),
            comorbidity_multiplier=round(comorbidity_multiplier, 3),
            genetic_multiplier=round(genetic_multiplier, 3),
            interaction_multiplier=round(interaction_multiplier, 3),
            final_score=round(final_score, 3),
            risk_level=risk_level,
            factors_applied=factors_applied
        )


# ============================================================================
# VISUALIZATION TRACKING
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


# ============================================================================
# PRODUCTION-GRADE AGENTS
# ============================================================================

class ProductionAgent:
    """Agent with tracking for visualization"""

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

def execute_production_workflow(patient_context: Dict):
    """Execute production-grade workflow with comprehensive risk assessment"""

    tracker = VisualizationTracker()

    # Create specialized agents
    pharma_agent = ProductionAgent("PharmacologyAgent", "Drug Mechanisms", tracker)
    safety_agent = ProductionAgent("ClinicalSafetyAgent", "Safety Assessment", tracker)
    genetics_agent = ProductionAgent("GeneticsAgent", "Genetic Validation", tracker)
    interaction_agent = ProductionAgent("DrugInteractionAgent", "Drug Interactions", tracker)
    patient_agent = ProductionAgent("PatientProfileAgent", "Patient Analysis", tracker)

    drug = "Pembrolizumab"

    print(f"\n{'='*80}")
    print(f"🏥 PRODUCTION-GRADE CLINICAL SAFETY WORKFLOW")
    print(f"{'='*80}\n")

    # ========================================================================
    # HOP 1: Patient Profile Analysis
    # ========================================================================
    print("HOP 1: Analyzing patient profile...")

    def analyze_patient(context: Dict):
        return {
            "age": context.get("age", 50),
            "comorbidities": context.get("comorbidities", []),
            "genetic_mutation": context.get("genetic_mutation"),
            "previous_treatment": context.get("previous_treatment"),
            "risk_factors": []
        }

    patient_profile = patient_agent.call_tool("analyze_patient_profile",
                                              analyze_patient,
                                              {"context": patient_context})

    # ========================================================================
    # HOP 2: Drug Mechanism Analysis
    # ========================================================================
    print("HOP 2: Analyzing drug mechanism...")

    def get_mechanism(drug_name: str):
        return SIMULATED_DATA[drug_name]

    mechanism = pharma_agent.call_tool("get_drug_mechanism", get_mechanism, {"drug_name": drug})

    # ========================================================================
    # HOP 3: Adverse Events Retrieval
    # ========================================================================
    print("HOP 3: Retrieving adverse events with severity and frequency...")

    def get_adverse_events(drug_name: str):
        return SIMULATED_DATA[drug_name]["adverse_events"]

    adverse_events = safety_agent.call_tool("get_adverse_events_detailed",
                                           get_adverse_events,
                                           {"drug_name": drug})

    # ========================================================================
    # HOP 4: Genetic Validation
    # ========================================================================
    print("HOP 4: Validating genetic contraindications...")

    def validate_genetics(gene: str, drug_name: str):
        return SIMULATED_DATA[drug_name]["genetic_validation"].get(gene, {})

    genetic_result = genetics_agent.call_tool("validate_genetic_contraindication",
                                              validate_genetics,
                                              {"gene": patient_context.get("genetic_mutation", "EGFR"),
                                               "drug_name": drug})

    # ========================================================================
    # HOP 5: Drug-Drug Interaction Check
    # ========================================================================
    print("HOP 5: Checking drug-drug interactions...")

    def check_interactions(current_drug: str, previous_drug: str):
        key = (current_drug, previous_drug)
        if key in DRUG_INTERACTIONS:
            return [DRUG_INTERACTIONS[key]]
        return []

    interactions = interaction_agent.call_tool("check_drug_interactions",
                                               check_interactions,
                                               {"current_drug": drug,
                                                "previous_drug": patient_context.get("previous_treatment", "")})

    # ========================================================================
    # STEP 6: Calculate Production-Grade Risk
    # ========================================================================
    print("\n" + "="*80)
    print("📊 CALCULATING COMPREHENSIVE RISK SCORE...")
    print("="*80 + "\n")

    risk_breakdown = ProductionRiskCalculator.calculate_comprehensive_risk(
        drug_name=drug,
        adverse_events=adverse_events,
        patient_context=patient_context,
        genetic_validation=genetic_result,
        drug_interactions=interactions
    )

    # ========================================================================
    # STEP 7: Simple Algorithm Comparison
    # ========================================================================
    simple_risk_score = min(len(adverse_events) * 0.05, 1.0)
    simple_risk_level = "low" if simple_risk_score < 0.3 else "moderate"

    result = {
        "drug_name": drug,
        "mechanism": mechanism["mechanism"],
        "targets": mechanism["targets"],
        "patient_profile": patient_profile,
        "adverse_events": adverse_events,
        "genetic_validation": genetic_result,
        "drug_interactions": interactions,
        "risk_assessment": {
            "simple_algorithm": {
                "risk_score": simple_risk_score,
                "risk_level": simple_risk_level,
                "methodology": "Count-based (5% per event)"
            },
            "production_algorithm": {
                "risk_score": risk_breakdown.final_score,
                "risk_level": risk_breakdown.risk_level,
                "breakdown": asdict(risk_breakdown),
                "methodology": "Multi-factor weighted scoring"
            }
        }
    }

    return tracker, result, risk_breakdown


# ============================================================================
# RESULTS DISPLAY
# ============================================================================

def display_results(result: Dict, risk_breakdown: RiskBreakdown):
    """Display comprehensive results"""

    print("\n" + "="*80)
    print("📊 RISK ASSESSMENT COMPARISON")
    print("="*80 + "\n")

    # Simple Algorithm
    simple = result["risk_assessment"]["simple_algorithm"]
    print("┌─ SIMPLE ALGORITHM (Demo)")
    print("│")
    print(f"│  Risk Score:  {simple['risk_score']:.3f}")
    print(f"│  Risk Level:  {simple['risk_level'].upper()}")
    print(f"│  Methodology: {simple['methodology']}")
    print("│")
    print("└─ ⚠️  Does NOT consider: severity, frequency, patient factors")
    print("")

    # Production Algorithm
    prod = result["risk_assessment"]["production_algorithm"]
    print("┌─ PRODUCTION ALGORITHM (Clinical-Grade)")
    print("│")
    print(f"│  Risk Score:  {prod['risk_score']:.3f}")
    print(f"│  Risk Level:  {prod['risk_level'].upper()}")
    print(f"│  Methodology: {prod['methodology']}")
    print("│")
    print("├─ CALCULATION BREAKDOWN:")
    print(f"│  • Base Score (count):           {risk_breakdown.base_score:.3f}")
    print(f"│  • Severity-Weighted:            {risk_breakdown.severity_weighted_score:.3f}")
    print(f"│  • Frequency-Adjusted:           {risk_breakdown.frequency_adjusted_score:.3f}")
    print(f"│  • Age Multiplier:               {risk_breakdown.age_multiplier:.3f}x")
    print(f"│  • Comorbidity Multiplier:       {risk_breakdown.comorbidity_multiplier:.3f}x")
    print(f"│  • Genetic Multiplier:           {risk_breakdown.genetic_multiplier:.3f}x")
    print(f"│  • Interaction Multiplier:       {risk_breakdown.interaction_multiplier:.3f}x")
    print("│")
    print("├─ FACTORS APPLIED:")
    for i, factor in enumerate(risk_breakdown.factors_applied, 1):
        print(f"│  {i}. {factor}")
    print("│")
    print("└─ ✅ Comprehensive clinical safety assessment")
    print("")

    # Impact Analysis
    diff = prod['risk_score'] - simple['risk_score']
    diff_pct = (diff / simple['risk_score']) * 100 if simple['risk_score'] > 0 else 0

    print("="*80)
    print("⚡ IMPACT ANALYSIS")
    print("="*80)
    print(f"\nRisk Score Difference: {diff:+.3f} ({diff_pct:+.1f}%)")

    if prod['risk_level'] != simple['risk_level']:
        print(f"Risk Level Changed: {simple['risk_level'].upper()} → {prod['risk_level'].upper()}")
        print("⚠️  This could change the clinical decision!")
    else:
        print(f"Risk Level: {prod['risk_level'].upper()} (consistent)")

    print("")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run production-grade workflow"""

    # Patient context
    patient_context = {
        "age": 68,
        "comorbidities": ["diabetes", "hypertension"],
        "genetic_mutation": "EGFR",
        "previous_treatment": "Nivolumab",
        "disease": "Non-Small Cell Lung Cancer"
    }

    print("\n" + "="*80)
    print("🏥 AWS STRANDS - PRODUCTION-GRADE RISK ASSESSMENT")
    print("="*80)
    print("\nPatient Profile:")
    for key, value in patient_context.items():
        print(f"  • {key}: {value}")
    print("")

    # Execute workflow
    tracker, result, risk_breakdown = execute_production_workflow(patient_context)

    # Display results
    display_results(result, risk_breakdown)

    # Save detailed results
    output_file = "production_risk_assessment.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print("="*80)
    print(f"✅ Complete assessment saved to: {output_file}")
    print("="*80)
    print("")

    print("Total Hops: ", len(tracker.hops))
    print("Active Agents:", len(tracker.agents))
    print("")


if __name__ == "__main__":
    main()
