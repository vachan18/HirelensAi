"""
HireLens AI — Interview Question Predictor
Generates likely interview questions based on skills gaps, experience weaknesses,
and hiring manager signals from the analysis. Uses Anthropic API or heuristics.
"""

from __future__ import annotations
import os
import re
import json
from dataclasses import dataclass, field
from typing import List, Literal


@dataclass
class InterviewQuestion:
    question: str
    category: Literal["Technical", "Behavioural", "Situational", "Culture", "Gap Defence"]
    difficulty: Literal["Easy", "Medium", "Hard"]
    why_asked: str          # what the interviewer is trying to learn
    strong_answer_tip: str  # how to nail it
    trap: str = ""          # what most candidates get wrong


@dataclass
class InterviewPrediction:
    questions: List[InterviewQuestion]
    focus_areas: List[str]   # areas the interview will focus on
    prep_priorities: List[str]


def _heuristic_questions(result: dict) -> InterviewPrediction:
    """Generate targeted interview questions from analysis results (no API required)."""
    skills = result.get("skills", {})
    exp    = result.get("experience", {})
    hm     = result.get("hiring_manager", {})
    coord  = result.get("coordinator", {})

    questions: List[InterviewQuestion] = []
    focus_areas: List[str] = []

    # ── From skills gaps ──
    missing_critical = skills.get("missing_critical", [])
    for gap in missing_critical[:3]:
        skill = gap.get("skill", "")
        importance = gap.get("importance", "High")
        if importance in ("Critical", "High"):
            questions.append(InterviewQuestion(
                question=f"Tell me about your experience with {skill}. How have you used it in production?",
                category="Technical",
                difficulty="Hard",
                why_asked=f"This skill is required — the interviewer needs to gauge actual depth vs resume padding.",
                strong_answer_tip=f"If you lack {skill} experience, be honest and describe your learning plan. Show you understand why it matters for this role specifically.",
                trap="Claiming expertise you don't have — interviewers probe with follow-ups and will expose overstatements immediately.",
            ))
            focus_areas.append(f"{skill} knowledge depth")

    # ── From experience weaknesses ──
    for b in exp.get("bullet_quality", [])[:2]:
        excerpt = b.get("bullet_excerpt", "")
        if excerpt:
            clean = excerpt[:50]
            questions.append(InterviewQuestion(
                question=f"You mentioned '{clean}...' — walk me through exactly what you owned in that work.",
                category="Behavioural",
                difficulty="Medium",
                why_asked="Vague resume language signals participation rather than ownership. This probes the real contribution.",
                strong_answer_tip="Use STAR: Situation (context) + Task (your specific responsibility) + Action (your exact decisions) + Result (measurable outcome). Own the 'I', not the 'we'.",
                trap="Saying 'we' throughout. Interviewers want to know YOUR contribution specifically.",
            ))

    # ── From hiring manager talking points ──
    for tp in hm.get("interview_talking_points", []):
        questions.append(InterviewQuestion(
            question=tp,
            category="Technical",
            difficulty="Medium",
            why_asked="This area is flagged by the hiring manager simulation as a key signal.",
            strong_answer_tip="Prepare a 3-minute detailed answer with architecture context, your specific decisions, and what you'd change now.",
        ))
        focus_areas.append("Ownership evidence")

    # ── Red flag probes ──
    red_flags = hm.get("red_flags", [])
    for flag in red_flags[:2]:
        if "tenure" in flag.lower() or "job" in flag.lower():
            questions.append(InterviewQuestion(
                question="I notice you've had a few shorter stints in your career — can you walk me through the reasoning behind each transition?",
                category="Behavioural",
                difficulty="Hard",
                why_asked="Multiple short tenures is the top retention risk signal. The interviewer needs reassurance.",
                strong_answer_tip="Prepare a coherent narrative for each transition. 'I left because X and specifically chose Y for Z reason' is far stronger than 'it was a good opportunity'.",
                trap="Being defensive or vague. Own the story — make each move sound strategic.",
            ))
            focus_areas.append("Retention and commitment signals")
            break

    # ── Gap defence ──
    primary_gap = coord.get("primary_rejection_reason", "")
    if primary_gap:
        questions.append(InterviewQuestion(
            question="What's your plan to get up to speed on our infrastructure stack in the first 30 days?",
            category="Gap Defence",
            difficulty="Hard",
            why_asked="Hiring manager knows about the skills gap — they want to see how self-aware and resourceful you are.",
            strong_answer_tip="Name specific resources (not 'I'll Google it'), give a timeline, and show you understand the business reason for needing the skill.",
            trap="Saying you'll 'learn quickly' without a specific plan. That answer is instantly forgettable.",
        ))
        focus_areas.append("Self-awareness of skills gaps")

    # ── Universal system design ──
    if exp.get("experience_score", 0) < 70:
        questions.append(InterviewQuestion(
            question="Design a URL shortener service. Walk me through the architecture, scaling considerations, and the tradeoffs you'd make.",
            category="Technical",
            difficulty="Hard",
            why_asked="Classic system design question that probes architectural thinking at seniority level.",
            strong_answer_tip="Start with requirements. Define scale. Draw the components: API layer → cache → DB → CDN. Then discuss tradeoffs (SQL vs NoSQL, caching strategy, consistency model).",
            trap="Jumping to implementation without clarifying requirements first. Senior engineers always scope before designing.",
        ))
        focus_areas.append("System design capability")

    # ── Cultural fit ──
    culture = hm.get("culture_fit_signals", "")
    if "individual" in culture.lower() or "solo" in culture.lower():
        questions.append(InterviewQuestion(
            question="Tell me about a time you had a significant technical disagreement with a colleague. How did you resolve it?",
            category="Behavioural",
            difficulty="Medium",
            why_asked="Signals collaborative problem-solving vs individual contributor mindset.",
            strong_answer_tip="Show you sought to understand the other perspective, brought data to the discussion, and reached consensus rather than just winning.",
            trap="Making yourself the hero who was right all along. That signals low collaboration maturity.",
        ))
        focus_areas.append("Collaboration and communication style")

    # Default filler questions to reach at least 8
    default_qs = [
        InterviewQuestion(
            question="Walk me through your most technically complex project. What made it hard and how did you approach it?",
            category="Technical",
            difficulty="Medium",
            why_asked="Reveals problem-solving depth, comfort with ambiguity, and technical vocabulary.",
            strong_answer_tip="Pick a project where you made genuine architectural decisions. Use before/after metrics.",
        ),
        InterviewQuestion(
            question="What does good code review look like to you, as both reviewer and reviewee?",
            category="Behavioural",
            difficulty="Easy",
            why_asked="Reveals team collaboration maturity and code quality philosophy.",
            strong_answer_tip="Mention specific things you look for: correctness, readability, test coverage, performance. Show you value the process beyond just style.",
        ),
        InterviewQuestion(
            question="Where do you see yourself in 2 years, and how does this role fit that path?",
            category="Culture",
            difficulty="Easy",
            why_asked="Hiring for retention — they want to know if this role serves your growth.",
            strong_answer_tip="Anchor your answer to specific skills or experiences you want to develop that this role uniquely offers.",
            trap="'I want to be a manager in 2 years' for an IC role, or vice versa.",
        ),
        InterviewQuestion(
            question="Tell me about a production incident you were involved in. What happened, what was your role, and what changed afterward?",
            category="Situational",
            difficulty="Medium",
            why_asked="Reveals how you handle failure, communicate under pressure, and build learning culture.",
            strong_answer_tip="Be concrete about the incident severity, your specific actions, and what process or code changed as a result. Own any part you played.",
        ),
    ]

    while len(questions) < 8:
        q = default_qs.pop(0) if default_qs else None
        if not q:
            break
        questions.append(q)

    focus_areas = list(dict.fromkeys(focus_areas))[:5]  # deduplicate

    prep_priorities = [
        f"Prepare a detailed answer about: {fa}" for fa in focus_areas
    ]
    if missing_critical:
        prep_priorities.insert(0,
            f"Be ready to discuss your plan to learn {missing_critical[0].get('skill','')} specifically"
        )

    return InterviewPrediction(
        questions=questions[:10],
        focus_areas=focus_areas,
        prep_priorities=prep_priorities[:5],
    )


def _api_questions(result: dict) -> InterviewPrediction:
    """Use Anthropic API for richer, role-specific question generation."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _heuristic_questions(result)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        coord  = result.get("coordinator", {})
        skills = result.get("skills", {})
        hm     = result.get("hiring_manager", {})
        exp    = result.get("experience", {})

        context = json.dumps({
            "primary_rejection_reason": coord.get("primary_rejection_reason", ""),
            "top_5_missing_skills": skills.get("top_5_missing", []),
            "red_flags": hm.get("red_flags", []),
            "experience_verdict": exp.get("experience_verdict", ""),
            "interview_talking_points": hm.get("interview_talking_points", []),
        }, indent=2)

        prompt = f"""Based on this job application analysis, generate 8 targeted interview questions
that a hiring manager would actually ask this specific candidate.

ANALYSIS CONTEXT:
{context}

Each question should address a real signal from the analysis — a skills gap, a resume weakness,
a red flag, or an area the hiring manager flagged.

Return ONLY a JSON array — no markdown, no explanation:
[
  {{
    "question": "<exact interview question>",
    "category": "<Technical|Behavioural|Situational|Culture|Gap Defence>",
    "difficulty": "<Easy|Medium|Hard>",
    "why_asked": "<what the interviewer is trying to learn — 1 sentence>",
    "strong_answer_tip": "<how to give a strong answer — 2 sentences>",
    "trap": "<most common mistake candidates make — 1 sentence, or empty string>"
  }}
]
"""
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        parsed = json.loads(raw)

        questions = [
            InterviewQuestion(
                question=q.get("question", ""),
                category=q.get("category", "Technical"),
                difficulty=q.get("difficulty", "Medium"),
                why_asked=q.get("why_asked", ""),
                strong_answer_tip=q.get("strong_answer_tip", ""),
                trap=q.get("trap", ""),
            )
            for q in parsed[:10]
        ]

        missing = skills.get("top_5_missing", [])
        focus_areas = [f"Depth check on {s}" for s in missing[:3]]
        focus_areas += ["Ownership evidence from experience bullets"]

        return InterviewPrediction(
            questions=questions,
            focus_areas=focus_areas,
            prep_priorities=[f"Prepare structured answer for: {q.question[:60]}..." for q in questions[:4]],
        )

    except Exception:
        return _heuristic_questions(result)


def predict_interview_questions(result: dict) -> InterviewPrediction:
    """Main entry. Uses API if available, falls back to heuristics."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _api_questions(result)
    return _heuristic_questions(result)
