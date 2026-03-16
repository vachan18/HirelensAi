"""
HireLens AI — PDF Report Generator (fpdf2)
All text is sanitised to latin-1 safe characters before rendering.
"""

from __future__ import annotations
import re
import json
from datetime import datetime


def _safe(text: str, limit: int = 500) -> str:
    """Replace non-latin-1 characters and truncate."""
    text = str(text)
    replacements = {
        '\u2014': '-', '\u2013': '-', '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '*',
        '\u2192': '->', '\u2190': '<-', '\u25b6': '>', '\u25cf': '*',
        '\u2713': '+', '\u2715': 'x', '\u2191': '^', '\u2193': 'v',
    }
    for ch, rep in replacements.items():
        text = text.replace(ch, rep)
    # strip remaining non-latin-1
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text[:limit]


def generate_pdf_report(result: dict, company: str = "N/A",
                        section_scores=None, recruiter_decision=None) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return json.dumps(result, indent=2, default=str).encode("utf-8")

    coord = result.get("coordinator", {})
    ats   = result.get("ats",    {})
    sk    = result.get("skills", {})
    exp   = result.get("experience", {})
    hm    = result.get("hiring_manager", {})

    GREEN  = (16,  185, 129)
    AMBER  = (245, 158,  11)
    RED    = (239,  68,  68)
    BLUE   = (59,  130, 246)
    DARK   = (15,  23,  42)
    MID    = (100, 116, 139)

    def score_color(s: int):
        if s >= 70: return GREEN
        if s >= 45: return AMBER
        return RED

    class Report(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*MID)
            co = _safe(company, 40)
            self.cell(0, 6, f"HireLens AI  -  Analysis Report  -  {co}", align="L", ln=False)
            self.cell(0, 6, datetime.now().strftime("%Y-%m-%d"), align="R", ln=True)
            self.set_draw_color(*BLUE)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)

        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*MID)
            self.cell(0, 5, f"Page {self.page_no()} | HireLens AI", align="C")

    pdf = Report()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(12, 15, 12)

    def section_title(title: str, color=DARK):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*color)
        pdf.cell(0, 8, _safe(title, 80), ln=True)
        pdf.set_draw_color(*color)
        pdf.set_line_width(0.4)
        pdf.line(12, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    def body_text(text: str):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 5, _safe(text, 600))
        pdf.ln(1)

    def bullet_item(text: str, color=MID, prefix="*"):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*color)
        pdf.set_x(16)
        pdf.cell(6, 5, prefix, ln=False)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 5, _safe(text, 200))

    def score_row(label: str, score: int):
        c = score_color(score)
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(*DARK)
        pdf.cell(70, 7, f"  {_safe(label, 40)}", ln=False)
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*c)
        pdf.cell(20, 7, str(score), ln=False)
        bx = pdf.get_x() + 2; by = pdf.get_y() + 2
        pdf.set_fill_color(220, 230, 240)
        pdf.rect(bx, by, 60, 3, "F")
        pdf.set_fill_color(*c)
        pdf.rect(bx, by, int(60 * score / 100), 3, "F")
        pdf.ln(7)

    # PAGE 1 - COVER
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*DARK)
    pdf.ln(8)
    pdf.cell(0, 12, "HireLens AI", ln=True)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*MID)
    pdf.cell(0, 7, "Multi-Agent Job Application Analysis Report", ln=True)
    pdf.ln(4)
    pdf.set_draw_color(*GREEN)
    pdf.set_line_width(1)
    pdf.line(12, pdf.get_y(), 80, pdf.get_y())
    pdf.ln(8)

    for k, v in [
        ("Company",               _safe(company, 60) or "N/A"),
        ("Generated",             datetime.now().strftime("%B %d, %Y")),
        ("Overall Score",         f"{coord.get('overall_score',0)}/100"),
        ("Rejection Probability", _safe(coord.get("rejection_probability","N/A"), 30)),
    ]:
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*MID)
        pdf.cell(52, 6, k + ":", ln=False)
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(*DARK)
        pdf.cell(0, 6, str(v), ln=True)

    pdf.ln(8)
    for label, score in [
        ("Overall Score",        coord.get("overall_score",  0)),
        ("ATS Compliance",       ats.get("ats_score",        0)),
        ("Skills Match",         sk.get("match_score",       0)),
        ("Experience Quality",   exp.get("experience_score", 0)),
        ("Hiring Manager Score", hm.get("gut_score",         0)),
    ]:
        score_row(label, score)

    # PAGE 2 - FINAL VERDICT
    pdf.add_page()
    section_title("Final Verdict", RED)
    body_text(coord.get("final_verdict","N/A"))
    pdf.ln(2)
    section_title("Primary Rejection Reason", RED)
    body_text(coord.get("primary_rejection_reason","N/A"))
    for r in coord.get("secondary_rejection_reasons",[]):
        bullet_item(r, AMBER)
    pdf.ln(4)
    section_title("Top 3 Fixable Gaps", AMBER)
    for i, gap in enumerate(coord.get("top_3_fixable_gaps",[])[:3], 1):
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*DARK)
        pdf.cell(0, 6, f"  #{i}  {_safe(gap.get('gap',''),60)}", ln=True)
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*GREEN)
        pdf.set_x(20); pdf.multi_cell(0, 5, f"-> {_safe(gap.get('fix',''),150)}")
        pdf.ln(2)

    # PAGE 3 - ATS + SKILLS
    pdf.add_page()
    section_title("ATS Analysis", BLUE)
    c = score_color(ats.get("ats_score",0))
    pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*c)
    pdf.cell(0, 7, f"ATS Score: {ats.get('ats_score',0)}/100  [{ats.get('pass_fail','?')}]", ln=True)
    pdf.ln(1)
    body_text(ats.get("ats_verdict",""))
    for kw in ats.get("missing_keywords",[])[:10]:
        bullet_item(kw, RED, "X")
    for issue in ats.get("formatting_issues",[]):
        bullet_item(issue, AMBER, "!")
    pdf.ln(4)
    section_title("Skills Gap Analysis", BLUE)
    body_text(sk.get("skills_verdict",""))
    for s in sk.get("missing_critical",[])[:8]:
        bullet_item(
            f"{_safe(s.get('skill',''),40)} - {s.get('importance','?')} ({s.get('learn_time_days','?')}d)",
            RED
        )

    # PAGE 4 - EXPERIENCE + HM
    pdf.add_page()
    section_title("Experience Evaluation", BLUE)
    body_text(exp.get("experience_verdict",""))
    for b in exp.get("bullet_quality",[])[:4]:
        pdf.set_font("Helvetica", "I", 9); pdf.set_text_color(*MID)
        pdf.set_x(16); pdf.multi_cell(0, 5, f'"{_safe(b.get("bullet_excerpt",""),70)}..."')
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*RED); pdf.set_x(20); pdf.cell(14, 5, "Issue:", ln=False)
        pdf.set_text_color(*DARK); pdf.multi_cell(0, 5, _safe(b.get("issue",""),120))
        pdf.set_text_color(*GREEN); pdf.set_x(20); pdf.cell(14, 5, "Fix:", ln=False)
        pdf.set_text_color(*DARK); pdf.multi_cell(0, 5, _safe(b.get("fix",""),120))
        pdf.ln(2)
    pdf.ln(2)
    section_title("Hiring Manager Simulation", BLUE)
    body_text(hm.get("hiring_manager_verdict",""))
    wi_map = {"Yes": "WOULD INTERVIEW", "Maybe": "MAYBE", "No": "WOULD NOT INTERVIEW"}
    pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*DARK)
    pdf.cell(0, 6, f"Decision: {wi_map.get(hm.get('would_interview','No'),'?')}", ln=True)
    for f in hm.get("red_flags",[]):
        bullet_item(f, RED, "!")
    for f in hm.get("green_flags",[]):
        bullet_item(f, GREEN, "+")

    # PAGE 5 - ROADMAP
    pdf.add_page()
    section_title("30-Day Career Improvement Roadmap", GREEN)
    week_colors_pdf = [GREEN, BLUE, AMBER, GREEN]
    roadmap = coord.get("30_day_roadmap", coord.get("roadmap", []))
    for week in roadmap:
        wn = week.get("week","?")
        wc = week_colors_pdf[(int(wn)-1) % 4] if str(wn).isdigit() else GREEN
        pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*wc)
        pdf.cell(0, 7, f"  Week {wn} - {_safe(week.get('theme',''),50)}", ln=True)
        for action in week.get("actions",[]):
            bullet_item(action, DARK)
        pdf.ln(3)
    if coord.get("encouragement"):
        pdf.ln(4)
        section_title("One Genuine Strength", GREEN)
        body_text(coord.get("encouragement",""))

    # OPTIONAL: recruiter simulation page
    if recruiter_decision:
        pdf.add_page()
        section_title("Recruiter Decision Simulation", BLUE)
        prob = recruiter_decision.shortlist_pct
        dc = score_color(prob)
        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(*dc)
        pdf.cell(0, 8, f"Shortlist Probability: {prob}%  [{recruiter_decision.decision}]", ln=True)
        pdf.ln(2)
        for sig in recruiter_decision.signals:
            c2 = score_color(sig.raw_score)
            pdf.set_font("Helvetica", "", 9); pdf.set_text_color(*DARK)
            pdf.set_x(16); pdf.cell(80, 5, _safe(sig.name, 40), ln=False)
            pdf.set_text_color(*c2); pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, f"{sig.raw_score}/100", ln=True)
        for p in (recruiter_decision.top_positive or []):
            bullet_item(p, GREEN, "+")
        for n in (recruiter_decision.top_negative or []):
            bullet_item(n, RED, "!")

    # OPTIONAL: section scores page
    if section_scores:
        pdf.add_page()
        section_title("Resume Section Scoring", BLUE)
        for ss in section_scores:
            c2 = score_color(ss.score)
            pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(*c2)
            pdf.cell(60, 7, f"  {_safe(ss.name, 20)}", ln=False)
            pdf.cell(0, 7, f"{ss.score}/100  [{ss.grade}]", ln=True)
            for s in (ss.strengths or [])[:2]:
                bullet_item(s, GREEN, "+")
            for w in (ss.weaknesses or [])[:2]:
                bullet_item(w, AMBER, "!")
            if ss.tip:
                pdf.set_font("Helvetica", "I", 9); pdf.set_text_color(*BLUE)
                pdf.set_x(16); pdf.multi_cell(0, 5, f"Tip: {_safe(ss.tip, 200)}")
            pdf.ln(3)

    return bytes(pdf.output())
