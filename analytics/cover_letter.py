"""
HireLens AI — Cover Letter Generator
Generates a targeted, non-generic cover letter based on resume, JD, and analysis signals.
Uses Anthropic API or heuristic template when unavailable.
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class CoverLetter:
    content: str           # full letter text
    tone: str              # the tone used
    word_count: int
    key_signals_used: list  # which analysis signals were incorporated


def _heuristic_cover_letter(
    resume_text: str,
    job_description: str,
    company: str,
    result: dict,
    tone: Literal["Professional", "Confident", "Direct"],
) -> CoverLetter:
    """Template-based cover letter using analysis signals."""

    skills  = result.get("skills", {})
    exp     = result.get("experience", {})
    coord   = result.get("coordinator", {})
    hm      = result.get("hiring_manager", {})

    # Extract key signals
    matched = [s.get("skill", "") for s in skills.get("matched_skills", [])[:4]]
    best_bullets = exp.get("best_bullets", [])
    green_flags = hm.get("green_flags", [])
    encouragement = coord.get("encouragement", "")

    # Build key achievements string from best bullets
    achievement = best_bullets[0] if best_bullets else "delivered measurable backend improvements"
    strength = green_flags[0] if green_flags else (encouragement or "strong backend engineering experience")
    skills_str = ", ".join(matched[:3]) if matched else "Python, REST API design, and backend systems"

    co = company or "your company"

    letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {co} engineering team. After reviewing the role requirements, I believe my background in {skills_str} positions me to contribute meaningfully from day one.

In my most recent work, I {achievement.lower() if achievement[0].isupper() else achievement}. This experience gave me direct exposure to the kind of challenges your team is solving — and I'm eager to bring that perspective to {co}.

What draws me to this specific role is the opportunity to work at the intersection of backend systems and cloud infrastructure. I have been actively building toward this direction: strengthening my Python and API architecture skills while investing in cloud foundations to close the infrastructure gaps I know are important for this position.

A few things I would bring to your team:
- Proven ability to deliver backend systems with measurable impact
- Experience designing APIs that handle real transaction volumes
- A track record of improving system performance through systematic diagnosis rather than guesswork

I would welcome the opportunity to discuss how my background aligns with your team's needs and where I could contribute most immediately.

Thank you for your time and consideration.

Best regards,
[Your Name]
"""

    key_signals = [
        "Top matched skills from analysis",
        "Best bullet evidence from experience section",
        "Green flags identified by hiring manager simulation",
        "Acknowledgment of growth area (cloud) to show self-awareness",
    ]

    return CoverLetter(
        content=letter.strip(),
        tone=tone,
        word_count=len(letter.split()),
        key_signals_used=key_signals,
    )


def _api_cover_letter(
    resume_text: str,
    job_description: str,
    company: str,
    result: dict,
    tone: Literal["Professional", "Confident", "Direct"],
    brutal_context: bool = False,
) -> CoverLetter:
    """Generate a genuinely tailored cover letter using Anthropic API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _heuristic_cover_letter(resume_text, job_description, company, result, tone)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        skills = result.get("skills", {})
        exp    = result.get("experience", {})
        coord  = result.get("coordinator", {})
        hm     = result.get("hiring_manager", {})

        signals = {
            "strongest_matched_skills": [s.get("skill") for s in skills.get("matched_skills", [])[:4]],
            "best_experience_bullets": exp.get("best_bullets", [])[:2],
            "green_flags_hiring_manager_noticed": hm.get("green_flags", [])[:3],
            "primary_gap_to_acknowledge": coord.get("top_3_fixable_gaps", [{}])[0].get("gap", "") if coord.get("top_3_fixable_gaps") else "",
            "encouragement": coord.get("encouragement", ""),
            "application_verdict": coord.get("application_verdict", ""),
        }

        tone_instruction = {
            "Professional": "formal and professional — measured confidence, third-person achievement framing",
            "Confident": "confident and direct — first-person ownership language, strong action verbs",
            "Direct": "concise and direct — every sentence earns its place, no fluff, shorter paragraphs",
        }.get(tone, "professional")

        prompt = f"""Write a targeted, non-generic cover letter for this job application.

TONE: {tone_instruction}

COMPANY: {company}

JOB DESCRIPTION (excerpt):
{job_description[:1000]}

RESUME (excerpt):
{resume_text[:1000]}

KEY SIGNALS FROM AI ANALYSIS:
{str(signals)}

REQUIREMENTS:
- Do NOT use generic phrases like "I am a passionate engineer" or "I have always loved technology"
- Reference specific signals from the analysis above
- Acknowledge one area of growth (the primary gap) — hiring managers respect self-awareness
- Keep under 350 words
- Do NOT use placeholders like [Your Name] — write the letter as-is
- End with a clear, confident call to action

Write only the letter text — no subject line, no markdown.
"""
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text.strip()

        key_signals = [
            f"Matched skills: {', '.join(signals['strongest_matched_skills'][:3])}",
            f"Best achievement: {signals['best_experience_bullets'][0][:60]}..." if signals['best_experience_bullets'] else "Experience highlights",
            f"Gap acknowledged: {signals['primary_gap_to_acknowledge'][:50]}..." if signals['primary_gap_to_acknowledge'] else "",
        ]

        return CoverLetter(
            content=content,
            tone=tone,
            word_count=len(content.split()),
            key_signals_used=[s for s in key_signals if s],
        )

    except Exception:
        return _heuristic_cover_letter(resume_text, job_description, company, result, tone)


def generate_cover_letter(
    resume_text: str,
    job_description: str,
    company: str,
    result: dict,
    tone: Literal["Professional", "Confident", "Direct"] = "Confident",
) -> CoverLetter:
    """Main entry. Generates a cover letter tailored to the analysis signals."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _api_cover_letter(resume_text, job_description, company, result, tone)
    return _heuristic_cover_letter(resume_text, job_description, company, result, tone)
