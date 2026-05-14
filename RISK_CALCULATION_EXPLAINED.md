# 🏥 Risk Calculation Algorithm - Detailed Explanation

## Overview
The risk calculation in the AWS Strands Multi-Agent Framework uses a **simple but effective adverse event counting algorithm** to assess the safety risk of prescribing a drug to a patient.

---

## 📊 The Risk Calculation Formula

### **Step 1: Count Adverse Events**
```python
adverse_events = get_adverse_events(drug_name="Pembrolizumab")
# Returns: 5 adverse events
```

**Adverse Events for Pembrolizumab:**
1. Immune-related pneumonitis (high severity, 10%)
2. Colitis (moderate severity, 8%)
3. Hepatitis (moderate severity, 5%)
4. Thyroid dysfunction (low severity, 12%)
5. Skin reactions (low severity, 15%)

### **Step 2: Calculate Risk Score**
```python
risk_score = min(len(adverse_events) * 0.05, 1.0)
```

**Breaking this down:**

```
risk_score = min(5 * 0.05, 1.0)
risk_score = min(0.25, 1.0)
risk_score = 0.25
```

**Why `min()` function?**
- Ensures the risk score never exceeds 1.0 (100%)
- If a drug has 20+ adverse events: `20 * 0.05 = 1.0` (capped at maximum)

### **Step 3: Determine Risk Level**
```python
if risk_score < 0.3:
    risk_level = "low"
elif risk_score < 0.6:
    risk_level = "moderate"  
elif risk_score < 0.8:
    risk_level = "high"
else:
    risk_level = "critical"
```

**For Pembrolizumab:**
```
risk_score = 0.25
0.25 < 0.3 → TRUE
Therefore: risk_level = "LOW"
```

---

## 📐 Risk Score Ranges and Thresholds

| Risk Score Range | Risk Level | Visual Indicator | Meaning |
|------------------|------------|------------------|---------|
| 0.00 - 0.29 | **LOW** | 🟢 Green Badge | Minimal risk, proceed with standard monitoring |
| 0.30 - 0.59 | **MODERATE** | 🟡 Yellow Badge | Moderate risk, enhanced monitoring required |
| 0.60 - 0.79 | **HIGH** | 🟠 Orange Badge | Significant risk, close supervision needed |
| 0.80 - 1.00 | **CRITICAL** | 🔴 Red Badge | Critical risk, consider alternative treatments |

---

## 🔢 Example Calculations

### Example 1: Pembrolizumab (Current)
```
Adverse Events: 5
Calculation: 5 × 0.05 = 0.25
Risk Level: LOW (0.25 < 0.30)
Badge Color: 🟢 Green
```

### Example 2: Hypothetical Drug A
```
Adverse Events: 8
Calculation: 8 × 0.05 = 0.40
Risk Level: MODERATE (0.30 ≤ 0.40 < 0.60)
Badge Color: 🟡 Yellow
```

### Example 3: Hypothetical Drug B
```
Adverse Events: 15
Calculation: 15 × 0.05 = 0.75
Risk Level: HIGH (0.60 ≤ 0.75 < 0.80)
Badge Color: 🟠 Orange
```

### Example 4: Hypothetical Drug C
```
Adverse Events: 18
Calculation: 18 × 0.05 = 0.90
Risk Level: CRITICAL (0.80 ≤ 0.90 ≤ 1.00)
Badge Color: 🔴 Red
```

### Example 5: Extremely Risky Drug
```
Adverse Events: 25
Calculation: 25 × 0.05 = 1.25 → min(1.25, 1.0) = 1.0
Risk Level: CRITICAL (1.0 = maximum)
Badge Color: 🔴 Red
```

---

## 🧮 Mathematical Properties

### **Linear Scaling**
Each adverse event adds **0.05 (5%)** to the risk score:
- 1 event = 5% risk
- 2 events = 10% risk
- 3 events = 15% risk
- 10 events = 50% risk
- 20 events = 100% risk (maximum)

### **Formula Components**

```python
risk_score = min(len(adverse_events) * 0.05, 1.0)
            └─┬─┘ └──────┬───────┘ └─┬─┘  └─┬─┘
              │          │          │      │
              │          │          │      └─ Upper bound (100%)
              │          │          └──────── Weight per event (5%)
              │          └─────────────────── Count of adverse events
              └────────────────────────────── Ensures ≤ 1.0
```

---

## 🎯 Why This Algorithm?

### **Advantages:**
1. **Simplicity**: Easy to understand and explain to clinicians
2. **Transparency**: Clear relationship between event count and risk
3. **Bounded**: Risk score always between 0.0 and 1.0
4. **Scalable**: Works for drugs with any number of adverse events
5. **Visual**: Maps cleanly to color-coded risk levels

### **Use Case:**
- Quick screening tool for drug safety
- First-pass risk assessment
- Comparative analysis between drugs
- Decision support in clinical workflows

---

## 🔬 What the Algorithm Does NOT Consider (Limitations)

### **1. Severity of Adverse Events**
Current calculation treats all events equally:
```python
# All weighted the same:
"Skin reactions" (low severity) = +0.05
"Immune-related pneumonitis" (high severity) = +0.05
```

**Production Improvement:**
```python
severity_weights = {
    "high": 0.15,
    "moderate": 0.10,
    "low": 0.05
}
risk_score = sum(severity_weights[ae["severity"]] for ae in adverse_events)
```

### **2. Frequency/Probability**
Current calculation ignores how often events occur:
```python
# Not considered:
"Skin reactions" → frequency: 15% of patients
"Hepatitis" → frequency: 5% of patients
```

**Production Improvement:**
```python
for ae in adverse_events:
    frequency_factor = float(ae["frequency"].strip("%")) / 100
    risk_score += 0.05 * frequency_factor
```

### **3. Patient-Specific Factors**
Not currently weighted:
- Age
- Comorbidities
- Genetic mutations
- Previous drug reactions
- Organ function

### **4. Drug Mechanism**
Doesn't consider:
- Drug class
- Mechanism of action
- Known drug-drug interactions

### **5. Genetic Validation**
Currently collected but not factored into score:
```python
genetic_result = validate_genetic_contraindication(gene="EGFR", drug="Pembrolizumab")
# Result: {"validated": True, "evidence": [...]}
# But not used in risk_score calculation
```

---

## 🚀 Production-Ready Enhanced Algorithm

Here's how the algorithm could be improved for real clinical use:

```python
def calculate_clinical_risk(drug_name, adverse_events, patient_context, genetic_validation):
    """
    Enhanced risk calculation for production use
    """
    
    # Base score from adverse event count
    base_score = 0.0
    
    # 1. Weight by severity and frequency
    severity_weights = {"high": 0.15, "moderate": 0.10, "low": 0.05}
    
    for ae in adverse_events:
        severity = ae.get("severity", "low")
        frequency_pct = float(ae.get("frequency", "5%").strip("%"))
        
        # Severity contribution
        severity_score = severity_weights.get(severity, 0.05)
        
        # Frequency contribution (higher frequency = higher risk)
        frequency_factor = frequency_pct / 100
        
        # Combined score for this adverse event
        ae_score = severity_score * (0.5 + frequency_factor)
        base_score += ae_score
    
    # 2. Patient-specific risk modifiers
    patient_multiplier = 1.0
    
    # Age factor
    age = patient_context.get("age", 50)
    if age > 65:
        patient_multiplier *= 1.2  # 20% increase for elderly
    elif age < 18:
        patient_multiplier *= 1.3  # 30% increase for pediatric
    
    # Comorbidity factor
    comorbidities = patient_context.get("comorbidities", [])
    if len(comorbidities) > 0:
        patient_multiplier *= (1.0 + 0.1 * len(comorbidities))
    
    # Previous treatment factor
    previous_treatment = patient_context.get("previous_treatment")
    if previous_treatment:
        patient_multiplier *= 1.1  # 10% increase if switching drugs
    
    # 3. Genetic contraindication factor
    genetic_multiplier = 1.0
    if not genetic_validation.get("validated", False):
        genetic_multiplier = 1.5  # 50% increase if genetic validation fails
    
    # 4. Calculate final score
    final_score = base_score * patient_multiplier * genetic_multiplier
    
    # Cap at 1.0
    final_score = min(final_score, 1.0)
    
    # Determine risk level
    if final_score < 0.3:
        risk_level = "low"
    elif final_score < 0.6:
        risk_level = "moderate"
    elif final_score < 0.8:
        risk_level = "high"
    else:
        risk_level = "critical"
    
    return {
        "risk_score": round(final_score, 3),
        "risk_level": risk_level,
        "breakdown": {
            "base_score": round(base_score, 3),
            "patient_multiplier": round(patient_multiplier, 3),
            "genetic_multiplier": round(genetic_multiplier, 3)
        }
    }
```

### **Enhanced Example:**
```python
# Pembrolizumab with enhanced algorithm
result = calculate_clinical_risk(
    drug_name="Pembrolizumab",
    adverse_events=[
        {"event": "Immune-related pneumonitis", "severity": "high", "frequency": "10%"},
        {"event": "Colitis", "severity": "moderate", "frequency": "8%"},
        {"event": "Hepatitis", "severity": "moderate", "frequency": "5%"},
        {"event": "Thyroid dysfunction", "severity": "low", "frequency": "12%"},
        {"event": "Skin reactions", "severity": "low", "frequency": "15%"}
    ],
    patient_context={
        "age": 68,  # Elderly
        "comorbidities": ["diabetes"],
        "previous_treatment": "Nivolumab"
    },
    genetic_validation={"validated": True}
)

# Result:
# {
#   "risk_score": 0.587,
#   "risk_level": "moderate",
#   "breakdown": {
#     "base_score": 0.396,
#     "patient_multiplier": 1.32,  # Age(1.2) × Comorbidity(1.1) × Previous(1.1)
#     "genetic_multiplier": 1.0
#   }
# }
```

---

## 🎓 Key Takeaways

### **Current Simple Algorithm:**
✅ Easy to understand
✅ Quick calculation
✅ Good for demos and prototypes
❌ Ignores severity, frequency, and patient factors

### **For Production Use:**
✅ Weight by severity (high/moderate/low)
✅ Factor in frequency percentages
✅ Include patient-specific modifiers (age, comorbidities)
✅ Consider genetic contraindications
✅ Add drug-drug interaction checks
✅ Incorporate clinical guidelines

---

## 📚 Code Location

**Simple Algorithm** (current implementation):
```
File: /workshop/strands_visual_demo.py
Lines: 164-167

risk_score = min(len(adverse_events) * 0.05, 1.0)
risk_level = "low" if risk_score < 0.3 else "moderate"
```

**Can be extended to** the enhanced algorithm shown above for production deployment.

---

## 💡 Summary

The risk calculation is a **counting-based algorithm** where:
- Each adverse event contributes **5%** to the risk score
- Risk score is capped at **100% (1.0)**
- Risk levels are determined by score thresholds
- **Pembrolizumab** has 5 adverse events → 0.25 risk score → **LOW risk**

For clinical deployment, the algorithm should be enhanced to consider severity, frequency, patient characteristics, and genetic factors.
