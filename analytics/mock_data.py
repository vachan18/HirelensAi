"""
HireLens AI — Rich Mock Data for Demo Mode
Used when no API key is present. Covers all schema fields including v2 additions.
"""

MOCK_RESULT = {
    "ats": {
        "ats_score": 62,
        "pass_fail": "BORDERLINE",
        "keyword_matches": ["Python", "SQL", "REST API", "Git", "Agile", "Docker", "PostgreSQL", "Django"],
        "missing_keywords": ["Kubernetes", "Terraform", "AWS Lambda", "GraphQL", "CI/CD", "Prometheus", "Helm"],
        "keyword_density_pct": 48,
        "formatting_issues": [
            "Multi-column layout detected in skills section — many ATS parsers read columns L-to-R, garbling order",
            "Contact info placed in document footer — some parsers skip footer regions entirely",
            "Skills listed as comma-separated run-on — ATS tokenises poorly vs line-by-line",
        ],
        "format_checks": [
            {"check": "File format", "status": "PASS", "detail": "Standard text-layer PDF — parseable"},
            {"check": "Column layout", "status": "FAIL", "detail": "2-column skills section detected"},
            {"check": "Section headers", "status": "WARN", "detail": "'Work History' should be 'Work Experience'"},
            {"check": "Contact completeness", "status": "WARN", "detail": "LinkedIn URL missing"},
            {"check": "Tables/graphics", "status": "PASS", "detail": "No tables or embedded graphics found"},
            {"check": "Font readability", "status": "PASS", "detail": "Standard fonts only"},
        ],
        "section_audit": {
            "has_summary": True,
            "has_skills": True,
            "has_experience": True,
            "has_education": True,
            "has_contact": True,
        },
        "score_breakdown": {
            "keyword_match": 48,
            "section_structure": 75,
            "format_parsability": 60,
            "contact_completeness": 70,
        },
        "top_ats_risks": [
            "Kubernetes missing — appears 6× in JD as required skill",
            "Terraform missing — appears 4× in JD as required",
            "Multi-column layout may garble skills order in ATS parse",
            "'Work History' header not in standard ATS taxonomy",
            "No LinkedIn URL reduces contact completeness score",
        ],
        "quick_ats_fixes": [
            "Add 'Kubernetes' to Skills section — 5 minutes, +8 pts keyword score",
            "Add 'Terraform' and 'AWS Lambda' to Skills section — 5 minutes, +6 pts",
            "Rename 'Work History' to 'Work Experience' — 1 minute",
            "Add LinkedIn profile URL to contact header — 2 minutes",
            "Convert comma-separated skills to line-by-line list — 10 minutes",
        ],
        "ats_verdict": (
            "Borderline ATS pass — keyword density at 48% when 65%+ is needed for competitive roles. "
            "The multi-column layout is the highest-risk formatting issue. Cloud keywords (Kubernetes, "
            "Terraform, AWS) dominate the JD and are completely absent from the resume."
        ),
    },

    "skills": {
        "match_score": 54,
        "matched_skills": [
            {"skill": "Python", "evidence": "Used across all 3 roles + 4 projects", "proficiency": "Advanced", "jd_importance": "Required"},
            {"skill": "SQL / PostgreSQL", "evidence": "Database work at Fintech Co and personal project", "proficiency": "Intermediate", "jd_importance": "Required"},
            {"skill": "REST API Design", "evidence": "Built Django REST APIs at 2 companies", "proficiency": "Advanced", "jd_importance": "Required"},
            {"skill": "Docker", "evidence": "Side project only — no production evidence", "proficiency": "Beginner", "jd_importance": "Required"},
            {"skill": "Git / GitHub", "evidence": "All projects, public repos linked", "proficiency": "Intermediate", "jd_importance": "Required"},
            {"skill": "Agile / Scrum", "evidence": "Mentioned once at most recent role", "proficiency": "Beginner", "jd_importance": "Preferred"},
        ],
        "missing_critical": [
            {
                "skill": "Kubernetes",
                "importance": "Critical",
                "learn_time_days": 45,
                "why_it_matters": "All services at this company run on EKS — Kubernetes is the core deployment platform for the team",
                "recommended_resource": "KodeKloud 'Kubernetes for Developers' + deploy a personal project to minikube",
            },
            {
                "skill": "AWS (EC2, S3, Lambda, RDS)",
                "importance": "Critical",
                "learn_time_days": 60,
                "why_it_matters": "The entire infra stack is AWS — no AWS knowledge means inability to debug production issues or own deployments",
                "recommended_resource": "AWS Solutions Architect Associate (A Cloud Guru) — aligns cert to JD stack",
            },
            {
                "skill": "Terraform / Infrastructure-as-Code",
                "importance": "High",
                "learn_time_days": 30,
                "why_it_matters": "JD explicitly lists IaC as required — team provisions all infrastructure via Terraform",
                "recommended_resource": "HashiCorp's official Terraform Associate certification path",
            },
            {
                "skill": "CI/CD Pipelines (GitHub Actions / Jenkins)",
                "importance": "High",
                "learn_time_days": 21,
                "why_it_matters": "Team ships 3x/week — owning CI/CD is expected of every engineer, not just DevOps",
                "recommended_resource": "GitHub Actions official docs + build a multi-stage pipeline for existing project",
            },
            {
                "skill": "System Design",
                "importance": "High",
                "learn_time_days": 90,
                "why_it_matters": "Senior role requires architectural ownership — system design interviews are standard at this company",
                "recommended_resource": "'Designing Data-Intensive Applications' (Kleppmann) + system design mock interviews",
            },
        ],
        "missing_nice_to_have": ["Prometheus / Grafana", "Helm", "ArgoCD", "GraphQL", "Redis"],
        "overqualified_areas": [],
        "transferable_skills": [
            "Strong Docker foundation (Beginner) reduces Kubernetes learning curve by ~30%",
            "PostgreSQL expertise transfers well to AWS RDS configuration",
            "Django REST experience maps to AWS API Gateway + Lambda patterns",
        ],
        "top_5_missing": ["Kubernetes", "AWS", "Terraform", "CI/CD", "System Design"],
        "skill_trajectory": (
            "Career is moving toward backend engineering depth but perpendicular to cloud infrastructure. "
            "Recent roles show deepening Python/API expertise but no cloud-native work — the gap is widening, not narrowing."
        ),
        "skills_verdict": (
            "Solid backend Python developer but missing all cloud infrastructure skills that are core to this role. "
            "The Kubernetes + AWS gap is a knockout risk — these are day-1 requirements, not stretch goals."
        ),
    },

    "experience": {
        "experience_score": 58,
        "years_required": 5,
        "years_apparent": 3,
        "seniority_match": "Under",
        "domain_relevance": "Medium",
        "impact_rating": "Weak",
        "quantification_score": 22,
        "action_verb_quality": "Mixed",
        "bullet_quality": [
            {
                "bullet_excerpt": "Worked on backend features for the product",
                "issue": "Passive verb 'worked on' signals zero ownership. No scope, no tech stack, no outcome.",
                "fix": "Replace with: what you built, what stack, what scale, what improved. Use 'Led', 'Built', 'Designed'.",
                "rewritten": "Led development of 4 backend REST API endpoints in Django, reducing checkout latency by [X]ms for [N] daily users",
            },
            {
                "bullet_excerpt": "Helped team migrate to microservices architecture",
                "issue": "'Helped' is the most damaging word on a resume. It signals participation, not ownership.",
                "fix": "Own your contribution specifically. What services did YOU migrate? What decisions did YOU make?",
                "rewritten": "Owned migration of 2 core services (auth + notifications) to microservices, cutting deployment time from [X] to [Y] minutes",
            },
            {
                "bullet_excerpt": "Improved application performance significantly",
                "issue": "'Significantly' is meaningless without a metric. Every candidate says they improved performance.",
                "fix": "Name the specific bottleneck, the technique used, and the before/after number.",
                "rewritten": "Optimised N+1 query in product listing endpoint, reducing p99 latency from 800ms to 120ms (85% improvement)",
            },
        ],
        "best_bullets": [
            "Reduced CI pipeline runtime from 22 min to 6 min by parallelising test suites across 4 workers",
            "Designed and shipped payment integration handling $2M+ monthly transactions with 99.97% uptime",
        ],
        "weakest_bullets": [
            "Worked on backend features for the product",
            "Assisted with various infrastructure improvements",
            "Participated in code reviews and helped maintain quality",
        ],
        "project_evaluations": [
            {
                "title": "Payment Gateway Integration (Fintech Co)",
                "relevance": "High",
                "impact_clarity": "Strong",
                "missing_info": "No mention of transaction volume growth, error rate, or team size",
            },
            {
                "title": "Personal E-Commerce Side Project",
                "relevance": "Medium",
                "impact_clarity": "Weak",
                "missing_info": "No users, no scale, no tech stack depth — reads as tutorial-following, not production engineering",
            },
            {
                "title": "Open Source Contribution (unnamed)",
                "relevance": "Low",
                "impact_clarity": "Weak",
                "missing_info": "Project name, stars, and what specifically was contributed are all missing",
            },
        ],
        "career_progression": "Lateral",
        "internship_quality": "Average",
        "experience_verdict": (
            "2 years below the stated 5-year requirement with a lateral career trajectory. "
            "Impact evidence is sparse — only 2 of 12 bullets have quantified outcomes. "
            "The payment system experience is genuinely strong and the only thing preventing an instant reject."
        ),
    },

    "hiring_manager": {
        "gut_score": 41,
        "would_interview": "Maybe",
        "decision_confidence": "Medium",
        "first_impression": (
            "Python dev, 3 years, no cloud — immediately suspicious for a senior backend role. "
            "Payment experience catches my eye but the title history shows no upward progression."
        ),
        "headline_strength": "Adequate",
        "red_flags": [
            "3 jobs in 4 years — shortest tenure 11 months raises retention concern",
            "22-skill technology list with no depth evidence — spray-and-pray skills padding",
            "Zero cloud or infrastructure exposure in a role that requires both on day 1",
            "No GitHub profile linked despite claiming strong open source contributions",
        ],
        "green_flags": [
            "Payment system at scale ($2M/month) is directly relevant and rare at this experience level",
            "CI pipeline optimisation shows genuine systems-thinking beyond typical backend work",
            "Python depth appears credible — used across multiple roles with specific framework evidence",
        ],
        "knockout_factors": [
            "No Kubernetes experience — this team ships on EKS daily, there is no ramp time budget",
        ],
        "rejection_reasons": [
            {
                "reason": "Missing all cloud infrastructure skills required for day-1 ownership",
                "severity": "Knockout",
                "fixable": True,
                "how_to_fix": "Complete AWS SAA + deploy an EKS project, then reapply in 3 months",
            },
            {
                "reason": "3 years vs 5 years required — seniority gap affects architectural judgment expectation",
                "severity": "Major",
                "fixable": True,
                "how_to_fix": "Apply to mid-level roles to build the missing senior experience evidence",
            },
            {
                "reason": "Career narrative doesn't point toward this role — no cloud evolution visible",
                "severity": "Major",
                "fixable": True,
                "how_to_fix": "Restructure resume to show the backend → infrastructure trajectory you want to build",
            },
            {
                "reason": "Skills list is too long and unsupported — signals resume padding",
                "severity": "Minor",
                "fixable": True,
                "how_to_fix": "Cut to 12 credible skills with evidence. Quality beats quantity every time.",
            },
        ],
        "rejection_email_draft": (
            "Thank you for your interest in the Senior Backend Engineer role. After careful review, "
            "we have decided to move forward with candidates whose experience more closely aligns "
            "with our current infrastructure requirements."
        ),
        "culture_fit_signals": (
            "No mention of cross-functional collaboration, documentation, or mentoring — "
            "signals an individual contributor mindset in a role that requires senior engineering leadership."
        ),
        "narrative_arc": (
            "Career reads as 3 years of execution work with no visible trajectory toward senior ownership. "
            "The story needs a clear 'why this role, why now' — currently it reads as opportunistic rather than intentional."
        ),
        "interview_talking_points": [
            "Walk me through the payment system architecture — what did you own vs what did you inherit?",
            "Tell me about the CI pipeline work — what was the constraint, what was your approach, what would you do differently?",
            "How have you been building cloud skills and what's your current AWS exposure?",
        ],
        "hiring_manager_verdict": (
            "On the edge of the reject pile. The payment experience is the one thing that would make me give it a second look. "
            "But the cloud gap is a knockout — I cannot hire someone for a role where Kubernetes is day-1 work "
            "if they have never touched it."
        ),
    },

    "coordinator": {
        "overall_score": 53,
        "rejection_probability": "High",
        "root_cause_category": "Skills Gap",
        "primary_rejection_reason": (
            "Missing all cloud infrastructure skills (Kubernetes, AWS, Terraform) that the JD lists as required — "
            "not preferred, not nice-to-have. These are day-1 tools and there is no onboarding runway for this gap."
        ),
        "secondary_rejection_reasons": [
            "2-year seniority shortfall compounds the skills gap — senior roles carry architectural expectation",
            "Resume narrative has no cloud evolution story — makes the gap look like disinterest, not timing",
        ],
        "top_3_fixable_gaps": [
            {
                "gap": "Zero Kubernetes and AWS evidence on resume",
                "impact": "This is the single disqualifying factor — the team ships on EKS daily and needs no ramp time",
                "fix": "Deploy a project to AWS EKS (minikube locally is fine for learning), document it with a public GitHub repo and a README, add it to Projects section with architecture decisions explained",
                "effort": "Months",
                "priority": 1,
            },
            {
                "gap": "60% of experience bullets lack quantified impact",
                "impact": "Makes a strong candidate look weak on paper — hiring managers skip unquantified bullets in the first scan",
                "fix": "Rewrite the 5 weakest bullets using: [Action verb] + [what] + [specific metric]. Use 'Led', 'Built', 'Reduced'. Add numbers even if estimated ('~40% reduction', '10K daily users')",
                "effort": "Days",
                "priority": 2,
            },
            {
                "gap": "Resume narrative has no cloud trajectory story",
                "impact": "Hiring manager sees a backend developer applying for an infra-heavy role with zero explanation",
                "fix": "Add a 3-sentence Summary section: current expertise + cloud learning investment + why this role. Example: 'Backend engineer with 3 years of Python/API experience, currently completing AWS SAA and building EKS portfolio. Looking to apply backend depth to cloud-native architecture at scale.'",
                "effort": "Days",
                "priority": 3,
            },
        ],
        "quick_wins": [
            "Add 'Kubernetes', 'AWS', 'Terraform' to Skills section — they appear 6×, 8×, 4× in JD — 10 minutes",
            "Rename 'Work History' to 'Work Experience' to match ATS section taxonomy — 1 minute",
            "Add LinkedIn URL to contact header — 2 minutes",
            "Cut skills list from 22 to 12 — remove anything you cannot confidently discuss for 5 minutes — 15 minutes",
            "Rewrite the 3 worst bullets identified above using the provided rewrites — 1 hour",
        ],
        "30_day_roadmap": [
            {
                "week": 1,
                "theme": "Resume Surgery",
                "actions": [
                    "Rewrite all 12+ experience bullets: Lead/Built/Designed + metric for every single one",
                    "Cut skills section to 12 credible skills grouped: Backend | Cloud (Learning) | Tools | Databases",
                    "Add 3-sentence Summary that explicitly names cloud interest and current AWS learning",
                ],
                "success_metric": "Resume scores 70+ on free ATS checkers (Jobscan, Resume Worded)",
            },
            {
                "week": 2,
                "theme": "Cloud Foundations Sprint",
                "actions": [
                    "Start AWS Cloud Practitioner on A Cloud Guru (free tier) — complete within the week",
                    "Deploy existing Django project to EC2 + RDS + S3 — document architecture in GitHub README",
                    "Add Terraform IaC for the EC2 deployment — 2 resources minimum",
                ],
                "success_metric": "AWS Cloud Practitioner passed + project deployed and linked on resume",
            },
            {
                "week": 3,
                "theme": "Kubernetes Proof-of-Work",
                "actions": [
                    "Complete KodeKloud 'Kubernetes for Absolute Beginners' (6 hours)",
                    "Deploy your Django app to minikube or EKS — create Deployment + Service + Ingress YAML files",
                    "Write a 500-word README explaining your architecture decisions and tradeoffs",
                ],
                "success_metric": "Public GitHub repo with Kubernetes deployment files + architecture README live",
            },
            {
                "week": 4,
                "theme": "Apply and Outreach",
                "actions": [
                    "Update resume with new cloud project and rewritten bullets — target 75+ ATS score",
                    "Apply to 3 mid-level backend roles that list cloud as preferred (not required) as practice",
                    "Reach out to 3 engineers at target companies on LinkedIn — genuine message about their cloud journey",
                ],
                "success_metric": "Updated resume submitted to 3 roles + 3 LinkedIn conversations started",
            },
        ],
        "application_verdict": "Apply After Fixes",
        "estimated_success_after_fixes": 68,
        "final_verdict": (
            "High rejection probability in current state — the cloud skills gap is real, not cosmetic, and cannot be papered over. "
            "The good news: your backend fundamentals are genuinely solid and the payment system experience is valuable. "
            "30 days of focused cloud work plus the resume rewrites would transform this from a likely reject to a competitive application."
        ),
        "encouragement": (
            "That CI pipeline optimisation bullet — reducing runtime from 22 to 6 minutes — is exactly the kind of "
            "systems-thinking evidence senior roles are looking for. Make that story louder, not quieter."
        ),
        "competitor_comparison": (
            "A typical shortlisted candidate for this role has 4-5 years of backend experience, a cloud cert (AWS SAA or CKA), "
            "and at least one project demonstrating Kubernetes deployment. "
            "You have the backend depth — you're 6-8 weeks of cloud proof-of-work away from being competitive."
        ),
    },
}
