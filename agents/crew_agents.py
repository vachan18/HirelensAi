"""
HireLens AI — Specialist Multi-Agent Crew (v2)

Five deeply-prompted specialist agents, each operating as a genuine domain expert:

  1. ATS Compliance Agent    — acts as an ATS parsing engine + compliance auditor
  2. Skills Gap Agent        — acts as a technical hiring manager / senior recruiter
  3. Experience Agent        — acts as an engineering director evaluating impact
  4. Hiring Manager Agent    — simulates the actual hiring manager's decision logic
  5. Coordinator Agent       — synthesises all signals into a structured career action plan

Design principles:
  - Each agent has a detailed role identity, domain expertise, and mental model
  - Task prompts provide explicit scoring rubrics and evaluation frameworks
  - All outputs are validated against Pydantic v2 schemas before downstream use
  - Coordinator receives clean validated JSON (not raw LLM text) from all four agents
  - Brutal mode toggles tone without changing analytical depth
"""

from __future__ import annotations
import json
import re

from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

from config import get_llm_config, get_app_config
from utils.logger import get_logger, AgentLogger
from models.schemas import (
    ATSOutput,
    SkillsGapOutput,
    ExperienceOutput,
    HiringManagerOutput,
    CoordinatorOutput,
    HireLensResult,
)

log = get_logger(__name__)
cfg = get_app_config()


# ══════════════════════════════════════════════════════════════════
#  LLM FACTORY
# ══════════════════════════════════════════════════════════════════

def build_llm() -> LLM:
    llm_cfg = get_llm_config()
    model_str = llm_cfg.active_model
    log.info(f"LLM | provider={llm_cfg.provider} model={model_str}")
    return LLM(model=model_str)


# ══════════════════════════════════════════════════════════════════
#  AGENT DEFINITIONS  — Specialist Personas
# ══════════════════════════════════════════════════════════════════

def create_ats_agent(llm: LLM) -> Agent:
    return Agent(
        role="ATS Compliance Specialist & Resume Parsing Expert",
        goal=(
            "Act as an Applicant Tracking System combined with a resume compliance auditor. "
            "Parse and score this resume exactly as enterprise ATS software would — evaluating "
            "keyword density, section structure, formatting parsability, and job description alignment. "
            "Produce a precise, scored compliance report with actionable fixes ranked by impact."
        ),
        backstory=(
            "You spent 8 years building ATS software at companies like Workday, Greenhouse, and Lever "
            "before becoming a resume compliance consultant. You have reverse-engineered how ATS systems "
            "actually score resumes — you know that 75% of resumes are rejected before a human sees them, "
            "and you know exactly why. You think in keyword frequency tables, section weights, and parse "
            "confidence scores. You are not a cheerleader — you flag every compliance failure with "
            "surgical precision. You know the difference between what candidates THINK ATS systems check "
            "and what they ACTUALLY check. You evaluate: (1) hard keyword matches vs JD, (2) section "
            "detection reliability, (3) formatting red flags that break parsers, (4) title/header alignment "
            "with common ATS taxonomies, and (5) contact information completeness. "
            "Your score rubric: 90-100 = top-tier ATS pass, 70-89 = likely pass with minor risk, "
            "50-69 = borderline — may pass or fail depending on applicant volume, "
            "30-49 = likely filtered out, 0-29 = almost certain rejection at ATS stage."
        ),
        llm=llm,
        verbose=cfg.crew_verbose,
        allow_delegation=False,
    )


def create_skills_gap_agent(llm: LLM) -> Agent:
    return Agent(
        role="Technical Skills Gap Analyst & Hiring Market Specialist",
        goal=(
            "Act as a technical hiring manager who has personally reviewed thousands of resumes "
            "for roles matching this job description. Perform a rigorous, evidence-based skills "
            "gap analysis — comparing what the candidate demonstrably has against what this role "
            "explicitly and implicitly requires. Rank missing skills by hiring impact, not "
            "alphabetically. Identify which gaps are knockout criteria vs nice-to-haves."
        ),
        backstory=(
            "You are a Staff Engineer turned Engineering Manager who has been the technical "
            "screener for over 200 engineering hires at companies ranging from Series A startups "
            "to FAANG. You track technology trends closely — you know which skills are genuinely "
            "scarce vs oversupplied in the market. You think in terms of skill adjacency: "
            "a React developer might be 80% of the way to Vue, but a Python developer is 0% of "
            "the way to Rust. You evaluate skills on three axes: (1) Is it explicitly required "
            "in the JD? (2) Is it implicitly assumed given the role level? (3) Is the candidate's "
            "claimed proficiency credible given their experience evidence? "
            "You never accept 'familiar with' as Advanced proficiency. You know that 'used in a "
            "side project' is Beginner, 'used professionally for 1 year' is Intermediate, "
            "'led architecture decisions' is Advanced, 'trained others / wrote the book' is Expert. "
            "You estimate realistic learning timelines based on market data: Kubernetes fundamentals "
            "= 3-6 weeks, AWS Solutions Architect Associate = 6-8 weeks, production-ready Terraform = 3-4 weeks."
        ),
        llm=llm,
        verbose=cfg.crew_verbose,
        allow_delegation=False,
    )


def create_experience_agent(llm: LLM) -> Agent:
    return Agent(
        role="Experience & Impact Evaluation Director",
        goal=(
            "Evaluate the candidate's actual experience depth, project relevance, and impact "
            "evidence with the rigor of an Engineering Director deciding who advances to interviews. "
            "Assess whether experience bullets tell a story of ownership and measurable impact, "
            "or passive participation. Identify the strongest and weakest experience evidence. "
            "Score projects for relevance and evaluate internship and early-career experience quality."
        ),
        backstory=(
            "You are a Director of Engineering who has personally conducted 500+ technical screens "
            "and built hiring rubrics at three different companies. You have a pathological aversion "
            "to vague resume bullets. When you see 'Worked on backend features,' you immediately "
            "think: worked on HOW? for HOW LONG? with what IMPACT? You evaluate experience on the "
            "STAR framework — every bullet should have a Situation, Task, Action, and Result implied. "
            "You know the difference between real experience (built from scratch, owned the oncall, "
            "drove the decision) and supporting experience (reviewed PRs, attended meetings, 'helped'). "
            "For projects, you evaluate: (1) Is this relevant to the target domain? (2) Does it show "
            "engineering depth or surface-level CRUD work? (3) Is the scale credible? (4) Would this "
            "impress someone who has solved similar problems at scale? "
            "For internships, you ask: Was there ownership? Did they ship something real? "
            "You rewrite bullets mentally into their STAR form to assess what actually happened. "
            "Your scoring rubric for impact_rating: Strong = 70%+ bullets have quantified outcomes, "
            "Moderate = 30-69% quantified, Weak = under 30% quantified or all bullets are passive."
        ),
        llm=llm,
        verbose=cfg.crew_verbose,
        allow_delegation=False,
    )


def create_hiring_manager_agent(llm: LLM) -> Agent:
    return Agent(
        role="Hiring Manager Decision Simulator",
        goal=(
            "Think and reason exactly like the hiring manager who posted this specific job. "
            "Simulate the real hiring decision process: the 6-second first scan, the deeper read, "
            "the comparison against the mental model of the ideal candidate, and the decision "
            "to shortlist or reject. Be explicit about which signals drove the decision. "
            "Generate the actual rejection reasoning a recruiter would give."
        ),
        backstory=(
            "You are a VP of Engineering who has managed hiring pipelines for 5+ years. You've "
            "seen every type of resume. In your first 6 seconds, you are asking: Does this person "
            "have the core skills? Is the experience level right? Does the career story make sense "
            "for this role? You know that most rejections happen for one of five reasons: "
            "(1) Missing a non-negotiable skill listed in the JD, "
            "(2) Experience level too junior or too senior, "
            "(3) Career trajectory doesn't point toward this role, "
            "(4) Resume tells no compelling story — just a list of jobs, "
            "(5) Red flags that create risk — too many short stints, unexplained gaps, "
            "claims that don't add up. "
            "You evaluate culture fit signals: Has this person worked in similar team structures? "
            "Do they show initiative and ownership language or just execution language? "
            "You think about the BUSINESS context: what problem does this role solve? Does this "
            "candidate's background suggest they can solve it in the first 90 days? "
            "When you write rejection emails, you write the polite version — but you know the real reason. "
            "You call out knockout factors specifically: things that would immediately remove someone "
            "from consideration regardless of everything else. "
            "For green flags, you note what made you pause before rejecting — the evidence that "
            "this person might be worth a stretch."
        ),
        llm=llm,
        verbose=cfg.crew_verbose,
        allow_delegation=False,
    )


def create_coordinator_agent(llm: LLM) -> Agent:
    return Agent(
        role="Career Strategy Synthesis Coordinator",
        goal=(
            "Synthesise the outputs of four specialist agents into a single, actionable career "
            "coaching report. Identify the ROOT CAUSE of likely rejection — not symptoms, but "
            "the actual decision driver. Produce a ranked action plan with realistic timelines "
            "and a concrete 30-day improvement roadmap. Be specific: name exact skills, exact "
            "resources, exact resume edits. Do not give generic advice."
        ),
        backstory=(
            "You are a principal-level career strategist who has coached 300+ engineers, "
            "data scientists, and product managers into top-tier roles at companies like Google, "
            "Stripe, Airbnb, and Anthropic. You think in root causes, not symptoms. "
            "You know that 'your resume needs improvement' is useless advice. "
            "Useful advice sounds like: 'Your ATS score is 54 because you haven't used the word "
            "'Kubernetes' once, and it appears 6 times in the JD — fix this in 10 minutes by "
            "adding it to your Skills section and one bullet point.' "
            "You synthesise signals across agents: if the ATS score is low AND skills match is low, "
            "the root cause is probably keyword strategy, not actual skill gaps. If ATS is fine "
            "but hiring manager score is low, the issue is narrative and impact presentation. "
            "You categorise the root cause precisely from: Skills Gap, Experience Level, "
            "ATS Filtering, Narrative Clarity, Cultural Fit, Overqualified, or Multiple. "
            "Your 30-day roadmap is week-by-week, each week has a focused theme and 3 concrete "
            "actions. Each week has a success metric so the candidate knows when they're done. "
            "You compare this candidate to what a typical shortlisted candidate looks like for "
            "this role — that comparison is where the insight lives. "
            "You end with genuine encouragement based on ONE specific, real strength you observed."
        ),
        llm=llm,
        verbose=cfg.crew_verbose,
        allow_delegation=False,
    )


# ══════════════════════════════════════════════════════════════════
#  TASK DEFINITIONS — Specialist Prompts with Scoring Rubrics
# ══════════════════════════════════════════════════════════════════

def _tone(brutal: bool, harsh: str, soft: str) -> str:
    return harsh if brutal else soft


def ats_task(agent: Agent, resume: str, job_desc: str, company: str, brutal: bool) -> Task:
    tone = _tone(
        brutal,
        "Apply maximum scrutiny. Every compliance failure must be named explicitly. No diplomatic softening.",
        "Be direct and precise. Every issue named must be specific and actionable.",
    )
    return Task(
        description=f"""
You are an ATS system AND a compliance auditor combined. Parse and evaluate this resume
as enterprise ATS software would, then explain exactly what you found.

TARGET COMPANY: {company}
EVALUATION MODE: {tone}

═══════════════════════════════════════
RESUME TEXT:
═══════════════════════════════════════
{resume}

═══════════════════════════════════════
JOB DESCRIPTION:
═══════════════════════════════════════
{job_desc}

═══════════════════════════════════════
YOUR EVALUATION FRAMEWORK:
═══════════════════════════════════════

STEP 1 — KEYWORD EXTRACTION
Extract all technical skills, tools, frameworks, methodologies, and role-specific terms from
the JD. These are the exact strings an ATS would match against. Then check which appear
verbatim (or as close variants) in the resume.

STEP 2 — SECTION STRUCTURE AUDIT
Verify standard resume sections exist and are correctly named. ATS systems look for
recognisable section headers: Summary/Profile/Objective, Skills/Technical Skills/Core Competencies,
Experience/Work History/Employment, Education/Academic Background, Contact/Contact Info.
Non-standard headers reduce parse confidence.

STEP 3 — FORMATTING COMPLIANCE CHECKS
Evaluate: use of tables/columns (breaks many parsers), graphics/logos (unreadable),
headers/footers with contact info (often skipped), unusual bullet characters, multi-column
layouts, embedded images. Each is a specific compliance failure.

STEP 4 — SCORE CALCULATION
Score each dimension 0-100:
  - Keyword Match (weight 40%): matched_keywords / total_jd_keywords * 100
  - Section Structure (weight 25%): all 5 sections present and correctly named
  - Format Parsability (weight 20%): no formatting violations
  - Contact Completeness (weight 15%): name, email, phone, LinkedIn/GitHub
Overall ATS score = weighted average of all four dimensions.

STEP 5 — RISK RANKING
Identify top ATS risks in order of rejection impact. The most common causes of ATS rejection:
1. Missing exact keyword from JD title (e.g. JD says "Kubernetes" but resume never uses it)
2. Incorrect section headers
3. Multi-column layout
4. Missing contact information
5. Very low keyword density

STEP 6 — QUICK FIXES
Identify fixes that take under 24 hours. Examples:
- "Add 'Kubernetes' to Skills section (appears 4x in JD)"
- "Rename 'Work History' header to 'Work Experience'"
- "Add GitHub profile URL to contact section"

Return a JSON object with EXACTLY this structure — no extra keys, no markdown:
{{
  "ats_score": <integer 0-100>,
  "pass_fail": "<PASS|BORDERLINE|FAIL>",
  "keyword_matches": ["<exact keyword matched>", ...],
  "missing_keywords": ["<exact keyword from JD not in resume>", ...],
  "keyword_density_pct": <integer 0-100, pct of JD keywords found in resume>,
  "formatting_issues": ["<specific formatting violation with location>", ...],
  "format_checks": [
    {{"check": "<check name>", "status": "<PASS|WARN|FAIL>", "detail": "<what was found>"}}
  ],
  "section_audit": {{
    "has_summary": <true|false>,
    "has_skills": <true|false>,
    "has_experience": <true|false>,
    "has_education": <true|false>,
    "has_contact": <true|false>
  }},
  "score_breakdown": {{
    "keyword_match": <0-100>,
    "section_structure": <0-100>,
    "format_parsability": <0-100>,
    "contact_completeness": <0-100>
  }},
  "top_ats_risks": ["<ranked rejection risk 1>", "<ranked rejection risk 2>", ...],
  "quick_ats_fixes": ["<specific fix with time estimate>", ...],
  "ats_verdict": "<2-3 sentence precise summary of ATS compliance status and primary risk>"
}}

Return ONLY the JSON object. No markdown fences, no explanation text.
""",
        agent=agent,
        expected_output="JSON object: ATS compliance analysis with keyword audit, format checks, score breakdown, and ranked fixes.",
    )


def skills_gap_task(agent: Agent, resume: str, job_desc: str, company: str, brutal: bool) -> Task:
    tone = _tone(
        brutal,
        "Name every gap without softening. Distinguish between genuine skills and resume padding.",
        "Be specific and evidence-based. Credit real skills, flag exaggerated claims.",
    )
    return Task(
        description=f"""
You are a technical hiring manager who has personally screened thousands of candidates for
roles similar to this one. Perform a rigorous, evidence-based skills gap analysis.

TARGET COMPANY: {company}
EVALUATION MODE: {tone}

═══════════════════════════════════════
RESUME TEXT:
═══════════════════════════════════════
{resume}

═══════════════════════════════════════
JOB DESCRIPTION:
═══════════════════════════════════════
{job_desc}

═══════════════════════════════════════
YOUR EVALUATION FRAMEWORK:
═══════════════════════════════════════

STEP 1 — JD SKILLS EXTRACTION
Extract ALL skills from the JD, categorised as:
  - Required (explicitly stated as required/must-have/essential)
  - Preferred (stated as preferred/nice-to-have/bonus)
  - Implied (not stated but expected at this role level — e.g. "Senior Engineer" implies
    system design, code review, mentoring)

STEP 2 — EVIDENCE-BASED SKILL MATCHING
For each skill the candidate claims, assess evidence quality:
  - Expert: led architecture, trained others, public talks, authored documentation
  - Advanced: used professionally for 2+ years, made key decisions
  - Intermediate: used professionally for 1 year, followed patterns set by others
  - Beginner: used in a side project, course, or briefly at work
  - Claimed but Unverifiable: listed but no evidence in experience bullets

STEP 3 — GAP SEVERITY CLASSIFICATION
For missing required skills, classify:
  - Critical: JD says "required" AND it's core to day-1 work — absence = automatic rejection
  - High: listed as required but a strong candidate could potentially bridge it
  - Medium: preferred or implied — absence reduces score but isn't knockout

STEP 4 — LEARNING PATH ESTIMATION
For each critical/high gap, provide:
  - Realistic days to functional proficiency (based on typical learning curves)
  - A specific recommended resource (named course, cert, or project type)

STEP 5 — TRANSFERABLE SKILLS
Identify skills the candidate has that partially substitute for missing ones.
Example: "Strong Python + experience with async frameworks partially compensates for
lack of Node.js experience listed as preferred."

STEP 6 — TOP 5 MISSING (for quick display)
Rank the 5 most impactful missing skills in order of hiring decision weight.

Return a JSON object with EXACTLY this structure — no extra keys, no markdown:
{{
  "match_score": <integer 0-100>,
  "matched_skills": [
    {{
      "skill": "<skill name>",
      "evidence": "<specific resume evidence: company name + use case>",
      "proficiency": "<Beginner|Intermediate|Advanced|Expert>",
      "jd_importance": "<Required|Preferred|Nice-to-have>"
    }}
  ],
  "missing_critical": [
    {{
      "skill": "<skill name>",
      "importance": "<Critical|High|Medium>",
      "learn_time_days": <integer>,
      "why_it_matters": "<1 sentence: why this specific skill matters for this specific role>",
      "recommended_resource": "<specific course name, cert, or project type>"
    }}
  ],
  "missing_nice_to_have": ["<skill>", ...],
  "overqualified_areas": ["<area where candidate exceeds requirements>", ...],
  "transferable_skills": ["<transferable skill and its substitution value>", ...],
  "top_5_missing": ["<most impactful missing skill>", "<second>", "<third>", "<fourth>", "<fifth>"],
  "skill_trajectory": "<Is the candidate's career moving toward or away from this role's tech stack? 1-2 sentences.>",
  "skills_verdict": "<2-3 sentence precise assessment of skills match, including the single most important gap>"
}}

Return ONLY the JSON object. No markdown fences, no explanation text.
""",
        agent=agent,
        expected_output="JSON object: Evidence-based skills gap analysis with ranked missing skills, transferable skills, and learning paths.",
    )


def experience_task(agent: Agent, resume: str, job_desc: str, company: str, brutal: bool) -> Task:
    tone = _tone(
        brutal,
        "Dissect every weak bullet. Show exactly what information is missing and why it matters.",
        "Be specific in your critique. Each identified weakness must have a concrete fix.",
    )
    return Task(
        description=f"""
You are an Engineering Director who has evaluated hundreds of candidates using structured
hiring rubrics. Evaluate this candidate's experience quality, project relevance, and impact
evidence with complete honesty.

TARGET COMPANY: {company}
EVALUATION MODE: {tone}

═══════════════════════════════════════
RESUME TEXT:
═══════════════════════════════════════
{resume}

═══════════════════════════════════════
JOB DESCRIPTION:
═══════════════════════════════════════
{job_desc}

═══════════════════════════════════════
YOUR EVALUATION FRAMEWORK:
═══════════════════════════════════════

STEP 1 — SENIORITY CALIBRATION
Extract years of relevant experience. Compare against JD requirement.
Assess level signals beyond years: Are titles progressing? Did they go from IC to tech lead?
Do they show expanding scope and responsibility?
Seniority match: Under = 2+ years below requirement, Match = within 1 year, Over = 3+ years above.

STEP 2 — DOMAIN RELEVANCE SCORING
How closely does their experience domain match this role?
High: Same industry + same tech stack + same scale
Medium: Same tech stack but different industry or scale
Low: Different tech stack, different domain, limited transferability

STEP 3 — BULLET QUALITY AUDIT
For each bullet point in the resume, mentally ask:
  - Does it start with a strong action verb (Led, Built, Designed, Reduced) or a weak/passive one?
  - Does it have a quantified outcome (%, $, users, time, scale)?
  - Does it show ownership or just participation?
  - Would this bullet be impressive to someone who has done similar work?

Select the 3-5 WEAKEST bullets for detailed critique. For each:
  - bullet_excerpt: first 10-12 words of the original
  - issue: specific diagnosis (vague verb / no metric / no context / passive voice / claim without evidence)
  - fix: concrete instruction for what to add/change
  - rewritten: your rewritten version of the bullet in STAR format with a placeholder metric

Also identify the 2-3 BEST bullets — these are evidence of real impact.

STEP 4 — PROJECT EVALUATION
Identify all projects and roles mentioned. For each significant one, evaluate:
  - title: project or company name
  - relevance: High/Medium/Low to this role
  - impact_clarity: Strong (metric + outcome) / Moderate (outcome but no metric) / Weak (activity only)
  - missing_info: what context would have made this more compelling

STEP 5 — CAREER PROGRESSION SIGNAL
  Strong: Clear upward trajectory, increasing responsibility, expanding scope
  Lateral: Same level across roles, no clear progression signal
  Unclear: Jobs seem disconnected, hard to see a narrative

STEP 6 — INTERNSHIP QUALITY (if applicable)
  Strong: Owned a real project, shipped code to production, measurable output
  Average: Standard intern work, basic CRUD, unclear impact
  Weak: Vague description, no technical depth evident
  None: No internships or early-career experience present

Return a JSON object with EXACTLY this structure — no extra keys, no markdown:
{{
  "experience_score": <integer 0-100>,
  "years_required": <integer or null if not specified in JD>,
  "years_apparent": <integer or null if not determinable from resume>,
  "seniority_match": "<Under|Match|Over>",
  "domain_relevance": "<High|Medium|Low>",
  "impact_rating": "<Strong|Moderate|Weak>",
  "quantification_score": <integer 0-100, estimated % of bullets with quantified outcomes>,
  "action_verb_quality": "<Strong|Mixed|Weak>",
  "bullet_quality": [
    {{
      "bullet_excerpt": "<first 10-12 words of original bullet>",
      "issue": "<specific diagnosis: what is wrong and why>",
      "fix": "<concrete instruction: what to add, change, or remove>",
      "rewritten": "<your rewritten version in STAR format with placeholder metric>"
    }}
  ],
  "best_bullets": ["<verbatim excerpt of strongest bullet 1>", "<strongest bullet 2>"],
  "weakest_bullets": ["<verbatim excerpt of weakest bullet 1>", "<weakest bullet 2>"],
  "project_evaluations": [
    {{
      "title": "<project or company name>",
      "relevance": "<High|Medium|Low>",
      "impact_clarity": "<Strong|Moderate|Weak>",
      "missing_info": "<what context is absent>"
    }}
  ],
  "career_progression": "<Strong|Lateral|Unclear>",
  "internship_quality": "<Strong|Average|Weak|None>",
  "experience_verdict": "<2-3 sentence honest assessment: seniority fit, strongest evidence, biggest experience gap>"
}}

Return ONLY the JSON object. No markdown fences, no explanation text.
""",
        agent=agent,
        expected_output="JSON object: Experience evaluation with seniority assessment, bullet-level critique with rewrites, and project evaluations.",
    )


def hiring_manager_task(agent: Agent, resume: str, job_desc: str, company: str, brutal: bool) -> Task:
    tone = _tone(
        brutal,
        "Think like the bluntest hiring manager in the room. State your actual reasoning, not the polite version.",
        "Be honest about your reasoning. Name what would actually cause the rejection decision.",
    )
    return Task(
        description=f"""
You are the hiring manager who posted this job. Simulate your actual decision process:
the first scan, the deeper read, and the final shortlist/reject decision.

TARGET COMPANY: {company}
EVALUATION MODE: {tone}

═══════════════════════════════════════
RESUME TEXT:
═══════════════════════════════════════
{resume}

═══════════════════════════════════════
JOB DESCRIPTION:
═══════════════════════════════════════
{job_desc}

═══════════════════════════════════════
YOUR EVALUATION FRAMEWORK:
═══════════════════════════════════════

STEP 1 — THE 6-SECOND FIRST SCAN
You spend 6 seconds on a resume before deciding whether to read further.
In those 6 seconds you check: current/most recent title, top company or school,
and whether the experience length is roughly right.
Write exactly what you think and feel in that first scan.
Rate headline_strength: Strong (immediately compelling), Adequate (neither impressive nor dismissive),
Weak (first impression is negative or neutral).

STEP 2 — KNOCKOUT FACTOR CHECK
What would make you immediately reject this resume without reading further?
  - Missing a technology you listed as required
  - Experience 3+ years below requirement
  - Career pivot with no bridge
  - Red flag patterns (multiple very short tenures, unexplained gaps)
List any knockout_factors. If none exist, leave this empty.

STEP 3 — DEEP READ (if no knockout)
Now read carefully. You are asking:
  - Does their experience actually solve the problem my team has?
  - Have they done this exact kind of work before?
  - Do the impact claims add up? Do numbers look credible?
  - Is there a pattern of ownership or just execution?
  - What is the story of this candidate's career, and does it point to this role?

STEP 4 — RED AND GREEN FLAGS
Red flags: patterns that create doubt or increase hiring risk
  Examples: "Worked at 4 companies in 3 years", "All bullets are 'helped' or 'assisted'",
  "Skills list has 30 technologies with no evidence depth"
Green flags: evidence that creates confidence despite weaknesses
  Examples: "Built payment system handling real transaction volume",
  "Led a migration that reduced costs — actual number given"

STEP 5 — REJECTION REASONING (detailed)
Even if you might shortlist, think through why a typical hiring manager would reject.
For each rejection reason:
  - reason: the specific reason (not generic)
  - severity: Knockout (instant reject) / Major (strong push toward reject) / Minor (noted but not decisive)
  - fixable: can this be addressed before reapplying?
  - how_to_fix: specific action the candidate can take

STEP 6 — REJECTION EMAIL DRAFT
Write the one-sentence version that a recruiter would send. Make it sound like the real
polite rejection email — not the actual reason, the polite version.

STEP 7 — IF YOU WERE GOING TO INTERVIEW THEM
List 2-3 talking_points you'd want to discuss in a phone screen — the things that would
make you give them a chance despite the weaknesses.

STEP 8 — WOULD YOU INTERVIEW?
Yes = confident shortlist. Maybe = on the fence, would compare to pile before deciding.
No = clear reject.

Return a JSON object with EXACTLY this structure — no extra keys, no markdown:
{{
  "gut_score": <integer 0-100, your overall gut confidence this is the right hire>,
  "would_interview": "<Yes|Maybe|No>",
  "decision_confidence": "<High|Medium|Low>",
  "first_impression": "<exact thought you have in the 6-second first scan>",
  "headline_strength": "<Strong|Adequate|Weak>",
  "red_flags": ["<specific red flag with evidence>", ...],
  "green_flags": ["<specific green flag with evidence>", ...],
  "knockout_factors": ["<instant disqualifier if any>", ...],
  "rejection_reasons": [
    {{
      "reason": "<specific rejection reason>",
      "severity": "<Knockout|Major|Minor>",
      "fixable": <true|false>,
      "how_to_fix": "<concrete fix the candidate can take>"
    }}
  ],
  "rejection_email_draft": "<polite one-sentence rejection a recruiter would send>",
  "culture_fit_signals": "<1-2 sentence assessment of culture fit based on available signals>",
  "narrative_arc": "<Is the career story coherent and pointing toward this role? 1-2 sentences.>",
  "interview_talking_points": ["<thing you'd want to discuss in phone screen>", ...],
  "hiring_manager_verdict": "<2-3 sentence honest assessment of the hire decision and the primary reason>"
}}

Return ONLY the JSON object. No markdown fences, no explanation text.
""",
        agent=agent,
        expected_output="JSON object: Hiring manager decision simulation with structured rejection reasoning, flags, and interview assessment.",
    )


def coordinator_task(
    agent: Agent,
    resume: str,
    job_desc: str,
    company: str,
    brutal: bool,
    ats_json: str,
    skills_json: str,
    experience_json: str,
    hiring_json: str,
) -> Task:
    tone = _tone(
        brutal,
        "Be a brilliant, unsentimental career strategist. Diagnose exactly what is broken and exactly how to fix it. Every recommendation must be specific, not generic.",
        "Be honest, empathetic, and actionable. Every recommendation must be specific enough to execute today.",
    )
    return Task(
        description=f"""
You are a senior career strategist synthesising four specialist agent analyses into one
coherent, actionable report. Your job is to find the ROOT CAUSE of rejection — not list
every symptom — and produce a specific, executable action plan.

TARGET COMPANY: {company}
APPROACH: {tone}

═══════════════════════════════════════
CANDIDATE PROFILE SUMMARY:
═══════════════════════════════════════
Resume (first 600 chars): {resume[:600]}
JD (first 600 chars): {job_desc[:600]}

═══════════════════════════════════════
ATS COMPLIANCE ANALYSIS:
═══════════════════════════════════════
{ats_json}

═══════════════════════════════════════
SKILLS GAP ANALYSIS:
═══════════════════════════════════════
{skills_json}

═══════════════════════════════════════
EXPERIENCE EVALUATION:
═══════════════════════════════════════
{experience_json}

═══════════════════════════════════════
HIRING MANAGER SIMULATION:
═══════════════════════════════════════
{hiring_json}

═══════════════════════════════════════
YOUR SYNTHESIS FRAMEWORK:
═══════════════════════════════════════

STEP 1 — ROOT CAUSE IDENTIFICATION
Look across all four analyses and ask: what is the SINGLE most decisive reason this
application would fail? Not the longest list of problems — the primary driver.
Classify it as one of:
  - Skills Gap: Missing required technical skills
  - Experience Level: Wrong seniority for the role
  - ATS Filtering: Never made it past the automated screen
  - Narrative Clarity: Experience exists but story is unclear/uncompelling
  - Cultural Fit: Signals don't match what the team is looking for
  - Overqualified: Likely rejected for being too senior
  - Multiple: Two or more factors equally decisive

STEP 2 — IMPACT RANKING OF FIXES
Rank the top 3 fixable problems by their impact on acceptance probability.
For each:
  - gap: the specific problem (not category, but actual problem)
  - impact: why THIS specific problem matters for THIS specific role
  - fix: exact action — what file to edit, what skill to learn, what project to build
  - effort: Days (under 48h), Weeks (1-4 weeks), Months (1-3 months)
  - priority: 1 = highest impact fix

STEP 3 — QUICK WINS (under 48 hours)
Identify 3-5 specific actions that take under 48 hours and would meaningfully improve
the application. These must be SPECIFIC:
  Good: "Add 'Kubernetes' to Skills section — it appears 6 times in JD"
  Bad: "Improve skills section"

STEP 4 — 30-DAY ROADMAP
Week-by-week action plan. Each week:
  - theme: one focused area (not generic)
  - actions: 3 concrete, executable tasks
  - success_metric: how to know this week's goal is complete

STEP 5 — APPLICATION VERDICT
Based on current state:
  - Apply Now: likely to get past ATS and recruiter screen as-is
  - Apply After Fixes: would benefit significantly from quick fixes before applying
  - Not Ready Yet: fundamental gaps that take weeks/months to address

STEP 6 — SUCCESS ESTIMATE
If the candidate completes all top 3 fixes, estimate the new probability of passing
the recruiter screen (0-100). Be calibrated — if all fixes are minor, improvement is minor.

STEP 7 — COMPETITOR COMPARISON
In 2 sentences, describe what a typical shortlisted candidate for this role looks like
compared to this candidate. Be specific about the gap.

STEP 8 — OVERALL SCORE
Weighted average: ATS (20%) + Skills (30%) + Experience (30%) + HM Gut (20%).
Do not round up. Be honest about a score of 45 if the data says 45.

Return a JSON object with EXACTLY this structure — no extra keys, no markdown:
{{
  "overall_score": <weighted integer 0-100>,
  "rejection_probability": "<Very High|High|Medium|Low>",
  "root_cause_category": "<Skills Gap|Experience Level|ATS Filtering|Narrative Clarity|Cultural Fit|Overqualified|Multiple>",
  "primary_rejection_reason": "<1-2 sentence specific root cause — not generic>",
  "secondary_rejection_reasons": ["<specific secondary reason>", ...],
  "top_3_fixable_gaps": [
    {{
      "gap": "<specific gap — not a category>",
      "impact": "<why this specific gap matters for this specific role>",
      "fix": "<specific executable action>",
      "effort": "<Days|Weeks|Months>",
      "priority": <1|2|3>
    }}
  ],
  "quick_wins": ["<specific action under 48h with expected improvement>", ...],
  "30_day_roadmap": [
    {{
      "week": 1,
      "theme": "<focused week theme>",
      "actions": ["<concrete action 1>", "<concrete action 2>", "<concrete action 3>"],
      "success_metric": "<measurable signal that this week is complete>"
    }},
    {{
      "week": 2,
      "theme": "<focused week theme>",
      "actions": ["<concrete action 1>", "<concrete action 2>", "<concrete action 3>"],
      "success_metric": "<measurable signal that this week is complete>"
    }},
    {{
      "week": 3,
      "theme": "<focused week theme>",
      "actions": ["<concrete action 1>", "<concrete action 2>", "<concrete action 3>"],
      "success_metric": "<measurable signal that this week is complete>"
    }},
    {{
      "week": 4,
      "theme": "<focused week theme>",
      "actions": ["<concrete action 1>", "<concrete action 2>", "<concrete action 3>"],
      "success_metric": "<measurable signal that this week is complete>"
    }}
  ],
  "application_verdict": "<Apply Now|Apply After Fixes|Not Ready Yet>",
  "estimated_success_after_fixes": <integer 0-100>,
  "final_verdict": "<3 sentence honest overall assessment: current state, primary issue, what changes the outcome>",
  "encouragement": "<1 sentence of specific, genuine encouragement based on a real strength observed>",
  "competitor_comparison": "<2 sentences: what a typical shortlisted candidate looks like vs this candidate>"
}}

Return ONLY the JSON object. No markdown fences, no explanation text.
""",
        agent=agent,
        expected_output="JSON object: Synthesised career coaching report with root cause analysis, ranked action plan, 30-day roadmap, and application verdict.",
    )


# ══════════════════════════════════════════════════════════════════
#  JSON PARSING + PYDANTIC VALIDATION
# ══════════════════════════════════════════════════════════════════

def _extract_json(raw: str) -> dict:
    """Strip markdown fences and extract the first JSON object."""
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except Exception:
                pass
    return {}


def _validate_ats(raw: str, alog: AgentLogger) -> ATSOutput:
    data = _extract_json(raw)
    try:
        result = ATSOutput.model_validate(data)
        alog.done("ats_score", result.ats_score)
        return result
    except Exception as e:
        alog.parse_error(raw)
        log.warning(f"ATS validation fallback: {e}")
        return ATSOutput(ats_score=0, pass_fail="FAIL", ats_verdict=f"Parse error: {e}")


def _validate_skills(raw: str, alog: AgentLogger) -> SkillsGapOutput:
    data = _extract_json(raw)
    try:
        result = SkillsGapOutput.model_validate(data)
        alog.done("match_score", result.match_score)
        return result
    except Exception as e:
        alog.parse_error(raw)
        log.warning(f"Skills validation fallback: {e}")
        return SkillsGapOutput(match_score=0, skills_verdict=f"Parse error: {e}")


def _validate_experience(raw: str, alog: AgentLogger) -> ExperienceOutput:
    data = _extract_json(raw)
    try:
        result = ExperienceOutput.model_validate(data)
        alog.done("experience_score", result.experience_score)
        return result
    except Exception as e:
        alog.parse_error(raw)
        log.warning(f"Experience validation fallback: {e}")
        return ExperienceOutput(experience_score=0, experience_verdict=f"Parse error: {e}")


def _validate_hiring_manager(raw: str, alog: AgentLogger) -> HiringManagerOutput:
    data = _extract_json(raw)
    try:
        result = HiringManagerOutput.model_validate(data)
        alog.done("gut_score", result.gut_score)
        return result
    except Exception as e:
        alog.parse_error(raw)
        log.warning(f"HM validation fallback: {e}")
        return HiringManagerOutput(gut_score=0, hiring_manager_verdict=f"Parse error: {e}")


def _validate_coordinator(raw: str, alog: AgentLogger) -> CoordinatorOutput:
    data = _extract_json(raw)
    try:
        result = CoordinatorOutput.model_validate(data)
        alog.done("overall_score", result.overall_score)
        return result
    except Exception as e:
        alog.parse_error(raw)
        log.warning(f"Coordinator validation fallback: {e}")
        return CoordinatorOutput(overall_score=0, final_verdict=f"Parse error: {e}")


# ══════════════════════════════════════════════════════════════════
#  MAIN ANALYSIS RUNNER
# ══════════════════════════════════════════════════════════════════

def run_hirelens_analysis(
    resume_text: str,
    job_description: str,
    company_name: str = "the company",
    brutal_mode: bool = False,
) -> HireLensResult:
    """
    Run the full 5-agent HireLens specialist pipeline.

    Pipeline:
      Tier 1 (parallel): ATS, Skills, Experience, HiringManager agents
      Tier 2 (serial):   Coordinator receives validated JSON from all Tier 1 agents

    Returns:
        HireLensResult — fully validated Pydantic model with all agent outputs.
    """
    resume = resume_text[: cfg.max_resume_chars]
    jd = job_description[: cfg.max_jd_chars]

    log.info(
        f"Analysis started | company={company_name!r} brutal={brutal_mode} "
        f"resume_chars={len(resume)} jd_chars={len(jd)}"
    )

    llm = build_llm()

    # Create specialist agents
    ats_agent    = create_ats_agent(llm)
    skills_agent = create_skills_gap_agent(llm)
    exp_agent    = create_experience_agent(llm)
    hm_agent     = create_hiring_manager_agent(llm)
    coord_agent  = create_coordinator_agent(llm)

    # Build Tier 1 tasks
    t_ats    = ats_task(ats_agent,    resume, jd, company_name, brutal_mode)
    t_skills = skills_gap_task(skills_agent, resume, jd, company_name, brutal_mode)
    t_exp    = experience_task(exp_agent,   resume, jd, company_name, brutal_mode)
    t_hm     = hiring_manager_task(hm_agent, resume, jd, company_name, brutal_mode)

    # Run Tier 1 crew
    log.info("Running Tier 1 crew: ATS | Skills | Experience | HiringManager")
    crew1 = Crew(
        agents=[ats_agent, skills_agent, exp_agent, hm_agent],
        tasks=[t_ats, t_skills, t_exp, t_hm],
        process=Process.sequential,
        verbose=cfg.crew_verbose,
    )
    crew1.kickoff()

    # Validate Tier 1 outputs
    ats_result    = _validate_ats(t_ats.output.raw if t_ats.output else "",    AgentLogger("ATS"))
    skills_result = _validate_skills(t_skills.output.raw if t_skills.output else "", AgentLogger("Skills"))
    exp_result    = _validate_experience(t_exp.output.raw if t_exp.output else "",  AgentLogger("Experience"))
    hm_result     = _validate_hiring_manager(t_hm.output.raw if t_hm.output else "", AgentLogger("HM"))

    log.info(
        f"Tier 1 complete | ats={ats_result.ats_score} "
        f"skills={skills_result.match_score} "
        f"exp={exp_result.experience_score} "
        f"hm={hm_result.gut_score}"
    )

    # Build Coordinator task with validated, clean JSON
    t_coord = coordinator_task(
        coord_agent,
        resume, jd, company_name, brutal_mode,
        ats_json=ats_result.model_dump_json(indent=2),
        skills_json=skills_result.model_dump_json(indent=2),
        experience_json=exp_result.model_dump_json(indent=2),
        hiring_json=hm_result.model_dump_json(indent=2),
    )

    # Run Tier 2 crew
    log.info("Running Tier 2 crew: Coordinator")
    crew2 = Crew(
        agents=[coord_agent],
        tasks=[t_coord],
        process=Process.sequential,
        verbose=cfg.crew_verbose,
    )
    crew2.kickoff()

    coord_result = _validate_coordinator(
        t_coord.output.raw if t_coord.output else "", AgentLogger("Coordinator")
    )

    log.info(
        f"Analysis complete | overall={coord_result.overall_score} "
        f"rejection_prob={coord_result.rejection_probability} "
        f"root_cause={coord_result.root_cause_category}"
    )

    return HireLensResult(
        ats=ats_result,
        skills=skills_result,
        experience=exp_result,
        hiring_manager=hm_result,
        coordinator=coord_result,
    )
