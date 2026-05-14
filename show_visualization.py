#!/usr/bin/env python3
"""
Quick ASCII visualization of the Strands workflow
"""

def show_ascii_visualization():
    print("\n" + "="*80)
    print(" "*20 + "🏥 AWS STRANDS MULTI-AGENT WORKFLOW")
    print("="*80 + "\n")

    # Dashboard
    print("┌" + "─"*78 + "┐")
    print("│" + " "*28 + "📊 DASHBOARD" + " "*37 + "│")
    print("├" + "─"*19 + "┬" + "─"*19 + "┬" + "─"*19 + "┬" + "─"*19 + "┤")
    print("│  Total Hops: 3    │  Agents: 3        │  Duration: 0.0ms  │  Risk: 0.25       │")
    print("└" + "─"*19 + "┴" + "─"*19 + "┴" + "─"*19 + "┴" + "─"*19 + "┘")

    # Agents
    print("\n" + "="*80)
    print("🤖 ACTIVE AGENTS")
    print("="*80 + "\n")

    agents = [
        ("PharmacologyAgent", "Drug Mechanisms", 1),
        ("ClinicalSafetyAgent", "Safety Assessment", 1),
        ("GeneticsAgent", "Genetic Validation", 1)
    ]

    for name, role, tools in agents:
        print(f"┌─ {name}")
        print(f"│  Role: {role}")
        print(f"│  Tools Called: {tools}")
        print(f"│  Status: ✓ Active")
        print("└" + "─"*60 + "\n")

    # Workflow
    print("="*80)
    print("🔄 WORKFLOW EXECUTION (Hop-by-Hop)")
    print("="*80 + "\n")

    hops = [
        {
            "num": 1,
            "from": "Orchestrator",
            "to": "PharmacologyAgent",
            "tool": "get_drug_mechanism",
            "params": {"drug_name": "Pembrolizumab"},
            "time": "16:20:14.627"
        },
        {
            "num": 2,
            "from": "Orchestrator",
            "to": "ClinicalSafetyAgent",
            "tool": "get_adverse_events",
            "params": {"drug_name": "Pembrolizumab"},
            "time": "16:20:14.627"
        },
        {
            "num": 3,
            "from": "Orchestrator",
            "to": "GeneticsAgent",
            "tool": "validate_genetic_contraindication",
            "params": {"gene": "EGFR", "drug_name": "Pembrolizumab"},
            "time": "16:20:14.627"
        }
    ]

    for hop in hops:
        print(f"╔{'═'*76}╗")
        print(f"║  HOP {hop['num']}  {hop['to']} → {hop['tool']}")
        print(f"║  Time: {hop['time']}")
        print(f"╠{'═'*76}╣")
        print(f"║  From: {hop['from']:<67}║")
        print(f"║  To:   {hop['to']:<67}║")
        print(f"║  Tool: {hop['tool']:<67}║")
        print(f"║  Parameters: {str(hop['params']):<61}║")
        print(f"╚{'═'*76}╝\n")

    # Results
    print("="*80)
    print("📊 CLINICAL SAFETY ASSESSMENT RESULT")
    print("="*80 + "\n")

    print("┌─ Risk Level")
    print("│  ╔════════════════╗")
    print("│  ║  🟢 LOW RISK   ║")
    print("│  ╚════════════════╝")
    print("│")
    print("├─ Risk Score: 0.25/1.00")
    print("│")
    print("├─ Drug Mechanism")
    print("│  • PD-1 inhibitor - blocks programmed death receptor-1")
    print("│")
    print("├─ Protein Targets")
    print("│  • PD-1")
    print("│  • PD-L1")
    print("│")
    print("├─ Adverse Events Identified (5)")
    print("│  ⚠️  Immune-related pneumonitis (high severity, 10%)")
    print("│  ⚠️  Colitis (moderate severity, 8%)")
    print("│  ⚠️  Hepatitis (moderate severity, 5%)")
    print("│  ⚠️  Thyroid dysfunction (low severity, 12%)")
    print("│  ⚠️  Skin reactions (low severity, 15%)")
    print("│")
    print("└─ Genetic Validation")
    print("   ✓ EGFR mutation validated for Non-Small Cell Lung Cancer")
    print("")

    # Flow diagram
    print("="*80)
    print("🔀 AGENT COMMUNICATION FLOW")
    print("="*80 + "\n")

    print("                    ┌─────────────────┐")
    print("                    │  Orchestrator   │")
    print("                    └────────┬────────┘")
    print("                             │")
    print("            ┌────────────────┼────────────────┐")
    print("            │                │                │")
    print("            ▼                ▼                ▼")
    print("   ┌─────────────────┐ ┌──────────────┐ ┌────────────┐")
    print("   │ Pharmacology    │ │   Clinical   │ │  Genetics  │")
    print("   │     Agent       │ │Safety Agent  │ │   Agent    │")
    print("   └─────────────────┘ └──────────────┘ └────────────┘")
    print("           │                   │                │")
    print("           └───────────────────┴────────────────┘")
    print("                             │")
    print("                             ▼")
    print("                    ┌─────────────────┐")
    print("                    │  Final Result   │")
    print("                    │  Risk: LOW      │")
    print("                    └─────────────────┘")

    print("\n" + "="*80)
    print("✅ Workflow Complete!")
    print("="*80 + "\n")

    print("📄 Full HTML visualization available at: strands_visualization.html")
    print("   Open this file in your web browser for interactive features:")
    print("   • Animated agent cards with pulse effects")
    print("   • Click to expand hop details")
    print("   • View full JSON trace data")
    print("   • Responsive dashboard with statistics")
    print("")


if __name__ == "__main__":
    show_ascii_visualization()
