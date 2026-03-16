"""
HireLens AI — Pydantic v2 schemas (v2 — expanded for specialist agent outputs).
Every agent's JSON response is validated before passing downstream.
"""

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# ATS COMPLIANCE AGENT
# ─────────────────────────────────────────────

class SectionAudit(BaseModel):
    has_summary: bool = False
    has_skills: bool = False
    has_experience: bool = False
    has_education: bool = False
    has_contact: bool = False


class ATSFormatCheck(BaseModel):
    """Granular ATS formatting signal."""
    check: str                                          # e.g. "File format"
    status: Literal["PASS", "WARN", "FAIL"] = "WARN"
    detail: str = ""                                    # what was found / what is wrong


class ATSOutput(BaseModel):
    ats_score: int = Field(..., ge=0, le=100)
    pass_fail: Literal["PASS", "BORDERLINE", "FAIL"]

    # Keyword analysis
    keyword_matches: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    keyword_density_pct: int = Field(default=0, ge=0, le=100)

    # Structural analysis
    formatting_issues: List[str] = Field(default_factory=list)
    format_checks: List[ATSFormatCheck] = Field(default_factory=list)
    section_audit: SectionAudit = Field(default_factory=SectionAudit)

    # Scoring breakdown
    score_breakdown: dict = Field(default_factory=dict)   # sub-scores by category
    top_ats_risks: List[str] = Field(default_factory=list)  # ranked rejection triggers
    quick_ats_fixes: List[str] = Field(default_factory=list)  # <24hr actionable fixes

    ats_verdict: str = ""

    @field_validator("ats_score", "keyword_density_pct", mode="before")
    @classmethod
    def clamp_score(cls, v):
        return max(0, min(100, int(v)))


# ─────────────────────────────────────────────
# SKILLS GAP AGENT
# ─────────────────────────────────────────────

class MatchedSkill(BaseModel):
    skill: str
    evidence: str = ""
    proficiency: Literal["Beginner", "Intermediate", "Advanced", "Expert"] = "Intermediate"
    jd_importance: Literal["Required", "Preferred", "Nice-to-have"] = "Required"


class MissingCriticalSkill(BaseModel):
    skill: str
    importance: Literal["Critical", "High", "Medium"] = "Medium"
    learn_time_days: int = Field(default=30, ge=1)
    why_it_matters: str = ""           # role-specific context
    recommended_resource: str = ""     # specific course / cert / project


class SkillsGapOutput(BaseModel):
    match_score: int = Field(..., ge=0, le=100)

    # Matched skills with depth
    matched_skills: List[MatchedSkill] = Field(default_factory=list)

    # Gaps with depth
    missing_critical: List[MissingCriticalSkill] = Field(default_factory=list)
    missing_nice_to_have: List[str] = Field(default_factory=list)

    # Context
    overqualified_areas: List[str] = Field(default_factory=list)
    transferable_skills: List[str] = Field(default_factory=list)   # adjacent skills that partially substitute
    skill_trajectory: str = ""    # is the career moving toward or away from this role?

    # Ranked top missing (for quick dashboard display)
    top_5_missing: List[str] = Field(default_factory=list)

    skills_verdict: str = ""

    @field_validator("match_score", mode="before")
    @classmethod
    def clamp_score(cls, v):
        return max(0, min(100, int(v)))


# ─────────────────────────────────────────────
# EXPERIENCE ANALYSIS AGENT
# ─────────────────────────────────────────────

class BulletCritique(BaseModel):
    bullet_excerpt: str
    issue: str
    fix: str
    rewritten: str = ""     # agent-provided rewritten version of the bullet


class ProjectEvaluation(BaseModel):
    """Evaluation of a specific project or role."""
    title: str                  # project / company name
    relevance: Literal["High", "Medium", "Low"] = "Medium"
    impact_clarity: Literal["Strong", "Moderate", "Weak"] = "Moderate"
    missing_info: str = ""      # what context is absent


class ExperienceOutput(BaseModel):
    experience_score: int = Field(..., ge=0, le=100)

    # Seniority
    years_required: Optional[int] = None
    years_apparent: Optional[int] = None
    seniority_match: Literal["Under", "Match", "Over"] = "Match"

    # Quality signals
    domain_relevance: Literal["High", "Medium", "Low"] = "Medium"
    impact_rating: Literal["Strong", "Moderate", "Weak"] = "Moderate"
    quantification_score: int = Field(default=0, ge=0, le=100)  # % of bullets with metrics
    action_verb_quality: Literal["Strong", "Mixed", "Weak"] = "Mixed"

    # Detailed critiques
    bullet_quality: List[BulletCritique] = Field(default_factory=list)
    best_bullets: List[str] = Field(default_factory=list)
    weakest_bullets: List[str] = Field(default_factory=list)

    # Project / role evaluations
    project_evaluations: List[ProjectEvaluation] = Field(default_factory=list)

    # Narrative analysis
    career_progression: Literal["Strong", "Lateral", "Unclear"] = "Unclear"
    internship_quality: Literal["Strong", "Average", "Weak", "None"] = "None"

    experience_verdict: str = ""

    @field_validator("experience_score", "quantification_score", mode="before")
    @classmethod
    def clamp_score(cls, v):
        return max(0, min(100, int(v)))


# ─────────────────────────────────────────────
# HIRING MANAGER AGENT
# ─────────────────────────────────────────────

class RejectionReason(BaseModel):
    """A specific reason a recruiter would reject this candidate."""
    reason: str
    severity: Literal["Knockout", "Major", "Minor"] = "Major"
    fixable: bool = True
    how_to_fix: str = ""


class HiringManagerOutput(BaseModel):
    gut_score: int = Field(..., ge=0, le=100)

    # Decision
    would_interview: Literal["Yes", "Maybe", "No"] = "No"
    decision_confidence: Literal["High", "Medium", "Low"] = "Medium"

    # First scan analysis
    first_impression: str = ""
    headline_strength: Literal["Strong", "Adequate", "Weak"] = "Adequate"

    # Flags
    red_flags: List[str] = Field(default_factory=list)
    green_flags: List[str] = Field(default_factory=list)
    knockout_factors: List[str] = Field(default_factory=list)   # instant-disqualifiers

    # Detailed rejection analysis
    rejection_reasons: List[RejectionReason] = Field(default_factory=list)
    rejection_email_draft: str = ""

    # Fit signals
    culture_fit_signals: str = ""
    narrative_arc: str = ""
    interview_talking_points: List[str] = Field(default_factory=list)  # if they WERE interviewed

    hiring_manager_verdict: str = ""

    @field_validator("gut_score", mode="before")
    @classmethod
    def clamp_score(cls, v):
        return max(0, min(100, int(v)))


# ─────────────────────────────────────────────
# COORDINATOR AGENT
# ─────────────────────────────────────────────

class FixableGap(BaseModel):
    gap: str
    impact: str
    fix: str
    effort: Literal["Days", "Weeks", "Months"] = "Weeks"
    priority: int = Field(default=1, ge=1, le=3)   # 1=highest


class RoadmapWeek(BaseModel):
    week: int = Field(..., ge=1, le=4)
    theme: str
    actions: List[str] = Field(default_factory=list)
    success_metric: str = ""    # how to know this week is done


class CoordinatorOutput(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    rejection_probability: Literal["Very High", "High", "Medium", "Low"] = "High"

    # Root cause analysis
    primary_rejection_reason: str = ""
    secondary_rejection_reasons: List[str] = Field(default_factory=list)
    root_cause_category: Literal[
        "Skills Gap", "Experience Level", "ATS Filtering",
        "Narrative Clarity", "Cultural Fit", "Overqualified", "Multiple"
    ] = "Multiple"

    # Action plan
    top_3_fixable_gaps: List[FixableGap] = Field(default_factory=list)
    quick_wins: List[str] = Field(default_factory=list)
    roadmap: List[RoadmapWeek] = Field(default_factory=list, alias="30_day_roadmap")

    # Outcome prediction
    application_verdict: Literal["Apply Now", "Apply After Fixes", "Not Ready Yet"] = "Apply After Fixes"
    estimated_success_after_fixes: int = Field(default=0, ge=0, le=100)

    # Summary
    final_verdict: str = ""
    encouragement: str = ""
    competitor_comparison: str = ""  # how this resume compares to typical shortlisted candidates

    model_config = {"populate_by_name": True}

    @field_validator("overall_score", "estimated_success_after_fixes", mode="before")
    @classmethod
    def clamp_score(cls, v):
        return max(0, min(100, int(v)))


# ─────────────────────────────────────────────
# COMBINED RESULT
# ─────────────────────────────────────────────

class HireLensResult(BaseModel):
    """Top-level container returned by run_hirelens_analysis()."""
    ats: ATSOutput
    skills: SkillsGapOutput
    experience: ExperienceOutput
    hiring_manager: HiringManagerOutput
    coordinator: CoordinatorOutput

    @classmethod
    def from_raw(cls, raw: dict) -> "HireLensResult":
        return cls(
            ats=ATSOutput.model_validate(raw.get("ats", {})),
            skills=SkillsGapOutput.model_validate(raw.get("skills", {})),
            experience=ExperienceOutput.model_validate(raw.get("experience", {})),
            hiring_manager=HiringManagerOutput.model_validate(raw.get("hiring_manager", {})),
            coordinator=CoordinatorOutput.model_validate(raw.get("coordinator", {})),
        )
