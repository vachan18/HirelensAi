"""
HireLens AI — Recruiter Decision Simulator
Calculates shortlist probability using a weighted scoring model
across 8 dimensions, with confidence intervals and decision reasoning.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class RecruiterSignal:
    name: str
    weight: float          # 0.0–1.0, weights sum to 1.0
    raw_score: int         # 0-100 from analysis
    weighted: float        # raw_score * weight
    verdict: str           # PASS / WARN / FAIL
    reason: str


@dataclass
class RecruiterDecision:
    shortlist_probability: float     # 0.0–1.0
    shortlist_pct: int               # 0-100
    decision: str                    # SHORTLIST / MAYBE / REJECT
    decision_color: str              # hex
    confidence: str                  # HIGH / MEDIUM / LOW
    signals: List[RecruiterSignal]
    top_positive: List[str]          # reasons supporting shortlist
    top_negative: List[str]          # reasons against shortlist
    stage_breakdown: Dict[str, int]  # proba at each stage
    benchmark: Dict[str, int]        # percentile vs general pool


# ─── WEIGHT TABLE ───────────────────────────────────────────────
# Total weights must sum to 1.0
SIGNAL_WEIGHTS = {
    "ats_pass_rate":      0.18,   # ATS gate — binary filter
    "skills_match":       0.22,   # Core skills coverage
    "experience_match":   0.18,   # Seniority + domain
    "impact_evidence":    0.14,   # Quantified achievements
    "hm_gut_reaction":    0.12,   # Hiring manager simulation
    "career_narrative":   0.08,   # Coherent career story
    "red_flag_penalty":   0.05,   # Red flags (inverted)
    "keyword_density":    0.03,   # ATS keyword match
}


def _verdict(score: int) -> str:
    if score >= 70: return "PASS"
    if score >= 45: return "WARN"
    return "FAIL"


def _impact_score(exp: dict) -> int:
    """Estimate impact evidence score from experience data."""
    base = exp.get("experience_score", 50)
    ir   = {"Strong": 85, "Moderate": 55, "Weak": 30}.get(exp.get("impact_rating","Moderate"), 55)
    return int(base * 0.5 + ir * 0.5)


def _career_narrative_score(hm: dict) -> int:
    """Estimate career narrative score from hiring manager data."""
    base = hm.get("gut_score", 50)
    wi   = {"Yes": 85, "Maybe": 55, "No": 20}.get(hm.get("would_interview","No"), 20)
    rf_penalty = len(hm.get("red_flags", [])) * 8
    return max(0, int(base * 0.6 + wi * 0.4 - rf_penalty))


def _red_flag_inverted(hm: dict) -> int:
    """Red flag score — 100 = no flags, decreases per flag."""
    flags = len(hm.get("red_flags", []))
    return max(0, 100 - flags * 18)


def simulate_recruiter_decision(result: dict) -> RecruiterDecision:
    """
    Simulate the probability a recruiter shortlists this candidate.

    Args:
        result: HireLensResult as dict.

    Returns:
        RecruiterDecision with probability, signals, and breakdown.
    """
    ats    = result.get("ats",    {})
    skills = result.get("skills", {})
    exp    = result.get("experience", {})
    hm     = result.get("hiring_manager", {})
    coord  = result.get("coordinator", {})

    # ── Build raw scores for each signal ──
    raw_scores = {
        "ats_pass_rate":    ats.get("ats_score", 0),
        "skills_match":     skills.get("match_score", 0),
        "experience_match": exp.get("experience_score", 0),
        "impact_evidence":  _impact_score(exp),
        "hm_gut_reaction":  hm.get("gut_score", 0),
        "career_narrative": _career_narrative_score(hm),
        "red_flag_penalty": _red_flag_inverted(hm),
        "keyword_density":  min(100, ats.get("ats_score", 0) + 5),
    }

    # ── Compute weighted total ──
    signals = []
    weighted_total = 0.0

    signal_labels = {
        "ats_pass_rate":    "ATS Pass Rate",
        "skills_match":     "Skills Match",
        "experience_match": "Experience Match",
        "impact_evidence":  "Impact Evidence",
        "hm_gut_reaction":  "HM Gut Reaction",
        "career_narrative": "Career Narrative",
        "red_flag_penalty": "Red Flag Check",
        "keyword_density":  "Keyword Density",
    }
    signal_reasons = {
        "ats_pass_rate":    "Determines whether resume clears automated filtering",
        "skills_match":     "Direct overlap with JD required skills",
        "experience_match": "Seniority and domain relevance to role",
        "impact_evidence":  "Quantified achievements signal high performer",
        "hm_gut_reaction":  "Would a VP want to meet this person?",
        "career_narrative": "Is the career story compelling and coherent?",
        "red_flag_penalty": "Red flags immediately reduce shortlist probability",
        "keyword_density":  "Role-relevant vocabulary saturation",
    }

    for key, weight in SIGNAL_WEIGHTS.items():
        raw  = raw_scores.get(key, 50)
        w    = raw * weight
        weighted_total += w
        signals.append(RecruiterSignal(
            name=signal_labels[key],
            weight=weight,
            raw_score=raw,
            weighted=round(w, 2),
            verdict=_verdict(raw),
            reason=signal_reasons[key],
        ))

    # ── Convert to probability with sigmoid smoothing ──
    # weighted_total is 0–100; map to 0–1 via soft sigmoid
    normalized = weighted_total / 100.0
    # Sigmoid to prevent extreme values
    prob = 1 / (1 + math.exp(-8 * (normalized - 0.52)))
    prob = round(max(0.02, min(0.97, prob)), 3)
    pct  = int(prob * 100)

    # ── Decision classification ──
    if pct >= 68:
        decision = "SHORTLIST"
        decision_color = "#10B981"
    elif pct >= 42:
        decision = "MAYBE"
        decision_color = "#F59E0B"
    else:
        decision = "REJECT"
        decision_color = "#EF4444"

    # ── Confidence based on signal variance ──
    raw_vals = list(raw_scores.values())
    variance = max(raw_vals) - min(raw_vals)
    if variance > 50:
        confidence = "LOW"     # Very mixed signals
    elif variance > 30:
        confidence = "MEDIUM"
    else:
        confidence = "HIGH"

    # ── Positive / negative drivers ──
    top_positive = []
    top_negative = []

    if ats.get("ats_score",0) >= 70:
        top_positive.append(f"Strong ATS score ({ats.get('ats_score',0)}/100) clears automated filters")
    if skills.get("match_score",0) >= 70:
        top_positive.append(f"High skills match ({skills.get('match_score',0)}%) reduces screening effort")
    if hm.get("would_interview") == "Yes":
        top_positive.append("Hiring manager simulation predicts interview interest")
    if exp.get("impact_rating") == "Strong":
        top_positive.append("Strong impact evidence in experience bullets")
    for gf in hm.get("green_flags", [])[:2]:
        top_positive.append(gf)

    if ats.get("ats_score",0) < 50:
        top_negative.append(f"Low ATS score ({ats.get('ats_score',0)}/100) likely triggers auto-rejection")
    if skills.get("match_score",0) < 50:
        top_negative.append(f"Skills match below 50% — recruiter sees clear gap immediately")
    if hm.get("would_interview") == "No":
        top_negative.append("Hiring manager simulation predicts rejection without interview")
    for rf in hm.get("red_flags", [])[:3]:
        top_negative.append(rf)

    rejection_prob = coord.get("rejection_probability","High")
    if rejection_prob in ("High","Very High"):
        top_negative.append(f"Coordinator assessment: rejection probability is {rejection_prob}")

    # Deduplicate and trim
    top_positive = list(dict.fromkeys(top_positive))[:4]
    top_negative = list(dict.fromkeys(top_negative))[:4]

    # ── Stage-by-stage breakdown ──
    stage_breakdown = {
        "ATS Screen":       min(99, ats.get("ats_score",0)),
        "Recruiter Screen": min(99, int(pct * 1.1)),
        "HM Screen":        min(99, hm.get("gut_score",0)),
        "Interview":        min(99, int(pct * 0.7)),
        "Offer":            min(99, int(pct * 0.4)),
    }

    # ── Benchmarking (estimated vs typical applicant pool) ──
    # Rough percentile model: pct 50 = 50th percentile for competitive roles
    pool_adj  = max(1, min(99, int(pct * 0.9 + 5)))
    benchmark = {
        "vs. All Applicants":         pool_adj,
        "vs. Qualified Applicants":   max(1, pool_adj - 15),
        "vs. Shortlisted Candidates": max(1, pool_adj - 30),
    }

    return RecruiterDecision(
        shortlist_probability=prob,
        shortlist_pct=pct,
        decision=decision,
        decision_color=decision_color,
        confidence=confidence,
        signals=signals,
        top_positive=top_positive,
        top_negative=top_negative,
        stage_breakdown=stage_breakdown,
        benchmark=benchmark,
    )
