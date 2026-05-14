# 🏥 AWS Strands Visualization Preview

## 📊 What the HTML Visualization Looks Like

### Header Section
```
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║              🏥 AWS Strands Multi-Agent Framework                        ║
║              Clinical Safety Workflow Visualization                     ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

### Dashboard Cards (Grid Layout)
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Total Hops     │  │  Active Agents  │  │  Total Duration │  │  Risk Score     │
│                 │  │                 │  │                 │  │                 │
│       3         │  │       3         │  │     0.0ms       │  │      0.25       │
│  Agent          │  │  Specialized    │  │  Execution time │  │  Safety         │
│  interactions   │  │  agents         │  │                 │  │  assessment     │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
    [Hover effect: cards lift up with shadow]
```

### Active Agents Section (Animated Cards with Purple Gradient)
```
╔════════════════════════════════════════════════════════════════════════════╗
║  🤖 Active Agents                                                          ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌────────────────────────────┐  ┌────────────────────────────┐          ║
║  │ [Purple Gradient Card]     │  │ [Purple Gradient Card]     │          ║
║  │ [Pulsing Animation]        │  │ [Pulsing Animation]        │          ║
║  │                            │  │                            │          ║
║  │  PharmacologyAgent         │  │  ClinicalSafetyAgent       │          ║
║  │  Drug Mechanisms           │  │  Safety Assessment         │          ║
║  │                            │  │                            │          ║
║  │  Tools Called: 1           │  │  Tools Called: 1           │          ║
║  │  Status: ✓ Active          │  │  Status: ✓ Active          │          ║
║  └────────────────────────────┘  └────────────────────────────┘          ║
║                                                                            ║
║  ┌────────────────────────────┐                                           ║
║  │ [Purple Gradient Card]     │                                           ║
║  │ [Pulsing Animation]        │                                           ║
║  │                            │                                           ║
║  │  GeneticsAgent             │                                           ║
║  │  Genetic Validation        │                                           ║
║  │                            │                                           ║
║  │  Tools Called: 1           │                                           ║
║  │  Status: ✓ Active          │                                           ║
║  └────────────────────────────┘                                           ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Workflow Execution (Hop-by-Hop) - Expandable
```
╔════════════════════════════════════════════════════════════════════════════╗
║  🔄 Workflow Execution (Hop-by-Hop)                                        ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │ ① PharmacologyAgent → get_drug_mechanism    16:20:14.627 (0.00ms)  │  ║
║  ├─────────────────────────────────────────────────────────────────────┤  ║
║  │  From Agent: Orchestrator                                           │  ║
║  │  To Agent:   PharmacologyAgent                                      │  ║
║  │  Tool:       get_drug_mechanism                                     │  ║
║  │  Duration:   0.00ms                                                 │  ║
║  │                                                                     │  ║
║  │  [Show Details] ◄── Click to expand parameters                     │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │ ② ClinicalSafetyAgent → get_adverse_events  16:20:14.627 (0.00ms)  │  ║
║  ├─────────────────────────────────────────────────────────────────────┤  ║
║  │  From Agent: Orchestrator                                           │  ║
║  │  To Agent:   ClinicalSafetyAgent                                    │  ║
║  │  Tool:       get_adverse_events                                     │  ║
║  │  Duration:   0.00ms                                                 │  ║
║  │                                                                     │  ║
║  │  [Show Details] ◄── Click to expand parameters                     │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │ ③ GeneticsAgent → validate_genetic_contraindication                │  ║
║  │                                              16:20:14.627 (0.00ms)  │  ║
║  ├─────────────────────────────────────────────────────────────────────┤  ║
║  │  From Agent: Orchestrator                                           │  ║
║  │  To Agent:   GeneticsAgent                                          │  ║
║  │  Tool:       validate_genetic_contraindication                      │  ║
║  │  Duration:   0.00ms                                                 │  ║
║  │                                                                     │  ║
║  │  [Show Details] ◄── Click to expand parameters                     │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Clinical Safety Assessment Result
```
╔════════════════════════════════════════════════════════════════════════════╗
║  📊 Clinical Safety Assessment Result                                      ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Risk Level:  ╔════════════════╗                                          ║
║               ║  🟢 LOW RISK   ║  ◄── Green badge                         ║
║               ╚════════════════╝                                          ║
║                                                                            ║
║  Risk Score: 0.25/1.00                                                     ║
║                                                                            ║
║  Drug Mechanism:                                                           ║
║  • PD-1 inhibitor - blocks programmed death receptor-1                    ║
║                                                                            ║
║  Protein Targets:                                                          ║
║  • PD-1, PD-L1                                                             ║
║                                                                            ║
║  Adverse Events Identified:                                                ║
║  ┌──────────────────────────┐  ┌──────────────────────────┐              ║
║  │ Immune-related           │  │ Colitis                  │              ║
║  │ pneumonitis              │  │                          │              ║
║  └──────────────────────────┘  └──────────────────────────┘              ║
║  ┌──────────────────────────┐  ┌──────────────────────────┐              ║
║  │ Hepatitis                │  │ Thyroid dysfunction      │              ║
║  └──────────────────────────┘  └──────────────────────────┘              ║
║  ┌──────────────────────────┐                                             ║
║  │ Skin reactions           │                                             ║
║  └──────────────────────────┘                                             ║
║                                                                            ║
║  Genetic Validation:                                                       ║
║  Status: ✓ Validated                                                       ║
║                                                                            ║
║  [Show Full JSON Result]  ◄── Click to expand                             ║
║  [Show Full Trace Data]   ◄── Click to expand                             ║
╚════════════════════════════════════════════════════════════════════════════╝
```

## 🎨 Visual Features

### Colors & Design
- **Background**: Purple-blue gradient (linear-gradient(135deg, #667eea 0%, #764ba2 100%))
- **Cards**: White with rounded corners and shadow effects
- **Agent Cards**: Purple gradient with pulsing animation
- **Risk Badge**: Green for LOW (🟢), Yellow for MODERATE (🟡), Red for HIGH (🔴)
- **Adverse Events**: Light gray boxes with red left border

### Animations
1. **Agent Cards**: Continuous pulse effect (scale 1.0 → 1.1)
2. **Hops**: Slide-in animation from left
3. **Cards**: Lift up on hover with shadow

### Interactive Elements
- **"Show Details" buttons**: Expand JSON parameters for each hop
- **"Show Full JSON Result" button**: View complete result object
- **"Show Full Trace Data" button**: View complete trace with all hops

### Responsive Design
- Grid layouts automatically adjust to screen size
- Minimum card widths ensure readability
- Mobile-friendly (stacks vertically on small screens)

## 📂 File Information

**Location**: `/workshop/strands_visualization.html`
**Size**: 21KB
**Type**: Standalone HTML (no external dependencies)
**Browser Support**: All modern browsers (Chrome, Firefox, Safari, Edge)

## 🚀 How to Use

1. **Download** the file from `/workshop/strands_visualization.html`
2. **Open** it in any web browser (just double-click)
3. **Interact**: Click buttons to expand details
4. **No server needed** - it's a completely standalone file

## 📸 Screenshot Description

If you could see the actual rendered page, you would see:
- A beautiful purple gradient filling the entire background
- White cards "floating" with shadows
- Purple animated agent cards that gently pulse
- A clean, professional medical/clinical aesthetic
- Clear typography with good spacing
- Green "LOW RISK" badge prominently displayed
- Grid of adverse event cards
- Interactive buttons in purple that turn darker on hover

---

**The visualization is production-ready and can be shared with stakeholders!**
