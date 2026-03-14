# ================================
# HUMAN JUSTIFICATION SYSTEM (HJS)
# Single File Implementation
# ================================

from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from datetime import datetime

# -------------------------------
# DATABASE (Audit Trail Storage)
# -------------------------------
conn = sqlite3.connect("hjs.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    score REAL,
    decision TEXT,
    reasons TEXT,
    timestamp TEXT
)
""")
conn.commit()

def save_decision(name, score, decision, reasons):
    cursor.execute("""
    INSERT INTO decisions (name, score, decision, reasons, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (name, score, decision, reasons, datetime.now()))
    conn.commit()

# -------------------------------
# INPUT MODEL
# -------------------------------
class Applicant(BaseModel):
    name: str
    experience: float      # years
    skill_match: float     # %
    test_score: float      # out of 100
    stability: float       # years in job

# -------------------------------
# DECISION ENGINE (Explainable)
# -------------------------------
def evaluate(applicant):
    # Feature weights (configurable)
    weights = {
        "experience": 0.30,
        "skill_match": 0.25,
        "test_score": 0.25,
        "stability": 0.20
    }

    # Required thresholds
    thresholds = {
        "experience": 2,
        "skill_match": 70,
        "test_score": 60,
        "stability": 1
    }

    # Score Calculation (Transparent Formula)
    score = (
        (applicant.experience / 5) * 100 * weights["experience"] +
        applicant.skill_match * weights["skill_match"] +
        applicant.test_score * weights["test_score"] +
        (applicant.stability / 3) * 100 * weights["stability"]
    )

    return score, thresholds

# -------------------------------
# JUSTIFICATION ENGINE
# -------------------------------
def generate_explanation(applicant, score, thresholds):
    rejection_reasons = []
    impact_analysis = []

    def add_reason(field, actual, required, weight):
        gap = required - actual
        impact = round(gap * weight, 2)
        rejection_reasons.append(
            f"{field} is {actual}, below required {required}"
        )
        impact_analysis.append((field, impact))

    if applicant.experience < thresholds["experience"]:
        add_reason("Experience (years)", applicant.experience,
                   thresholds["experience"], 0.30)

    if applicant.skill_match < thresholds["skill_match"]:
        add_reason("Skill Match (%)", applicant.skill_match,
                   thresholds["skill_match"], 0.25)

    if applicant.test_score < thresholds["test_score"]:
        add_reason("Assessment Score", applicant.test_score,
                   thresholds["test_score"], 0.25)

    if applicant.stability < thresholds["stability"]:
        add_reason("Job Stability (years)", applicant.stability,
                   thresholds["stability"], 0.20)

    decision = "ACCEPTED" if score >= 65 else "REJECTED"

    # -----------------------
    # Explanation Levels
    # -----------------------

    # Level 1 — Human Friendly
    summary = f"Application {decision}. Suitability Score = {round(score,2)}."

    # Level 2 — Professional Explanation
    if rejection_reasons:
        detailed = summary + "\nReasons:\n- " + "\n- ".join(rejection_reasons)
    else:
        detailed = summary + "\nAll evaluation criteria satisfied."

    # Level 3 — Audit Mode
    audit = {
        "final_score": score,
        "decision": decision,
        "threshold_required": 65,
        "impact_analysis": impact_analysis,
        "model": "Rule-Based Explainable Evaluator v1.0"
    }

    return decision, summary, detailed, audit

# -------------------------------
# FAIRNESS CHECK (Basic Simulation)
# -------------------------------
def fairness_check(score):
    # In real-world this compares with/without sensitive attributes
    # Here we simulate bias-risk scoring
    if score < 40:
        return "LOW RISK"
    elif score < 70:
        return "MEDIUM RISK"
    else:
        return "NO BIAS INDICATOR"

# -------------------------------
# FASTAPI APPLICATION
# -------------------------------
app = FastAPI(title="Human Justification System")

@app.post("/evaluate")
def evaluate_applicant(applicant: Applicant):

    score, thresholds = evaluate(applicant)

    decision, summary, detailed, audit = generate_explanation(
        applicant, score, thresholds
    )

    fairness = fairness_check(score)

    save_decision(applicant.name, score, decision, str(audit))

    return {
        "Summary Explanation": summary,
        "Detailed Explanation": detailed,
        "Audit Information": audit,
        "Fairness Check": fairness
    }

@app.get("/history")
def get_history():
    cursor.execute("SELECT * FROM decisions")
    rows = cursor.fetchall()
    return {"Decision History": rows}

# -------------------------------
# RUN USING:
# uvicorn hjs:app --reload
# -------------------------------