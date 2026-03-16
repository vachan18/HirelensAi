"""
HireLens AI — Resume Section Scorer
Scores individual resume sections (Skills, Projects, Experience, Education, Summary)
using heuristics + LLM analysis, returns structured scores with breakdowns.
"""

from __future__ import annotations
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class SectionScore:
    name: str
    score: int                    # 0-100
    grade: str                    # A/B/C/D/F
    color: str                    # hex
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    sub_scores: Dict[str, int] = field(default_factory=dict)
    tip: str = ""


def _grade(score: int) -> tuple[str, str]:
    """Return (grade, color) for a score."""
    if score >= 85: return "A", "#10B981"
    if score >= 70: return "B", "#3B82F6"
    if score >= 55: return "C", "#F59E0B"
    if score >= 40: return "D", "#F97316"
    return "F", "#EF4444"


def _count_metrics(text: str) -> int:
    """Count numeric metrics in text (%, numbers with units, $, x multipliers)."""
    return len(re.findall(
        r'(\d+[\.,]?\d*\s*(%|x|X|ms|kb|mb|gb|k\b|m\b|\$|£|€|hrs?|days?|weeks?|months?)|\$[\d,]+|\d+\s*(users?|customers?|engineers?|requests?|queries?))',
        text, re.IGNORECASE
    ))


def _count_action_verbs(text: str) -> int:
    """Count strong action verbs."""
    verbs = {
        'led', 'built', 'designed', 'architected', 'created', 'developed',
        'launched', 'shipped', 'delivered', 'reduced', 'increased', 'improved',
        'optimized', 'automated', 'migrated', 'integrated', 'deployed', 'scaled',
        'mentored', 'managed', 'owned', 'drove', 'spearheaded', 'pioneered',
        'engineered', 'implemented', 'established', 'transformed', 'accelerated',
    }
    weak_verbs = {'helped', 'assisted', 'worked', 'participated', 'contributed', 'involved'}
    words = set(re.findall(r'\b\w+ed\b|\b\w+\b', text.lower()))
    strong = len(words & verbs)
    weak   = len(words & weak_verbs)
    return strong, weak


def score_experience_section(bullets: list, years: Optional[int] = None) -> SectionScore:
    """Score the Experience section from agent bullet critique data."""
    if not bullets:
        s = 40
        g, c = _grade(s)
        return SectionScore(
            name="Experience", score=s, grade=g, color=c,
            weaknesses=["No bullet data available for analysis"],
            tip="Add quantified bullet points using the STAR format.",
        )

    total = len(bullets)
    has_metric = sum(1 for b in bullets if _count_metrics(b.get("bullet_excerpt","") + " " + b.get("fix","")) > 0)
    has_issue  = sum(1 for b in bullets if b.get("issue",""))

    # Sub scores
    metric_pct    = int((has_metric / max(total,1)) * 100)
    clarity_score = max(0, 100 - int((has_issue / max(total,1)) * 80))
    impact_score  = min(100, metric_pct + 20)
    ownership     = 60  # base — bumped by action verbs

    sub = {
        "Quantification": metric_pct,
        "Clarity":        clarity_score,
        "Impact":         impact_score,
        "Ownership":      ownership,
    }
    overall = int(sum(sub.values()) / len(sub))
    g, c = _grade(overall)

    strengths = []
    weaknesses = []

    if metric_pct >= 60: strengths.append("Good use of quantified metrics")
    else: weaknesses.append(f"Only {metric_pct}% of bullets have measurable impact")

    if has_issue > total // 2: weaknesses.append("Majority of bullets have identified issues")
    else: strengths.append("Most bullets are structurally sound")

    tip = "Prioritize adding % improvements, user counts, or time savings to each bullet."

    return SectionScore(
        name="Experience", score=overall, grade=g, color=c,
        strengths=strengths, weaknesses=weaknesses, sub_scores=sub, tip=tip,
    )


def score_skills_section(matched: list, missing_critical: list, match_score: int) -> SectionScore:
    """Score the Skills section."""
    total_matched = len(matched)
    total_missing = len(missing_critical)
    critical_count = sum(1 for s in missing_critical if s.get("importance") == "Critical")

    depth_score  = min(100, total_matched * 12)
    gap_penalty  = min(60, critical_count * 20 + (total_missing - critical_count) * 8)
    gap_score    = max(0, 100 - gap_penalty)
    match_norm   = match_score

    sub = {
        "Breadth":    depth_score,
        "Gap Score":  gap_score,
        "JD Match":   match_norm,
    }
    overall = int((depth_score * 0.3 + gap_score * 0.35 + match_norm * 0.35))
    g, c = _grade(overall)

    strengths = []
    weaknesses = []

    if total_matched >= 6: strengths.append(f"{total_matched} matched skills demonstrate solid coverage")
    if critical_count == 0: strengths.append("No critical skill gaps identified")
    if critical_count > 0: weaknesses.append(f"{critical_count} critical skills completely absent from resume")
    if total_missing > 4: weaknesses.append(f"{total_missing} total missing skills reduce JD match score")

    tip = "Lead with the top 6 skills from the JD in your Skills section. Group by category."

    return SectionScore(
        name="Skills", score=overall, grade=g, color=c,
        strengths=strengths, weaknesses=weaknesses, sub_scores=sub, tip=tip,
    )


def score_projects_section(resume_text: str = "", matched_skills: list = None) -> SectionScore:
    """Score Projects section using resume text heuristics."""
    matched_skills = matched_skills or []
    text_lower = resume_text.lower()

    has_projects = any(kw in text_lower for kw in ["project", "github", "built", "created", "developed"])
    has_links    = bool(re.search(r'github\.com|gitlab\.com|bitbucket|portfolio|demo|live', text_lower))
    has_tech     = len(re.findall(r'\b(python|react|node|docker|aws|kubernetes|sql|typescript|java|go\b)', text_lower))
    metric_hits  = _count_metrics(resume_text)
    strong_v, _  = _count_action_verbs(resume_text)

    presence  = 80 if has_projects else 20
    links     = 80 if has_links    else 30
    tech_cov  = min(100, has_tech * 12)
    impact    = min(100, metric_hits * 15)
    verbs     = min(100, strong_v  * 10)

    sub = {
        "Presence":   presence,
        "Links":      links,
        "Tech Stack": tech_cov,
        "Impact":     impact,
    }
    overall = int(sum(sub.values()) / len(sub))
    g, c = _grade(overall)

    strengths  = []
    weaknesses = []
    if has_links: strengths.append("Portfolio / GitHub links detected")
    else:         weaknesses.append("No public project links — add GitHub / live demo URLs")
    if has_tech >= 4: strengths.append(f"{has_tech} technology keywords detected in project context")
    else:             weaknesses.append("Projects lack specific technology stack details")
    if metric_hits > 0: strengths.append("Projects include measurable outcomes")
    else:               weaknesses.append("Projects have no quantified impact or scale")

    tip = "Each project should have: Tech used + Problem solved + Quantified outcome + Public link."

    return SectionScore(
        name="Projects", score=overall, grade=g, color=c,
        strengths=strengths, weaknesses=weaknesses, sub_scores=sub, tip=tip,
    )


def score_summary_section(resume_text: str = "", ats_score: int = 0) -> SectionScore:
    """Score the Summary / Profile section."""
    text_lower = resume_text.lower()

    # Detect summary block
    has_summary = any(kw in text_lower for kw in [
        "summary", "profile", "about", "objective", "overview",
        "senior engineer", "software engineer", "data scientist",
    ])
    word_count = len(resume_text.split()) if resume_text else 0

    density    = min(100, int((ats_score / 100) * 80 + 20))
    presence   = 75 if has_summary else 15
    length_ok  = 80 if 50 <= word_count <= 200 else (50 if word_count < 50 else 60)
    keyword    = min(100, ats_score + 10)

    sub = {
        "Presence":    presence,
        "Keyword Fit": keyword,
        "Conciseness": length_ok,
    }
    overall = int(sum(sub.values()) / len(sub))
    g, c = _grade(overall)

    strengths  = []
    weaknesses = []
    if has_summary: strengths.append("Summary section detected")
    else:           weaknesses.append("No summary section — add a 3-line profile targeting this role")
    if ats_score >= 70: strengths.append("Strong keyword density for ATS")
    else:               weaknesses.append("Summary likely lacks role-specific keywords")

    tip = "Write a 3-sentence summary: Who you are + Your top 2 skills + Your biggest win with a metric."

    return SectionScore(
        name="Summary", score=overall, grade=g, color=c,
        strengths=strengths, weaknesses=weaknesses, sub_scores=sub, tip=tip,
    )


def score_education_section(resume_text: str = "") -> SectionScore:
    """Score Education section."""
    text_lower = resume_text.lower()

    has_degree  = any(k in text_lower for k in ["bachelor", "master", "phd", "b.s", "m.s", "b.e", "b.tech", "m.tech", "degree"])
    has_courses = any(k in text_lower for k in ["coursework", "courses", "relevant", "gpa", "honors", "cum laude"])
    has_year    = bool(re.search(r'20\d\d|19\d\d', resume_text))
    has_certs   = any(k in text_lower for k in ["certified", "certification", "aws", "gcp", "azure", "cka", "pmp", "cfa"])

    degree_score = 90 if has_degree else 40
    extra_score  = 70 if has_courses or has_certs else 40
    recency      = 80 if has_year else 50

    sub = {
        "Degree":      degree_score,
        "Certs/Extras": extra_score,
        "Recency":     recency,
    }
    overall = int(sum(sub.values()) / len(sub))
    g, c = _grade(overall)

    strengths  = []
    weaknesses = []
    if has_degree: strengths.append("Degree qualification detected")
    else:          weaknesses.append("No clear degree listed — add full degree name and institution")
    if has_certs:  strengths.append("Professional certifications add credibility")
    else:          weaknesses.append("No certifications — relevant certs strengthen technical credibility")

    tip = "List certs directly below education. AWS/GCP/Azure certs are high-signal for tech roles."

    return SectionScore(
        name="Education", score=overall, grade=g, color=c,
        strengths=strengths, weaknesses=weaknesses, sub_scores=sub, tip=tip,
    )


def compute_all_section_scores(result: dict, resume_text: str = "") -> List[SectionScore]:
    """Main entry: compute all 5 section scores from analysis result dict."""
    ats    = result.get("ats",    {})
    skills = result.get("skills", {})
    exp    = result.get("experience", {})

    scores = [
        score_experience_section(exp.get("bullet_quality", []), exp.get("years_apparent")),
        score_skills_section(
            skills.get("matched_skills", []),
            skills.get("missing_critical", []),
            skills.get("match_score", 0),
        ),
        score_projects_section(resume_text, skills.get("matched_skills", [])),
        score_summary_section(resume_text, ats.get("ats_score", 0)),
        score_education_section(resume_text),
    ]
    return scores
