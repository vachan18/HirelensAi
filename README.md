# 🔍 HireLens AI — Multi-Agent Job Rejection Analyzer

[![CI Tests](https://github.com/vachan18/HirelensAi/actions/workflows/ci.yml/badge.svg)](https://github.com/vachan18/HirelensAi/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![CrewAI](https://img.shields.io/badge/Orchestration-CrewAI-red.svg)](https://www.crewai.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)

> **See your application through the recruiter's lens.**

HireLens AI is a full-stack AI application built with **CrewAI multi-agent orchestration**, a **Streamlit dashboard**, and a **premium animated intro**.

It simulates the **entire hiring pipeline** — ATS filtering, skills gap analysis, experience evaluation, and hiring manager decision logic — to explain **why your resume gets rejected** and how to improve it.

---

# 📁 Project Structure

```
hirelens_ai/

│
├── app.py                # Streamlit entry point (2,800+ lines)
├── config.py             # LLM provider config (Anthropic/OpenAI/Gemini)
├── requirements.txt      # All Python dependencies
├── .env.example          # Environment variable template
│
├── .streamlit/
│   └── config.toml       # Dark theme + server settings
│
├── static/               # Frontend assets
│   ├── intro.html        # Pure HTML/CSS/JS intro animation
│   └── intro_react.html  # React + Tailwind version
│
├── agents/
│   └── crew_agents.py    # 5 CrewAI agents + orchestration
│
├── analytics/
│   ├── mock_data.py
│   ├── section_scorer.py
│   ├── bullet_improver.py
│   ├── recruiter_simulator.py
│   ├── comparison.py
│   ├── interview_predictor.py
│   └── cover_letter.py
│
├── models/
│   └── schemas.py        # Pydantic schemas
│
├── utils/
│   ├── pdf_parser.py
│   ├── logger.py
│   └── report_generator.py
│
├── ui/
│   └── components.py     # Plotly charts + UI components
│
└── tests/
    ├── test_analytics.py
    ├── test_models.py
    ├── test_pdf_parser.py
    └── test_config.py
```

---

# 🚀 Quick Start

## 1️⃣ Install Dependencies

```bash
cd hirelens_ai
pip install -r requirements.txt
```

---

## 2️⃣ Configure LLM Provider

Create environment file:

```bash
cp .env.example .env
```

Edit `.env`:

```
# Choose one provider
HIRELENS_LLM_PROVIDER=anthropic
# options: anthropic | openai | gemini

# Add API key
ANTHROPIC_API_KEY=your_api_key_here

# Optional
# OPENAI_API_KEY=
# GOOGLE_API_KEY=
```

---

## 3️⃣ Run the Application

```bash
streamlit run app.py
```

App opens at:

```
http://localhost:8501
```

### Demo Mode

If no API key is provided, HireLens automatically runs in **Demo Mode** with **realistic mock data** so every feature still works.

---

## 4️⃣ Run Tests

```bash
pytest tests/ -v
```

```
100 / 100 tests passing
```

---

# 🎬 Intro Animation

On first page load, HireLens shows a **premium animated intro experience**.

Features include:

• Logo spring animation with orbit rings
• Glowing scan bar effect
• Gradient blur-reveal brand text
• Animated agent pill indicators
• Progress bar startup animation
• Full-screen transition wipe

Animation duration: **4.5 seconds**

Two versions available:

| File               | Description                 |
| ------------------ | --------------------------- |
| `intro.html`       | Pure HTML/CSS/JS version    |
| `intro_react.html` | React 18 + Tailwind version |

---

# 🤖 Multi-Agent Hiring Pipeline

HireLens uses **5 specialized AI agents**.

| Agent               | Persona              | Output                       |
| ------------------- | -------------------- | ---------------------------- |
| ATS Compliance      | Former ATS engineer  | Resume format score + risks  |
| Skills Gap          | Engineering Manager  | Skill match + learning paths |
| Experience Analysis | Engineering Director | Bullet improvement + impact  |
| Hiring Manager      | VP Engineering       | Rejection reasons            |
| Coordinator         | Career strategist    | Root cause + 30-day plan     |

Each agent contains **6-8 structured evaluation steps** with scoring rubrics.

---

# 📊 Dashboard Sections

HireLens dashboard contains **12 major analytics sections**.

| #  | Section                   | Description                    |
| -- | ------------------------- | ------------------------------ |
| 1  | ATS Score Card            | Resume ATS compatibility       |
| 2  | Agent Analysis            | Results from each AI agent     |
| 3  | Skills Gap Chart          | Skill match visualization      |
| 4  | Final Verdict             | Rejection probability          |
| 5  | Improvement Areas         | Effort vs impact analysis      |
| 6  | 30-Day Career Plan        | Structured improvement roadmap |
| 7  | Resume Section Scoring    | Score per resume section       |
| 8  | Bullet Improver           | AI rewritten bullet points     |
| 9  | Recruiter Shortlist Meter | Probability of shortlist       |
| 10 | Multi-Agent Comparison    | Single AI vs multi-agent       |
| 11 | Interview Predictor       | Likely interview questions     |
| 12 | Cover Letter Generator    | AI generated cover letters     |

---

# 🔀 Switching LLM Providers

| Provider  | Environment Variable | Default Model  |
| --------- | -------------------- | -------------- |
| Anthropic | `ANTHROPIC_API_KEY`  | claude-opus    |
| OpenAI    | `OPENAI_API_KEY`     | gpt-4o         |
| Gemini    | `GOOGLE_API_KEY`     | gemini-1.5-pro |

Override model example:

```
ANTHROPIC_MODEL=claude-sonnet
```

---

# 📦 Key Dependencies

| Package             | Purpose                   |
| ------------------- | ------------------------- |
| crewai              | Multi-agent orchestration |
| streamlit           | Dashboard UI              |
| plotly              | Interactive charts        |
| pydantic            | Data validation           |
| pypdf / PyPDF2      | PDF parsing               |
| fpdf2               | PDF report generation     |
| anthropic           | Claude API                |
| openai              | GPT API                   |
| google-generativeai | Gemini API                |
| python-dotenv       | Environment loading       |
| pandas              | Data processing           |

---

# 🧪 Test Coverage

```
tests/test_analytics.py   → 54 tests
tests/test_models.py      → 30 tests
tests/test_pdf_parser.py  → 6 tests
tests/test_config.py      → 10 tests
```

**Total Tests:**

```
100 tests — 100% passing
```

---

# 📌 Project Tags

```
#AI
#MultiAgentAI
#CrewAI
#Streamlit
#LLM
#ResumeAnalyzer
#CareerAI
#HirelensAI
```
