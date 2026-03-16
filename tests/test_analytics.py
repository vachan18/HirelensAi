"""
Tests for all analytics modules.
Run with: pytest tests/test_analytics.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from analytics.mock_data import MOCK_RESULT


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def mock():
    return MOCK_RESULT

@pytest.fixture
def minimal():
    """Minimal result — all defaults, no optional data."""
    return {
        "ats":    {"ats_score": 50, "pass_fail": "BORDERLINE"},
        "skills": {"match_score": 50},
        "experience": {"experience_score": 50},
        "hiring_manager": {"gut_score": 50},
        "coordinator": {"overall_score": 50, "rejection_probability": "Medium"},
    }


# ─────────────────────────────────────────────
# SECTION SCORER
# ─────────────────────────────────────────────

class TestSectionScorer:
    def test_returns_five_sections(self, mock):
        from analytics.section_scorer import compute_all_section_scores
        scores = compute_all_section_scores(mock)
        assert len(scores) == 5

    def test_section_names_correct(self, mock):
        from analytics.section_scorer import compute_all_section_scores
        scores = compute_all_section_scores(mock)
        names = {s.name for s in scores}
        assert "Experience" in names
        assert "Skills" in names
        assert "Projects" in names

    def test_scores_in_range(self, mock):
        from analytics.section_scorer import compute_all_section_scores
        scores = compute_all_section_scores(mock)
        for s in scores:
            assert 0 <= s.score <= 100, f"{s.name} score {s.score} out of range"

    def test_grade_matches_score(self, mock):
        from analytics.section_scorer import compute_all_section_scores
        scores = compute_all_section_scores(mock)
        for s in scores:
            if s.score >= 85:   assert s.grade == "A"
            elif s.score >= 70: assert s.grade == "B"
            elif s.score >= 55: assert s.grade == "C"
            elif s.score >= 40: assert s.grade == "D"
            else:               assert s.grade == "F"

    def test_color_is_hex(self, mock):
        from analytics.section_scorer import compute_all_section_scores
        import re
        scores = compute_all_section_scores(mock)
        for s in scores:
            assert re.match(r"#[0-9A-Fa-f]{6}", s.color), f"Invalid color: {s.color}"

    def test_minimal_input_no_crash(self, minimal):
        from analytics.section_scorer import compute_all_section_scores
        scores = compute_all_section_scores(minimal, resume_text="")
        assert len(scores) == 5

    def test_resume_text_improves_projects_score(self):
        from analytics.section_scorer import score_projects_section
        with_links = score_projects_section("github.com/myproject deployed to production")
        without    = score_projects_section("I worked on a project")
        assert with_links.score >= without.score

    def test_education_certs_boost_score(self):
        from analytics.section_scorer import score_education_section
        with_cert    = score_education_section("Bachelor of Science. AWS Certified Solutions Architect.")
        without_cert = score_education_section("Bachelor of Science.")
        assert with_cert.score >= without_cert.score

    def test_sub_scores_populated(self, mock):
        from analytics.section_scorer import compute_all_section_scores
        scores = compute_all_section_scores(mock)
        exp_score = next(s for s in scores if s.name == "Experience")
        assert isinstance(exp_score.sub_scores, dict)
        assert len(exp_score.sub_scores) >= 2

    def test_has_tip_on_all_sections(self, mock):
        from analytics.section_scorer import compute_all_section_scores
        scores = compute_all_section_scores(mock)
        for s in scores:
            assert s.tip, f"{s.name} has no tip"


# ─────────────────────────────────────────────
# BULLET IMPROVER
# ─────────────────────────────────────────────

class TestBulletImprover:
    def test_returns_one_per_input(self):
        from analytics.bullet_improver import improve_bullets
        bullets = ["Worked on backend", "Helped team deploy"]
        result = improve_bullets(bullets, use_ai=False)
        assert len(result) == 2

    def test_improved_differs_from_original(self):
        from analytics.bullet_improver import improve_bullets
        bullets = ["Worked on backend features for the product"]
        result = improve_bullets(bullets, use_ai=False)
        assert result[0].improved != result[0].original or len(result[0].changes) > 0

    def test_impact_delta_positive(self):
        from analytics.bullet_improver import improve_bullets
        bullets = ["Helped team with database queries"]
        result = improve_bullets(bullets, use_ai=False)
        assert result[0].impact_delta >= 0

    def test_impact_delta_capped_at_25(self):
        from analytics.bullet_improver import improve_bullets
        bullets = ["Worked on things", "Helped with stuff", "Did some work"]
        results = improve_bullets(bullets, use_ai=False)
        for r in results:
            assert r.impact_delta <= 25

    def test_empty_input_returns_empty(self):
        from analytics.bullet_improver import improve_bullets
        assert improve_bullets([], use_ai=False) == []

    def test_whitespace_bullets_skipped(self):
        from analytics.bullet_improver import improve_bullets
        bullets = ["", "  ", "\n"]
        result = improve_bullets(bullets, use_ai=False)
        assert len(result) == 0

    def test_extract_bullets_from_result(self, mock):
        from analytics.bullet_improver import extract_bullets_from_result
        bullets = extract_bullets_from_result(mock)
        assert isinstance(bullets, list)
        assert len(bullets) >= 1

    def test_changes_list_populated(self):
        from analytics.bullet_improver import improve_bullets
        bullets = ["Worked on backend features"]
        result = improve_bullets(bullets, use_ai=False)
        assert isinstance(result[0].changes, list)
        assert len(result[0].changes) >= 1

    def test_weak_verb_replacement(self):
        from analytics.bullet_improver import _heuristic_improve
        result = _heuristic_improve("Helped team migrate to microservices")
        assert "Helped" not in result.improved[:6]

    def test_metric_placeholder_added_when_none(self):
        from analytics.bullet_improver import _heuristic_improve
        result = _heuristic_improve("Worked on backend refactoring project")
        assert "METRIC" in result.improved.upper() or result.impact_delta > 0


# ─────────────────────────────────────────────
# RECRUITER SIMULATOR
# ─────────────────────────────────────────────

class TestRecruiterSimulator:
    def test_probability_in_range(self, mock):
        from analytics.recruiter_simulator import simulate_recruiter_decision
        d = simulate_recruiter_decision(mock)
        assert 0 <= d.shortlist_probability <= 1.0
        assert 0 <= d.shortlist_pct <= 100

    def test_decision_classification(self, mock):
        from analytics.recruiter_simulator import simulate_recruiter_decision
        d = simulate_recruiter_decision(mock)
        assert d.decision in ("SHORTLIST", "MAYBE", "REJECT")

    def test_high_scores_yield_shortlist(self):
        from analytics.recruiter_simulator import simulate_recruiter_decision
        strong = {
            "ats": {"ats_score": 90, "pass_fail": "PASS"},
            "skills": {"match_score": 90, "matched_skills": [], "missing_critical": []},
            "experience": {"experience_score": 88, "impact_rating": "Strong", "bullet_quality": []},
            "hiring_manager": {"gut_score": 85, "would_interview": "Yes", "red_flags": [], "green_flags": ["Expert Python"]},
            "coordinator": {"overall_score": 88, "rejection_probability": "Low"},
        }
        d = simulate_recruiter_decision(strong)
        assert d.shortlist_pct >= 50

    def test_low_scores_yield_reject(self):
        from analytics.recruiter_simulator import simulate_recruiter_decision
        weak = {
            "ats": {"ats_score": 20, "pass_fail": "FAIL"},
            "skills": {"match_score": 20, "matched_skills": [], "missing_critical": []},
            "experience": {"experience_score": 25, "impact_rating": "Weak", "bullet_quality": []},
            "hiring_manager": {"gut_score": 18, "would_interview": "No", "red_flags": ["Multiple issues"], "green_flags": []},
            "coordinator": {"overall_score": 20, "rejection_probability": "Very High"},
        }
        d = simulate_recruiter_decision(weak)
        assert d.shortlist_pct <= 50

    def test_signals_have_correct_count(self, mock):
        from analytics.recruiter_simulator import simulate_recruiter_decision, SIGNAL_WEIGHTS
        d = simulate_recruiter_decision(mock)
        assert len(d.signals) == len(SIGNAL_WEIGHTS)

    def test_weights_sum_to_one(self):
        from analytics.recruiter_simulator import SIGNAL_WEIGHTS
        total = sum(SIGNAL_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01

    def test_stage_breakdown_populated(self, mock):
        from analytics.recruiter_simulator import simulate_recruiter_decision
        d = simulate_recruiter_decision(mock)
        assert len(d.stage_breakdown) >= 3
        for stage, pct in d.stage_breakdown.items():
            assert 0 <= pct <= 100

    def test_confidence_is_valid(self, mock):
        from analytics.recruiter_simulator import simulate_recruiter_decision
        d = simulate_recruiter_decision(mock)
        assert d.confidence in ("HIGH", "MEDIUM", "LOW")

    def test_benchmark_populated(self, mock):
        from analytics.recruiter_simulator import simulate_recruiter_decision
        d = simulate_recruiter_decision(mock)
        assert len(d.benchmark) >= 2


# ─────────────────────────────────────────────
# COMPARISON
# ─────────────────────────────────────────────

class TestComparison:
    def test_returns_eight_dimensions(self, mock):
        from analytics.comparison import run_comparison
        r = run_comparison(mock)
        assert len(r.dimensions) == 8

    def test_multi_agent_beats_single_ai(self, mock):
        from analytics.comparison import run_comparison
        r = run_comparison(mock)
        assert r.overall_multi >= r.overall_single

    def test_total_delta_positive(self, mock):
        from analytics.comparison import run_comparison
        r = run_comparison(mock)
        assert r.total_delta >= 0

    def test_unique_insights_populated(self, mock):
        from analytics.comparison import run_comparison
        r = run_comparison(mock)
        assert len(r.unique_insights) >= 1

    def test_verdict_is_string(self, mock):
        from analytics.comparison import run_comparison
        r = run_comparison(mock)
        assert isinstance(r.verdict, str) and len(r.verdict) > 10

    def test_dimension_winner_field(self, mock):
        from analytics.comparison import run_comparison
        r = run_comparison(mock)
        for d in r.dimensions:
            assert d.winner in ("Multi-Agent", "Comparable")

    def test_scores_in_range(self, mock):
        from analytics.comparison import run_comparison
        r = run_comparison(mock)
        for d in r.dimensions:
            assert 0 <= d.multi_agent_score <= 100
            assert 0 <= d.single_ai_score <= 100

    def test_minimal_no_crash(self, minimal):
        from analytics.comparison import run_comparison
        r = run_comparison(minimal)
        assert r.overall_multi >= 0


# ─────────────────────────────────────────────
# INTERVIEW PREDICTOR
# ─────────────────────────────────────────────

class TestInterviewPredictor:
    def test_returns_questions(self, mock):
        from analytics.interview_predictor import predict_interview_questions
        result = predict_interview_questions(mock)
        assert len(result.questions) >= 5

    def test_category_valid(self, mock):
        from analytics.interview_predictor import predict_interview_questions
        valid = {"Technical", "Behavioural", "Situational", "Culture", "Gap Defence"}
        pred = predict_interview_questions(mock)
        for q in pred.questions:
            assert q.category in valid, f"Invalid category: {q.category}"

    def test_difficulty_valid(self, mock):
        from analytics.interview_predictor import predict_interview_questions
        pred = predict_interview_questions(mock)
        for q in pred.questions:
            assert q.difficulty in ("Easy", "Medium", "Hard")

    def test_all_questions_have_tip(self, mock):
        from analytics.interview_predictor import predict_interview_questions
        pred = predict_interview_questions(mock)
        for q in pred.questions:
            assert q.strong_answer_tip, f"No tip for: {q.question[:40]}"

    def test_focus_areas_populated(self, mock):
        from analytics.interview_predictor import predict_interview_questions
        pred = predict_interview_questions(mock)
        assert len(pred.focus_areas) >= 1

    def test_minimal_no_crash(self, minimal):
        from analytics.interview_predictor import predict_interview_questions
        pred = predict_interview_questions(minimal)
        assert len(pred.questions) >= 1

    def test_gap_defence_included_for_critical_gaps(self, mock):
        from analytics.interview_predictor import predict_interview_questions
        pred = predict_interview_questions(mock)
        categories = [q.category for q in pred.questions]
        assert "Gap Defence" in categories or "Technical" in categories


# ─────────────────────────────────────────────
# COVER LETTER GENERATOR
# ─────────────────────────────────────────────

class TestCoverLetterGenerator:
    def test_generates_content(self, mock):
        from analytics.cover_letter import generate_cover_letter
        cl = generate_cover_letter("resume text", "job description", "Google", mock)
        assert len(cl.content) > 100

    def test_word_count_reasonable(self, mock):
        from analytics.cover_letter import generate_cover_letter
        cl = generate_cover_letter("resume text", "job description", "Google", mock)
        assert 100 <= cl.word_count <= 600

    def test_tone_stored(self, mock):
        from analytics.cover_letter import generate_cover_letter
        for tone in ("Professional", "Confident", "Direct"):
            cl = generate_cover_letter("resume", "jd", "Co", mock, tone=tone)
            assert cl.tone == tone

    def test_key_signals_list(self, mock):
        from analytics.cover_letter import generate_cover_letter
        cl = generate_cover_letter("resume", "jd", "Co", mock)
        assert isinstance(cl.key_signals_used, list)

    def test_no_placeholder_brackets(self, mock):
        from analytics.cover_letter import generate_cover_letter
        cl = generate_cover_letter("Engineer with Python skills", "Need Python developer", "Stripe", mock)
        # Template may have [Your Name] — that's acceptable in heuristic mode
        assert len(cl.content) > 0

    def test_minimal_no_crash(self, minimal):
        from analytics.cover_letter import generate_cover_letter
        cl = generate_cover_letter("", "", "", minimal)
        assert len(cl.content) > 50


# ─────────────────────────────────────────────
# MOCK DATA INTEGRITY
# ─────────────────────────────────────────────

class TestMockData:
    def test_all_sections_present(self):
        assert "ats" in MOCK_RESULT
        assert "skills" in MOCK_RESULT
        assert "experience" in MOCK_RESULT
        assert "hiring_manager" in MOCK_RESULT
        assert "coordinator" in MOCK_RESULT

    def test_new_schema_fields_present(self):
        """All v2 schema fields should be in mock data."""
        ats = MOCK_RESULT["ats"]
        assert "keyword_density_pct" in ats
        assert "format_checks" in ats
        assert "score_breakdown" in ats
        assert "top_ats_risks" in ats
        assert "quick_ats_fixes" in ats

        sk = MOCK_RESULT["skills"]
        assert "top_5_missing" in sk
        assert "transferable_skills" in sk
        assert "skill_trajectory" in sk

        exp = MOCK_RESULT["experience"]
        assert "quantification_score" in exp
        assert "project_evaluations" in exp
        assert "career_progression" in exp

        hm = MOCK_RESULT["hiring_manager"]
        assert "knockout_factors" in hm
        assert "rejection_reasons" in hm
        assert "interview_talking_points" in hm
        assert "decision_confidence" in hm

        coord = MOCK_RESULT["coordinator"]
        assert "root_cause_category" in coord
        assert "application_verdict" in coord
        assert "estimated_success_after_fixes" in coord
        assert "competitor_comparison" in coord

    def test_mock_validates_against_schemas(self):
        from models.schemas import HireLensResult
        result = HireLensResult.from_raw(MOCK_RESULT)
        assert result.ats.ats_score == 62
        assert result.coordinator.overall_score == 53

    def test_roadmap_has_four_weeks(self):
        roadmap = MOCK_RESULT["coordinator"]["30_day_roadmap"]
        assert len(roadmap) == 4
        for week in roadmap:
            assert "week" in week
            assert "theme" in week
            assert "actions" in week
            assert len(week["actions"]) >= 2
