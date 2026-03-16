"""
Unit tests for Pydantic schemas in models/schemas.py
Run with: pytest tests/test_models.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from pydantic import ValidationError
from models.schemas import (
    ATSOutput,
    SkillsGapOutput,
    ExperienceOutput,
    HiringManagerOutput,
    CoordinatorOutput,
    HireLensResult,
    SectionAudit,
    MatchedSkill,
    MissingCriticalSkill,
    FixableGap,
    RoadmapWeek,
)


# ─────────────────────────────────────────────
# ATSOutput
# ─────────────────────────────────────────────

class TestATSOutput:
    def test_valid_pass(self):
        obj = ATSOutput(ats_score=85, pass_fail="PASS")
        assert obj.ats_score == 85
        assert obj.pass_fail == "PASS"

    def test_score_clamped_above_100(self):
        obj = ATSOutput(ats_score=150, pass_fail="PASS")
        assert obj.ats_score == 100

    def test_score_clamped_below_0(self):
        obj = ATSOutput(ats_score=-10, pass_fail="FAIL")
        assert obj.ats_score == 0

    def test_invalid_pass_fail(self):
        with pytest.raises(ValidationError):
            ATSOutput(ats_score=50, pass_fail="UNKNOWN")

    def test_defaults(self):
        obj = ATSOutput(ats_score=50, pass_fail="BORDERLINE")
        assert obj.keyword_matches == []
        assert obj.missing_keywords == []
        assert obj.formatting_issues == []
        assert obj.ats_verdict == ""

    def test_section_audit_defaults(self):
        obj = ATSOutput(ats_score=60, pass_fail="BORDERLINE")
        assert obj.section_audit.has_summary is False
        assert obj.section_audit.has_contact is False

    def test_full_construction(self):
        obj = ATSOutput(
            ats_score=72,
            pass_fail="PASS",
            keyword_matches=["Python", "SQL"],
            missing_keywords=["Kubernetes"],
            formatting_issues=["No bullet points"],
            section_audit=SectionAudit(
                has_summary=True, has_skills=True,
                has_experience=True, has_education=True, has_contact=True
            ),
            ats_verdict="Decent ATS score but missing cloud keywords.",
        )
        assert len(obj.keyword_matches) == 2
        assert obj.section_audit.has_summary is True


# ─────────────────────────────────────────────
# SkillsGapOutput
# ─────────────────────────────────────────────

class TestSkillsGapOutput:
    def test_valid(self):
        obj = SkillsGapOutput(match_score=65)
        assert obj.match_score == 65

    def test_matched_skill_proficiency_enum(self):
        with pytest.raises(ValidationError):
            MatchedSkill(skill="Python", proficiency="Ninja")

    def test_matched_skill_valid(self):
        s = MatchedSkill(skill="Python", evidence="Used in all projects", proficiency="Expert")
        assert s.proficiency == "Expert"

    def test_missing_critical_skill(self):
        s = MissingCriticalSkill(skill="Kubernetes", importance="Critical", learn_time_days=30)
        assert s.learn_time_days == 30

    def test_missing_critical_importance_enum(self):
        with pytest.raises(ValidationError):
            MissingCriticalSkill(skill="K8s", importance="Urgent", learn_time_days=14)

    def test_score_clamp(self):
        obj = SkillsGapOutput(match_score=999)
        assert obj.match_score == 100


# ─────────────────────────────────────────────
# ExperienceOutput
# ─────────────────────────────────────────────

class TestExperienceOutput:
    def test_valid(self):
        obj = ExperienceOutput(experience_score=70, seniority_match="Match")
        assert obj.seniority_match == "Match"

    def test_seniority_enum(self):
        with pytest.raises(ValidationError):
            ExperienceOutput(experience_score=70, seniority_match="Senior")

    def test_domain_relevance_enum(self):
        with pytest.raises(ValidationError):
            ExperienceOutput(experience_score=70, domain_relevance="Very High")

    def test_impact_rating_enum(self):
        with pytest.raises(ValidationError):
            ExperienceOutput(experience_score=70, impact_rating="Outstanding")

    def test_optional_years(self):
        obj = ExperienceOutput(experience_score=50, years_required=None, years_apparent=None)
        assert obj.years_required is None


# ─────────────────────────────────────────────
# HiringManagerOutput
# ─────────────────────────────────────────────

class TestHiringManagerOutput:
    def test_valid(self):
        obj = HiringManagerOutput(gut_score=45, would_interview="No")
        assert obj.would_interview == "No"

    def test_would_interview_enum(self):
        with pytest.raises(ValidationError):
            HiringManagerOutput(gut_score=45, would_interview="Perhaps")

    def test_defaults(self):
        obj = HiringManagerOutput(gut_score=60)
        assert obj.red_flags == []
        assert obj.green_flags == []


# ─────────────────────────────────────────────
# CoordinatorOutput
# ─────────────────────────────────────────────

class TestCoordinatorOutput:
    def test_valid(self):
        obj = CoordinatorOutput(overall_score=55, rejection_probability="High")
        assert obj.rejection_probability == "High"

    def test_rejection_prob_enum(self):
        with pytest.raises(ValidationError):
            CoordinatorOutput(overall_score=55, rejection_probability="Extreme")

    def test_fixable_gap(self):
        g = FixableGap(gap="Missing Python", impact="Core language", fix="Take a course", effort="Weeks")
        assert g.effort == "Weeks"

    def test_fixable_gap_effort_enum(self):
        with pytest.raises(ValidationError):
            FixableGap(gap="X", impact="Y", fix="Z", effort="Years")

    def test_roadmap_week(self):
        w = RoadmapWeek(week=1, theme="ATS Fixes", actions=["Fix formatting", "Add keywords"])
        assert len(w.actions) == 2

    def test_alias_30_day_roadmap(self):
        """Test that the 30_day_roadmap alias works."""
        data = {
            "overall_score": 50,
            "rejection_probability": "High",
            "30_day_roadmap": [
                {"week": 1, "theme": "Fix resume", "actions": ["Do X"]}
            ]
        }
        obj = CoordinatorOutput.model_validate(data)
        assert len(obj.roadmap) == 1


# ─────────────────────────────────────────────
# HireLensResult (integration)
# ─────────────────────────────────────────────

class TestHireLensResult:
    def _make_result(self):
        return HireLensResult(
            ats=ATSOutput(ats_score=70, pass_fail="PASS"),
            skills=SkillsGapOutput(match_score=60),
            experience=ExperienceOutput(experience_score=65),
            hiring_manager=HiringManagerOutput(gut_score=55),
            coordinator=CoordinatorOutput(overall_score=62, rejection_probability="Medium"),
        )

    def test_construction(self):
        r = self._make_result()
        assert r.ats.ats_score == 70
        assert r.coordinator.overall_score == 62

    def test_serialization_roundtrip(self):
        r = self._make_result()
        data = r.model_dump()
        r2 = HireLensResult.model_validate(data)
        assert r2.skills.match_score == r.skills.match_score

    def test_from_raw(self):
        raw = {
            "ats": {"ats_score": 80, "pass_fail": "PASS"},
            "skills": {"match_score": 75},
            "experience": {"experience_score": 70},
            "hiring_manager": {"gut_score": 65},
            "coordinator": {"overall_score": 72, "rejection_probability": "Medium"},
        }
        r = HireLensResult.from_raw(raw)
        assert r.ats.ats_score == 80
        assert r.coordinator.overall_score == 72
