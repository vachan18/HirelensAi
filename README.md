# 🔍 HireLens AI — Multi-Agent Job Rejection Analyzer

> **See your application through the recruiter's lens.**

HireLens AI is a full-stack AI application built with **CrewAI multi-agent orchestration**, a **Streamlit dashboard**, and a **premium animated intro**. It simulates the entire hiring pipeline — ATS filtering, skills gap analysis, experience evaluation, and hiring manager decision logic — to tell you exactly why your resume gets rejected.

---

## 📁 Project Structure

```
hirelens_ai/
│
├── app.py                          # Streamlit entry point (2,800+ lines)
├── config.py                       # LLM provider config (Anthropic/OpenAI/Gemini)
├── requirements.txt                # All Python dependencies
├── .env.example                    # Environment variable template
│
├── .streamlit/
│   └── config.toml                 # Dark theme + server settings
│
├── static/                         # Frontend assets
│   ├── intro.html                  # Pure HTML/CSS/JS intro animation (39 KB)
│   └── intro_react.html            # React 18 + Tailwind CSS version (35 KB)
│
├── agents/
│   └── crew_agents.py              # 5 specialist CrewAI agents + crew runner (998 lines)
│
├── analytics/
│   ├── mock_data.py                # Rich demo data (no API key needed)
│   ├── section_scorer.py           # Resume section scoring engine
│   ├── bullet_improver.py          # AI bullet point rewriter
│   ├── recruiter_simulator.py      # Shortlist probability calculator
│   ├── comparison.py               # Multi-agent vs Single AI comparison
│   ├── interview_predictor.py      # Likely interview question predictor
│   └── cover_letter.py             # AI cover letter generator
│
├── models/
│   └── schemas.py                  # Pydantic v2 schemas (all 5 agents)
│
├── utils/
│   ├── pdf_parser.py               # PDF text extraction (pypdf + PyPDF2)
│   ├── logger.py                   # Structured logging
│   └── report_generator.py         # Multi-page PDF report generator
│
├── ui/
│   └── components.py               # Reusable Plotly charts + HTML components
│
└── tests/                          # 100 tests — all passing
    ├── test_analytics.py           # 54 analytics module tests
    ├── test_models.py              # 30 Pydantic schema tests
    ├── test_pdf_parser.py          # 6 PDF parser tests
    └── test_config.py              # 10 config tests
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
cd hirelens_ai
pip install -r requirements.txt
```

### 2. Configure your LLM provider
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Choose ONE provider
HIRELENS_LLM_PROVIDER=anthropic    # or: openai | gemini

# Set the matching key
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# GOOGLE_API_KEY=...
```

### 3. Run the app
```bash
streamlit run app.py
```

Opens at **http://localhost:8501**

> **No API key?** The app auto-detects this and runs in **Demo Mode** with full realistic mock data — every feature works immediately.

### 4. Run tests
```bash
pytest tests/ -v
```
100/100 tests pass.

---

## 🎬 Intro Animation

On first page load, a **full-screen animated intro** plays automatically:

- **Logo** springs in with bounce physics + rotating orbit rings + glowing scan bar
- **Brand name** blur-reveals with gradient shift animation
- **Tagline** slides up
- **Agent pills** stagger-pop in one by one
- **Progress bar** fills to signal startup
- **Scan line sweep** wipes screen at exit
- Transitions to main dashboard after 4.5 seconds

Two versions available in `static/`:
- `intro.html` — Pure HTML/CSS/JS (no dependencies, works everywhere)
- `intro_react.html` — React 18 + Tailwind CSS (open directly in browser)

The Streamlit app injects the animation via a full-viewport overlay on first session visit.

---

## 🤖 The 5-Agent Pipeline

| Agent | Persona | Key Output |
|-------|---------|-----------|
| **ATS Compliance** | Former ATS engineer (Workday/Greenhouse) | Score 0-100, format checks, ranked risks, quick fixes |
| **Skills Gap** | Staff Eng turned Engineering Manager | Match score, JD importance per skill, learn paths |
| **Experience Analysis** | Engineering Director, 500+ screens | Bullet rewrites, project evaluations, quantification rate |
| **Hiring Manager** | VP of Engineering | Knockout factors, rejection reasons by severity, interview points |
| **Coordinator** | Executive career strategist | Root cause, application verdict, 30-day roadmap w/ success metrics |

Each agent prompt contains **6-8 explicit evaluation steps** with scoring rubrics — not generic instructions.

---

## 📊 Dashboard Sections (12 total)

| # | Section | What You See |
|---|---------|-------------|
| ① | ATS Score Card | Gauge + format check table + score breakdown + top risks + quick fixes |
| ② | Agent Analysis Tabs | 5 tabs — one per agent with full specialist output |
| ③ | Skills Gap Chart | Plotly bar chart + JD importance + transferable skills |
| ④ | Final Verdict | Rejection probability + primary root cause |
| ⑤ | Top Improvement Areas | Effort vs Impact bubble chart + quick win checklist |
| ⑥ | 30-Day Career Plan | Week-by-week roadmap with success metrics |
| ⑦ | Resume Section Scoring | Grouped bar + donut + sub-score breakdown for 5 sections |
| ⑧ | Bullet Point Improver | AI rewrites with before/after + score delta per bullet |
| ⑨ | Recruiter Shortlist Meter | 8-signal weighted probability + hiring funnel + benchmarking |
| ⑩ | Multi-Agent vs Single AI | Grouped bar comparison across 8 analytical dimensions |
| ⑪ | Interview Predictor | Predicted questions with category/difficulty/tips/traps |
| ⑫ | Cover Letter Generator | 3 tones, signals-aware, downloadable .txt |

---

## 🔀 Switching LLM Providers

| Provider | Key Variable | Default Model |
|----------|-------------|---------------|
| Anthropic (default) | `ANTHROPIC_API_KEY` | `claude-opus-4-5` |
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| Google Gemini | `GOOGLE_API_KEY` | `gemini/gemini-1.5-pro` |

Override model: `ANTHROPIC_MODEL=claude-sonnet-4-6`

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `crewai` | Multi-agent orchestration |
| `streamlit` | Web dashboard |
| `plotly` | All charts (gauges, radar, bars, funnels) |
| `pydantic` | Agent output validation |
| `pypdf` + `PyPDF2` | PDF text extraction |
| `fpdf2` | PDF report generation |
| `anthropic` | Claude API |
| `openai` | GPT-4 API |
| `google-generativeai` | Gemini API |
| `python-dotenv` | .env loading |
| `pandas` | Data manipulation for charts |

---

## 🧪 Test Coverage

```
tests/test_analytics.py   54 tests  — all analytics modules
tests/test_models.py      30 tests  — Pydantic schemas, enums, validation
tests/test_pdf_parser.py   6 tests  — PDF extraction with mocking
tests/test_config.py      10 tests  — LLM provider switching
                         ─────────
Total:                   100 tests  — 100% passing
```
