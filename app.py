"""
HireLens AI — Multi-Agent Job Rejection Analyzer
Run: streamlit run app.py
"""

import os
import json
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="HireLens AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════
# SAFE IMPORTS
# ══════════════════════════════════════════════════════
_errs = []

try:
    import plotly.graph_objects as go
    import pandas as pd
    CHARTS = True
except Exception as e:
    CHARTS = False; _errs.append(f"plotly: {e}")

try:
    from utils.pdf_parser import extract_text_from_pdf
except Exception:
    def extract_text_from_pdf(f): return ""

try:
    from utils.report_generator import generate_pdf_report
except Exception:
    def generate_pdf_report(*a, **k): return b""  # noqa: E731

try:
    from analytics.mock_data import MOCK_RESULT
    HAS_MOCK = True
except Exception as e:
    HAS_MOCK = False; MOCK_RESULT = {}; _errs.append(f"mock: {e}")

# ══════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
  --bg:      #03050C;
  --bg2:     #070B15;
  --bg3:     #0B1020;
  --bg4:     #0F1628;
  --border:  #131D30;
  --border2: #1A2840;
  --green:   #00FFB2;
  --green2:  #00D48F;
  --green3:  #00A86E;
  --amber:   #FFB830;
  --red:     #FF3D6B;
  --blue:    #3D9BFF;
  --violet:  #9D7FFF;
  --cyan:    #00E5FF;
  --text:    #EEF2FF;
  --dim:     #7A8FAA;
  --muted:   #3A4F6A;
}

html, body, .stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Space Grotesk', sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden !important; }
.block-container { padding: 1.5rem 2.5rem 5rem !important; max-width: 1440px !important; }

.stApp::before {
  content: '';
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 60% 40% at 20% 20%, rgba(0,255,178,.04) 0%, transparent 70%),
    radial-gradient(ellipse 50% 35% at 80% 80%, rgba(61,155,255,.04) 0%, transparent 70%),
    radial-gradient(ellipse 40% 30% at 60% 10%, rgba(157,127,255,.03) 0%, transparent 70%),
    linear-gradient(rgba(0,255,178,.018) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,255,178,.018) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 100% 100%, 48px 48px, 48px 48px;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #060914 0%, #040609 100%) !important;
  border-right: 1px solid var(--border2) !important;
  box-shadow: 6px 0 40px rgba(0,0,0,.6), inset -1px 0 0 rgba(0,255,178,.06) !important;
}
[data-testid="stSidebar"] .block-container { padding: 1.2rem 1.4rem 2rem !important; }
[data-testid="stSidebar"]::after {
  content: '';
  position: absolute; top: 0; right: 0; width: 1px; height: 100%;
  background: linear-gradient(180deg, transparent 0%, var(--green) 30%, var(--blue) 70%, transparent 100%);
  opacity: .2; animation: sidebarGlow 4s ease-in-out infinite alternate;
}
@keyframes sidebarGlow { 0%{opacity:.1} 100%{opacity:.35} }

.stTextArea textarea, .stTextInput input {
  background: var(--bg3) !important;
  border: 1px solid var(--border2) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 13px !important;
  transition: all .25s cubic-bezier(.4,0,.2,1) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.03) !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 3px rgba(0,255,178,.08), 0 0 24px rgba(0,255,178,.06) !important;
  background: var(--bg4) !important;
}

[data-testid="stFileUploader"] {
  background: var(--bg3) !important;
  border: 1.5px dashed var(--border2) !important;
  border-radius: 12px !important;
  transition: all .25s ease !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--green) !important;
  background: rgba(0,255,178,.025) !important;
  box-shadow: 0 0 20px rgba(0,255,178,.06) !important;
  transform: translateY(-1px) !important;
}

.stButton > button {
  background: linear-gradient(135deg, var(--green), var(--green2)) !important;
  color: #020810 !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-weight: 600 !important;
  font-size: 11px !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  padding: .75rem 1.6rem !important;
  box-shadow: 0 0 28px rgba(0,255,178,.35), 0 4px 20px rgba(0,0,0,.5) !important;
  transition: all .25s cubic-bezier(.4,0,.2,1) !important;
  position: relative !important;
  overflow: hidden !important;
  animation: btnPulse 3s ease-in-out infinite !important;
}
@keyframes btnPulse {
  0%,100%{ box-shadow: 0 0 28px rgba(0,255,178,.35), 0 4px 20px rgba(0,0,0,.5); }
  50%    { box-shadow: 0 0 50px rgba(0,255,178,.6),  0 4px 20px rgba(0,0,0,.5); }
}
.stButton > button::before {
  content: '';
  position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.25), transparent);
  transition: left .5s ease;
}
.stButton > button:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 0 55px rgba(0,255,178,.6), 0 12px 32px rgba(0,0,0,.6) !important;
  animation: none !important;
}
.stButton > button:hover::before { left: 100%; }
.stButton > button:active { transform: translateY(-1px) !important; }

.stDownloadButton > button {
  background: transparent !important;
  color: var(--green) !important;
  border: 1px solid rgba(0,255,178,.3) !important;
  border-radius: 10px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  transition: all .2s ease !important;
}
.stDownloadButton > button:hover {
  background: rgba(0,255,178,.07) !important;
  border-color: var(--green) !important;
  box-shadow: 0 0 20px rgba(0,255,178,.15) !important;
  transform: translateY(-2px) !important;
}

.stTabs [data-baseweb="tab-list"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 14px !important;
  padding: 5px !important;
  gap: 3px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.03), 0 4px 20px rgba(0,0,0,.3) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  border-radius: 10px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  letter-spacing: 1.2px !important;
  text-transform: uppercase !important;
  padding: 9px 18px !important;
  border: none !important;
  transition: all .2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--dim) !important;
  background: rgba(255,255,255,.04) !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--green), var(--green2)) !important;
  color: #020810 !important;
  font-weight: 600 !important;
  box-shadow: 0 0 20px rgba(0,255,178,.3), 0 2px 8px rgba(0,0,0,.4) !important;
}

.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--green), var(--cyan), var(--blue)) !important;
  background-size: 200% 100% !important;
  border-radius: 4px !important;
  box-shadow: 0 0 10px rgba(0,255,178,.4) !important;
  animation: progressShimmer 1.5s linear infinite !important;
}
@keyframes progressShimmer { 0%{background-position:100% 0} 100%{background-position:-100% 0} }

[data-testid="stExpander"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  transition: border-color .2s !important;
}
[data-testid="stExpander"] summary {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important; color: var(--muted) !important; letter-spacing: .5px !important;
}
[data-testid="stCheckbox"] label { color: var(--dim) !important; font-size: 13px !important; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
hr { border-color: var(--border2) !important; margin: 28px 0 !important; opacity: .4 !important; }

/* ── CARDS ── */
.card {
  background: linear-gradient(145deg, var(--bg2), var(--bg3));
  border: 1px solid var(--border2); border-radius: 14px;
  padding: 20px 22px; margin-bottom: 12px;
  position: relative; overflow: hidden;
  transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease;
}
.card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,255,178,.25), transparent);
}
.card:hover {
  border-color: rgba(0,255,178,.2);
  box-shadow: 0 8px 40px rgba(0,0,0,.4), 0 0 0 1px rgba(0,255,178,.05);
  transform: translateY(-2px);
}
.card-g { border-top: 2px solid var(--green)  !important; }
.card-r { border-top: 2px solid var(--red)    !important; }
.card-a { border-top: 2px solid var(--amber)  !important; }
.card-b { border-top: 2px solid var(--blue)   !important; }
.card-v { border-top: 2px solid var(--violet) !important; }

.sec {
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  text-transform: uppercase; letter-spacing: 2.5px; color: var(--muted);
  border-bottom: 1px solid var(--border); padding-bottom: 8px; margin: 28px 0 18px;
  display: flex; align-items: center; gap: 8px;
}
.sec::before {
  content: ''; display: block; width: 3px; height: 14px;
  background: linear-gradient(180deg, var(--green), var(--blue));
  border-radius: 2px; flex-shrink: 0;
  box-shadow: 0 0 8px rgba(0,255,178,.4);
}
.lbl { font-family:'JetBrains Mono',monospace; font-size:10px; text-transform:uppercase; letter-spacing:1.5px; color:var(--muted); margin-bottom:5px; }

.chip {
  display: inline-flex; align-items: center;
  padding: 4px 12px; border-radius: 20px;
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  margin: 2px; letter-spacing: .5px; border: 1px solid;
  transition: all .2s ease; cursor: default;
}
.chip:hover { transform: translateY(-1px); filter: brightness(1.2); }
.chip-g { background:rgba(0,255,178,.07);   color:var(--green);  border-color:rgba(0,255,178,.3);   }
.chip-r { background:rgba(255,61,107,.07);  color:var(--red);    border-color:rgba(255,61,107,.3);  }
.chip-a { background:rgba(255,184,48,.07);  color:var(--amber);  border-color:rgba(255,184,48,.3);  }
.chip-b { background:rgba(61,155,255,.07);  color:var(--blue);   border-color:rgba(61,155,255,.3);  }
.chip-v { background:rgba(157,127,255,.07); color:var(--violet); border-color:rgba(157,127,255,.3); }
.chip-c { background:rgba(0,229,255,.07);   color:var(--cyan);   border-color:rgba(0,229,255,.3);   }

.al {
  border-radius: 10px; padding: 12px 16px; margin-bottom: 10px;
  border-left: 3px solid; font-size: 13px; line-height: 1.65;
  position: relative; overflow: hidden; transition: transform .2s ease;
}
.al:hover { transform: translateX(3px); }
.al-g { background:rgba(0,255,178,.06);  border-color:var(--green); color:#7FFFD4; }
.al-a { background:rgba(255,184,48,.06); border-color:var(--amber); color:#FFD68A; }
.al-r { background:rgba(255,61,107,.06); border-color:var(--red);   color:#FFB3C1; }
.al-b { background:rgba(61,155,255,.06); border-color:var(--blue);  color:#A8D4FF; }

.glow-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--green);
  box-shadow: 0 0 0 0 rgba(0,255,178,.6);
  animation: sonar 2s ease-out infinite; display: inline-block;
}
@keyframes sonar {
  0%  { box-shadow: 0 0 0 0 rgba(0,255,178,.6); }
  70% { box-shadow: 0 0 0 10px rgba(0,255,178,0); }
  100%{ box-shadow: 0 0 0 0 rgba(0,255,178,0); }
}

.stat-card {
  background: linear-gradient(145deg, var(--bg2), var(--bg3));
  border: 1px solid var(--border2); border-radius: 12px;
  padding: 14px 16px; text-align: center;
  transition: all .25s cubic-bezier(.4,0,.2,1); position: relative; overflow: hidden;
}
.stat-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.08), transparent);
}
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 12px 36px rgba(0,0,0,.4); }

.tag {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(0,255,178,.06); border: 1px solid rgba(0,255,178,.15);
  border-radius: 20px; padding: 5px 14px;
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  letter-spacing: 1px; text-transform: uppercase; color: var(--green);
  transition: all .2s ease;
}
.tag:hover { background:rgba(0,255,178,.12); border-color:rgba(0,255,178,.4); box-shadow:0 0 12px rgba(0,255,178,.15); transform:translateY(-1px); }

.sev-knockout { background:rgba(255,61,107,.12); color:#FF3D6B; border:1px solid rgba(255,61,107,.4); border-radius:6px; padding:2px 8px; font-size:10px; font-family:JetBrains Mono,monospace; animation:sevPulse 2s ease-in-out infinite; }
.sev-major    { background:rgba(255,184,48,.12); color:#FFB830; border:1px solid rgba(255,184,48,.4); border-radius:6px; padding:2px 8px; font-size:10px; font-family:JetBrains Mono,monospace; }
.sev-minor    { background:rgba(58,79,106,.15);  color:#7A8FAA; border:1px solid rgba(58,79,106,.3);  border-radius:6px; padding:2px 8px; font-size:10px; font-family:JetBrains Mono,monospace; }
@keyframes sevPulse { 0%,100%{opacity:1} 50%{opacity:.7} }

.week-action {
  font-size: 12px; color: var(--dim); padding: 7px 0;
  border-bottom: 1px solid var(--border); line-height: 1.5;
  display: flex; gap: 8px; align-items: flex-start; transition: color .2s;
}
.week-action::before { content:'›'; color:var(--green); flex-shrink:0; font-weight:700; font-size:14px; }
.week-action:hover { color: var(--text); }
.week-action:last-child { border-bottom: none; }

.kw { display:inline-block; padding:4px 11px; margin:2px; border-radius:6px; font-family:'JetBrains Mono',monospace; font-size:11px; border:1px solid; letter-spacing:.3px; transition:all .15s ease; cursor:default; }
.kw:hover { transform:translateY(-2px); box-shadow:0 4px 12px rgba(0,0,0,.3); }
.kw-g { background:rgba(0,255,178,.06);  color:var(--green); border-color:rgba(0,255,178,.2);  }
.kw-r { background:rgba(255,61,107,.06); color:var(--red);   border-color:rgba(255,61,107,.2); }

.sbar { background:var(--border); border-radius:4px; overflow:hidden; }
.sbar-fill { height:100%; border-radius:4px; transition:width 1s cubic-bezier(.4,0,.2,1); }

/* ── SCORE NUM ── */
.score-num { font-family:'Space Grotesk',sans-serif; font-size:42px; font-weight:800; line-height:1; letter-spacing:-1px; }

/* ═══ INTRO ═══ */
#hl-intro-wrap {
  position: fixed; inset: 0;
  background: radial-gradient(ellipse 80% 60% at 50% 30%, #061422 0%, #03050C 65%);
  display: flex;
  flex-direction: column; align-items: center; justify-content: center;
  z-index: 99999; gap: 22px; font-family: 'Space Grotesk', sans-serif; overflow: hidden;
}
#hl-intro-wrap::before {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(0,255,178,.022) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,255,178,.022) 1px, transparent 1px);
  background-size: 48px 48px;
}
#hl-intro-wrap::after {
  content: ''; position: absolute; width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(0,255,178,.06) 0%, transparent 70%);
  border-radius: 50%; top: 50%; left: 50%; transform: translate(-50%,-50%);
  animation: orb 6s ease-in-out infinite alternate;
}
@keyframes orb { 0%{transform:translate(-50%,-50%) scale(1)} 100%{transform:translate(-50%,-50%) scale(1.3)} }

#hl-logo {
  width: 96px; height: 96px;
  background: linear-gradient(145deg, #0D1F30, #060E18);
  border-radius: 28px; border: 1px solid rgba(0,255,178,.3);
  display: flex; align-items: center; justify-content: center; position: relative; z-index: 1;
  box-shadow: 0 0 60px rgba(0,255,178,.18), 0 0 120px rgba(0,255,178,.06), inset 0 1px 0 rgba(255,255,255,.08);
  animation: logoIn .9s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes logoIn { from{opacity:0;transform:scale(.3) rotate(-25deg)} to{opacity:1;transform:scale(1) rotate(0)} }

#hl-name {
  font-family: 'Syne', sans-serif; font-size: clamp(48px,8.5vw,84px);
  font-weight: 800; letter-spacing: -3px; line-height: 1;
  background: linear-gradient(135deg, #FFFFFF 0%, #00FFB2 45%, #3D9BFF 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: nameIn .9s ease-out .7s both; position: relative; z-index: 1;
}
@keyframes nameIn { from{opacity:0;filter:blur(16px);letter-spacing:-8px} to{opacity:1;filter:blur(0);letter-spacing:-3px} }

#hl-tag { font-size:clamp(11px,1.4vw,13px); letter-spacing:4px; text-transform:uppercase; color:var(--muted); animation:slideUp .6s ease-out 1.5s both; z-index:1; }
#hl-pills { display:flex; gap:8px; flex-wrap:wrap; justify-content:center; max-width:540px; animation:slideUp .6s ease-out 1.9s both; z-index:1; }
.hl-pill { font-size:10px; font-family:'JetBrains Mono',monospace; letter-spacing:1.5px; text-transform:uppercase; padding:6px 16px; border-radius:20px; border:1px solid; }
#hl-bar-wrap { animation:slideUp .5s ease-out 2.4s both; display:flex; flex-direction:column; align-items:center; gap:8px; z-index:1; }
#hl-track { width:220px; height:2px; background:rgba(255,255,255,.06); border-radius:2px; overflow:hidden; }
#hl-fill  { height:100%; width:0; background:linear-gradient(90deg,#00FFB2,#3D9BFF); animation:fillUp 1.2s ease-out 2.5s both; box-shadow:0 0 10px rgba(0,255,178,.5); }
@keyframes fillUp { to{width:100%} }
#hl-lbl { font-size:9px; font-family:'JetBrains Mono',monospace; letter-spacing:2.5px; text-transform:uppercase; color:var(--muted); }
@keyframes slideUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }

.scan-line { position:absolute; left:0; right:0; height:2px; background:linear-gradient(90deg,transparent,rgba(0,255,178,.4),transparent); animation:scan 4s linear 1s infinite; pointer-events:none; z-index:0; }
@keyframes scan { 0%{top:-10%} 100%{top:110%} }

@keyframes floatUp {
  0%  { transform:translateY(0) translateX(0); opacity:0; }
  10% { opacity:var(--op); }
  90% { opacity:var(--op); }
  100%{ transform:translateY(-100vh) translateX(var(--dx)); opacity:0; }
}
.hl-particle { position:fixed; border-radius:50%; pointer-events:none; z-index:0; animation:floatUp var(--dur) linear var(--del) infinite; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# INTRO — JS localStorage gates it to truly first visit only
# ══════════════════════════════════════════════════════
def maybe_show_intro():
    """
    Inject intro animation HTML.
    JS checks localStorage — if already seen this session, div is
    immediately hidden so it never blocks the dashboard on st.rerun().
    """
    # Never show intro when dashboard results are already loaded
    if st.session_state.get("done"):
        return

    st.markdown("""
    <div id="hl-intro-wrap">
      <div class="scan-line"></div>
      <div id="hl-logo">
        <svg width="46" height="46" viewBox="0 0 46 46" fill="none">
          <circle cx="23" cy="23" r="11" fill="rgba(0,255,178,.1)" stroke="#00FFB2" stroke-width="1.5"/>
          <line x1="23" y1="15" x2="23" y2="18.5" stroke="#00FFB2" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="23" y1="27.5" x2="23" y2="31" stroke="#00FFB2" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="15" y1="23" x2="18.5" y2="23" stroke="#00FFB2" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="27.5" y1="23" x2="31" y2="23" stroke="#00FFB2" stroke-width="1.5" stroke-linecap="round"/>
          <circle cx="23" cy="23" r="2.5" fill="#00FFB2"/>
          <line x1="31.5" y1="31.5" x2="37" y2="37" stroke="#00FFB2" stroke-width="2" stroke-linecap="round"/>
          <circle cx="23" cy="23" r="19" stroke="#00FFB2" stroke-width=".75" stroke-dasharray="4 3" opacity=".4"/>
          <circle cx="23" cy="23" r="16" stroke="#3D9BFF" stroke-width=".5" stroke-dasharray="2 4" opacity=".3"/>
        </svg>
      </div>
      <div id="hl-name">HireLens AI</div>
      <div id="hl-tag">See your application through the recruiter's lens</div>
      <div id="hl-pills">
        <span class="hl-pill" style="color:#00FFB2;border-color:rgba(0,255,178,.4);background:rgba(0,255,178,.06)">ATS Agent</span>
        <span class="hl-pill" style="color:#3D9BFF;border-color:rgba(61,155,255,.4);background:rgba(61,155,255,.06)">Skills Gap</span>
        <span class="hl-pill" style="color:#FFB830;border-color:rgba(255,184,48,.4);background:rgba(255,184,48,.06)">Experience</span>
        <span class="hl-pill" style="color:#9D7FFF;border-color:rgba(157,127,255,.4);background:rgba(157,127,255,.06)">HM Sim</span>
        <span class="hl-pill" style="color:#FF3D6B;border-color:rgba(255,61,107,.4);background:rgba(255,61,107,.06)">Coordinator</span>
      </div>
      <div id="hl-bar-wrap">
        <div id="hl-track"><div id="hl-fill"></div></div>
        <div id="hl-lbl">Initialising 5 specialist agents</div>
      </div>
    </div>

    <script>
    (function() {
        var wrap = document.getElementById('hl-intro-wrap');
        if (!wrap) return;

        // If already seen this session — hide instantly, no animation
        if (sessionStorage.getItem('hl_seen') === '1') {
            wrap.style.display = 'none';
            return;
        }

        // First visit — mark seen, show animation, then fade out
        sessionStorage.setItem('hl_seen', '1');
        wrap.style.display = 'flex';

        setTimeout(function() {
            wrap.style.transition = 'opacity 0.5s ease-out';
            wrap.style.opacity = '0';
            wrap.style.pointerEvents = 'none';
            setTimeout(function() {
                if (wrap.parentNode) wrap.parentNode.removeChild(wrap);
            }, 500);
        }, 4200);
    })();
    </script>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# CHART HELPERS
# ══════════════════════════════════════════════════════
def _sc(s): return "#10B981" if s>=70 else "#F59E0B" if s>=45 else "#EF4444"

def _gauge(score, title, size=210):
    if not CHARTS: return None
    c = _sc(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        title={"text":title,"font":{"size":11,"color":"#64748B","family":"DM Mono"}},
        number={"font":{"size":28,"color":c,"family":"DM Mono"},"suffix":"/100"},
        gauge={
            "axis":{"range":[0,100],"tickwidth":1,"tickcolor":"#1E293B"},
            "bar":{"color":c,"thickness":.28}, "bgcolor":"#0E1420","borderwidth":0,
            "steps":[{"range":[0,45],"color":"#0F172A"},{"range":[45,70],"color":"#0F1F2A"},{"range":[70,100],"color":"#0F2A1F"}],
            "threshold":{"line":{"color":c,"width":3},"thickness":.78,"value":score},
        },
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                      height=size,margin=dict(l=16,r=16,t=28,b=8))
    return fig

def _bar(missing):
    if not CHARTS or not missing: return None
    df = pd.DataFrame(missing).sort_values("learn_time_days",ascending=True)
    colors = [{"Critical":"#EF4444","High":"#F59E0B","Medium":"#3B82F6"}.get(i,"#3B82F6") for i in df.get("importance",[])]
    fig = go.Figure(go.Bar(
        x=df.get("learn_time_days",[]),y=df.get("skill",[]),orientation="h",
        marker=dict(color=colors,line=dict(width=0)),
        text=[f"{d}d" for d in df.get("learn_time_days",[])],
        textposition="outside",textfont=dict(color="#64748B",size=10,family="DM Mono"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        height=max(180,len(df)*44),
        xaxis=dict(title="Days to Learn",color="#1E293B",gridcolor="#1E293B",titlefont=dict(color="#64748B",size=10)),
        yaxis=dict(color="#94A3B8",tickfont=dict(size=10,family="DM Mono")),
        margin=dict(l=8,r=56,t=8,b=36),font={"color":"#64748B","family":"DM Mono"},
    )
    return fig

def _radar(matched):
    if not CHARTS or not matched or len(matched)<3: return None
    pm={"Beginner":25,"Intermediate":50,"Advanced":75,"Expert":100}
    items=matched[:8]; labels=[s.get("skill","")[:16] for s in items]
    vals=[pm.get(s.get("proficiency","Intermediate"),50) for s in items]
    labels.append(labels[0]); vals.append(vals[0])
    fig=go.Figure(go.Scatterpolar(r=vals,theta=labels,fill="toself",
        fillcolor="rgba(16,185,129,.1)",line=dict(color="#10B981",width=2),marker=dict(color="#10B981",size=5)))
    fig.update_layout(polar=dict(
        radialaxis=dict(visible=True,range=[0,100],color="#1E293B",gridcolor="#1E293B",tickfont={"size":8}),
        angularaxis=dict(color="#64748B",gridcolor="#1E293B",tickfont={"size":9}),bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",showlegend=False,
        height=290,margin=dict(l=36,r=36,t=16,b=16),font={"color":"#64748B","family":"DM Mono","size":9})
    return fig

def _chips(items,cls="g"):
    if not items: return '<span style="color:#64748B;font-size:12px;">None</span>'
    return "".join(f'<span class="chip chip-{cls}">{i}</span>' for i in items)

def _pc(fig):
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})


# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:10px 0 22px;border-bottom:1px solid var(--border2);margin-bottom:20px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <div style="width:34px;height:34px;background:linear-gradient(145deg,#0D1F30,#060E18);
                        border-radius:10px;border:1px solid rgba(0,217,163,.3);
                        display:flex;align-items:center;justify-content:center;flex-shrink:0;
                        box-shadow:0 0 16px rgba(0,217,163,.1);">
              <svg width="18" height="18" viewBox="0 0 46 46" fill="none">
                <circle cx="23" cy="23" r="11" fill="rgba(0,217,163,.1)" stroke="#00D9A3" stroke-width="1.5"/>
                <line x1="23" y1="16" x2="23" y2="19.5" stroke="#00D9A3" stroke-width="1.5" stroke-linecap="round"/>
                <line x1="23" y1="26.5" x2="23" y2="30" stroke="#00D9A3" stroke-width="1.5" stroke-linecap="round"/>
                <line x1="16" y1="23" x2="19.5" y2="23" stroke="#00D9A3" stroke-width="1.5" stroke-linecap="round"/>
                <line x1="26.5" y1="23" x2="30" y2="23" stroke="#00D9A3" stroke-width="1.5" stroke-linecap="round"/>
                <circle cx="23" cy="23" r="2.5" fill="#00D9A3"/>
                <line x1="31" y1="31" x2="37" y2="37" stroke="#00D9A3" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div>
              <div style="font-family:'Outfit',sans-serif;font-size:18px;font-weight:800;
                          background:linear-gradient(135deg,#00D9A3,#4D9EFF);
                          -webkit-background-clip:text;background-clip:text;color:transparent;
                          letter-spacing:-.5px;line-height:1.1;">HireLens AI</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--muted);
                          letter-spacing:1.5px;text-transform:uppercase;margin-top:1px;">
                Multi-Agent Analyzer</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="lbl" style="margin-bottom:7px;">📄 Resume PDF</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("resume", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            st.markdown(f'<div class="al al-g" style="margin-bottom:10px;font-size:12px;">✓ {uploaded.name} · {uploaded.size//1024} KB</div>', unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown('<div class="lbl" style="margin-bottom:7px;">🏢 Company Name</div>', unsafe_allow_html=True)
        company = st.text_input("company", placeholder="Google, Infosys, TCS...", label_visibility="collapsed")

        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown('<div class="lbl" style="margin-bottom:7px;">📋 Job Description</div>', unsafe_allow_html=True)
        jd = st.text_area("jd", height=190, placeholder="Paste the full job description here...", label_visibility="collapsed")

        st.markdown('<br>', unsafe_allow_html=True)
        brutal = st.checkbox("💀 Brutal Honesty Mode", value=False)

        st.markdown('<br>', unsafe_allow_html=True)
        analyze = st.button("🔍  Analyze Application", use_container_width=True)

        if st.session_state.get("done"):
            if st.button("🔄  New Analysis", use_container_width=True):
                for k in ["done","results","company","resume_text","_intro_done"]:
                    st.session_state.pop(k, None)
                st.rerun()

        api_key = (os.environ.get("ANTHROPIC_API_KEY") or
                   os.environ.get("OPENAI_API_KEY") or
                   os.environ.get("GOOGLE_API_KEY"))
        if not api_key:
            st.markdown("""
            <div style="background:rgba(245,166,35,.06);border:1px solid rgba(245,166,35,.25);
                        border-radius:10px;padding:11px 13px;margin-top:14px;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--amber);
                          text-transform:uppercase;letter-spacing:1.2px;margin-bottom:3px;">⚡ Demo Mode</div>
              <div style="font-size:11px;color:var(--muted);line-height:1.5;">
                No API key detected.<br>Showing mock analysis results.</div>
            </div>
            """, unsafe_allow_html=True)

    return uploaded, company, jd, brutal, analyze


# ══════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════
def render_header(company=""):
    co = f'<span style="color:var(--green);font-size:18px;font-weight:300;opacity:.7;margin-left:8px;">/ {company}</span>' if company else ""
    st.markdown(f"""
    <div style="display:flex;align-items:flex-end;justify-content:space-between;
                padding:6px 0 26px;border-bottom:1px solid var(--border2);
                margin-bottom:28px;flex-wrap:wrap;gap:14px;">
      <div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:7px;">
          <div class="glow-dot"></div>
          <span style="font-family:'JetBrains Mono',monospace;font-size:10px;
                       color:var(--green);letter-spacing:2px;text-transform:uppercase;">
            System Online · 5 Agents Ready</span>
        </div>
        <h1 style="font-family:'Outfit',sans-serif;font-size:clamp(30px,3.5vw,48px);
                   font-weight:800;letter-spacing:-1.5px;
                   background:linear-gradient(135deg,#F0F4FF 0%,#00D9A3 50%,#4D9EFF 100%);
                   -webkit-background-clip:text;background-clip:text;color:transparent;
                   margin:0;line-height:1.1;">HireLens AI{co}</h1>
        <p style="font-family:'Outfit',sans-serif;font-size:14px;color:var(--muted);
                  margin:7px 0 0;letter-spacing:.2px;">
          See your application through the recruiter's lens</p>
      </div>
      <div style="display:flex;gap:10px;align-items:center;">
        <div style="background:linear-gradient(145deg,var(--bg2),var(--bg3));
                    border:1px solid var(--border2);border-radius:12px;
                    padding:10px 18px;text-align:center;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:8px;
                      color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;">Agents</div>
          <div style="font-family:'Outfit',sans-serif;font-size:26px;font-weight:700;
                      color:var(--green);line-height:1.2;margin-top:2px;">5</div>
        </div>
        <div style="background:linear-gradient(145deg,var(--bg2),var(--bg3));
                    border:1px solid var(--border2);border-radius:12px;
                    padding:10px 18px;text-align:center;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:8px;
                      color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;">Signals</div>
          <div style="font-family:'Outfit',sans-serif;font-size:26px;font-weight:700;
                      color:var(--blue);line-height:1.2;margin-top:2px;">40+</div>
        </div>
        <div style="background:linear-gradient(145deg,var(--bg2),var(--bg3));
                    border:1px solid var(--border2);border-radius:12px;
                    padding:10px 18px;text-align:center;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:8px;
                      color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;">Fields</div>
          <div style="font-family:'Outfit',sans-serif;font-size:26px;font-weight:700;
                      color:var(--violet);line-height:1.2;margin-top:2px;">27+</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# SCORE STRIP
# ══════════════════════════════════════════════════════
def render_scores(r):
    # inject floating particles once per session
    if not st.session_state.get("_particles_injected"):
        st.session_state["_particles_injected"] = True
        st.markdown("""
        <style>
        @keyframes floatUp {
          0%   { transform:translateY(0) translateX(0); opacity:0; }
          10%  { opacity:var(--op); }
          90%  { opacity:var(--op); }
          100% { transform:translateY(-100vh) translateX(var(--dx)); opacity:0; }
        }
        .hl-particle {
          position:fixed; border-radius:50%;
          pointer-events:none; z-index:0;
          animation:floatUp var(--dur) linear var(--del) infinite;
        }
        </style>
        <script>
        (function(){
          if(document.getElementById('hl-particles-done')) return;
          var marker = document.createElement('div');
          marker.id = 'hl-particles-done';
          document.body.appendChild(marker);
          var colors=['rgba(0,217,163,.5)','rgba(77,158,255,.4)','rgba(245,166,35,.35)','rgba(167,139,250,.35)','rgba(34,211,238,.4)'];
          for(var i=0;i<22;i++){
            var p=document.createElement('div');
            p.className='hl-particle';
            var sz=Math.random()*2.5+1;
            var col=colors[Math.floor(Math.random()*colors.length)];
            var op=(Math.random()*.35+.08).toFixed(2);
            var dur=(Math.random()*22+14).toFixed(1)+'s';
            var del=-(Math.random()*20).toFixed(1)+'s';
            var dx=((Math.random()-.5)*140).toFixed(0)+'px';
            var left=(Math.random()*100).toFixed(1)+'%';
            p.style.cssText='width:'+sz+'px;height:'+sz+'px;background:'+col+';left:'+left+';bottom:-8px;--op:'+op+';--dur:'+dur+';--del:'+del+';--dx:'+dx+';box-shadow:0 0 '+(sz*3)+'px '+col;
            document.body.appendChild(p);
          }
        })();
        </script>
        """, unsafe_allow_html=True)

    data = [
        ("Overall",    r.get("coordinator",{}).get("overall_score",0),    "Coordinator",  "#00D9A3", 200),
        ("ATS",        r.get("ats",{}).get("ats_score",0),                "Compliance",   "#4D9EFF", 201),
        ("Skills",     r.get("skills",{}).get("match_score",0),           "Gap Match",    "#A78BFA", 201),
        ("Experience", r.get("experience",{}).get("experience_score",0),  "Relevance",    "#F5A623", 201),
        ("HM Gut",     r.get("hiring_manager",{}).get("gut_score",0),     "Hiring Mgr",   "#22D3EE", 201),
    ]
    cols = st.columns(5, gap="small")
    for col, (label, score, sub, accent, circ) in zip(cols, data):
        c      = _sc(score)
        grade  = "A" if score>=85 else "B" if score>=70 else "C" if score>=55 else "D" if score>=40 else "F"
        # SVG ring: circumference=201, offset = circ*(1 - score/100)
        r_val  = 32
        circum = round(2 * 3.14159 * r_val)
        offset = round(circum * (1 - score / 100))
        with col:
            st.markdown(f"""
            <div style="background:linear-gradient(145deg,var(--bg2),var(--bg3));
                        border:1px solid rgba(255,255,255,.06);
                        border-radius:16px;padding:18px 10px;text-align:center;
                        position:relative;overflow:hidden;margin-bottom:12px;
                        transition:transform .2s,box-shadow .2s;cursor:default;"
                 onmouseenter="this.style.transform='translateY(-3px)';this.style.boxShadow='0 12px 32px rgba(0,0,0,.5),0 0 24px {accent}18'"
                 onmouseleave="this.style.transform='';this.style.boxShadow=''">
              <div style="position:absolute;inset:0;
                          background:radial-gradient(ellipse 80% 50% at 50% 0%, {accent}0D, transparent 70%);
                          pointer-events:none;"></div>
              <div style="position:absolute;top:0;left:0;right:0;height:2px;
                          background:linear-gradient(90deg,transparent,{accent},{accent},transparent);
                          box-shadow:0 0 8px {accent};"></div>

              <div style="font-family:'JetBrains Mono',monospace;font-size:8px;
                          text-transform:uppercase;letter-spacing:2px;
                          color:var(--muted);margin-bottom:10px;">{label}</div>

              <div style="position:relative;width:72px;height:72px;margin:0 auto 8px;">
                <svg viewBox="0 0 80 80" width="72" height="72"
                     style="transform:rotate(-90deg)">
                  <circle cx="40" cy="40" r="{r_val}" fill="none"
                          stroke="rgba(255,255,255,.06)" stroke-width="7"/>
                  <circle cx="40" cy="40" r="{r_val}" fill="none"
                          stroke="{accent}" stroke-width="7"
                          stroke-dasharray="{circum}" stroke-dashoffset="{offset}"
                          stroke-linecap="round"
                          style="filter:drop-shadow(0 0 5px {accent});transition:stroke-dashoffset .8s ease"/>
                </svg>
                <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
                  <div style="font-family:'Outfit',sans-serif;font-size:22px;font-weight:800;
                              color:{accent};line-height:1;
                              text-shadow:0 0 16px {accent}80;">{score}</div>
                </div>
              </div>

              <div style="font-family:'JetBrains Mono',monospace;font-size:9px;
                          color:{c};text-transform:uppercase;letter-spacing:1px;
                          margin-bottom:6px;">{sub}</div>

              <div style="background:rgba(255,255,255,.04);border-radius:4px;height:3px;
                          margin:0 4px;overflow:hidden;">
                <div style="width:{score}%;height:100%;
                            background:linear-gradient(90deg,{c},{accent});
                            border-radius:4px;
                            box-shadow:0 0 6px {c}80;
                            transition:width .8s ease;"></div>
              </div>

              <div style="font-family:'Outfit',sans-serif;font-size:14px;font-weight:700;
                          color:{accent};opacity:.5;margin-top:5px;">{grade}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# AGENT TABS
# ══════════════════════════════════════════════════════
def render_agent_tabs(results):
    ats  = results.get("ats",{})
    sk   = results.get("skills",{})
    exp  = results.get("experience",{})
    hm   = results.get("hiring_manager",{})
    coord= results.get("coordinator",{})

    t1,t2,t3,t4,t5 = st.tabs(["🤖 ATS Agent","🔬 Skills Gap","📊 Experience","🧠 Hiring Manager","🎯 Coordinator"])

    # ── ATS ──
    with t1:
        score = ats.get("ats_score",0)
        pf    = ats.get("pass_fail","FAIL")
        pf_c  = {"PASS":"#10B981","BORDERLINE":"#F59E0B","FAIL":"#EF4444"}.get(pf,"#EF4444")
        density = ats.get("keyword_density_pct",0)

        c1,c2,c3 = st.columns([1,1.2,1],gap="medium")
        with c1:
            if CHARTS:
                fig=_gauge(score,"ATS SCORE");
                if fig: _pc(fig)
            else:
                st.markdown(f'<div class="card" style="text-align:center;padding:28px 16px;"><div class="lbl">ATS Score</div><div style="font-family:DM Mono,monospace;font-size:52px;font-weight:700;color:{_sc(score)};">{score}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;margin-top:-4px;"><span style="background:{pf_c}18;border:1px solid {pf_c};border-radius:20px;padding:5px 14px;font-family:DM Mono,monospace;font-size:12px;color:{pf_c};">{pf}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;margin-top:6px;font-family:DM Mono,monospace;font-size:10px;color:#64748B;">Keyword Density: <span style="color:{_sc(density)};">{density}%</span></div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="sec" style="margin-top:0;">Section Audit</div>', unsafe_allow_html=True)
            audit=ats.get("section_audit",{})
            for name,key in [("Summary","has_summary"),("Skills","has_skills"),("Experience","has_experience"),("Education","has_education"),("Contact","has_contact")]:
                p=audit.get(key,False); ic,bg=("#10B981","#064E3B") if p else ("#EF4444","#450A0A")
                st.markdown(f'<div style="background:{bg};border-radius:7px;padding:7px 12px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;"><span style="font-size:13px;color:#CBD5E1;">{name}</span><span style="font-family:DM Mono,monospace;font-size:14px;color:{ic};font-weight:700;">{"✓" if p else "✗"}</span></div>', unsafe_allow_html=True)

        with c3:
            bd=ats.get("score_breakdown",{})
            if bd:
                st.markdown('<div class="sec" style="margin-top:0;">Score Breakdown</div>', unsafe_allow_html=True)
                lmap={"keyword_match":"Keywords","section_structure":"Sections","format_parsability":"Format","contact_completeness":"Contact"}
                for k,v in bd.items():
                    lbl=lmap.get(k,k.replace("_"," ").title()); c=_sc(v)
                    st.markdown(f'<div style="margin-bottom:9px;"><div style="display:flex;justify-content:space-between;margin-bottom:3px;"><span style="font-size:12px;color:#94A3B8;">{lbl}</span><span style="font-family:DM Mono,monospace;font-size:11px;color:{c};">{v}</span></div><div style="background:#1E293B;border-radius:3px;height:5px;"><div style="width:{v}%;height:100%;background:{c};border-radius:3px;"></div></div></div>', unsafe_allow_html=True)

        ac="al-g" if score>=70 else "al-a" if score>=45 else "al-r"
        st.markdown(f'<div class="al {ac}">{ats.get("ats_verdict","")}</div>', unsafe_allow_html=True)

        risks=ats.get("top_ats_risks",[]); fixes=ats.get("quick_ats_fixes",[])
        if risks or fixes:
            rc1,rc2=st.columns(2)
            with rc1:
                if risks:
                    st.markdown('<div class="sec">Top ATS Risks</div>', unsafe_allow_html=True)
                    for i,r in enumerate(risks[:5],1):
                        rc=("#EF4444" if i<=2 else "#F59E0B")
                        st.markdown(f'<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid #1E293B;"><span style="font-family:DM Mono,monospace;font-size:10px;color:{rc};flex-shrink:0;">#{i}</span><span style="font-size:12px;color:#94A3B8;line-height:1.4;">{r}</span></div>', unsafe_allow_html=True)
            with rc2:
                if fixes:
                    st.markdown('<div class="sec">Quick Fixes</div>', unsafe_allow_html=True)
                    for f in fixes[:5]: st.markdown(f'<div class="al al-g" style="margin-bottom:5px;">→ {f}</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">Keywords</div>', unsafe_allow_html=True)
        kc1,kc2=st.columns(2)
        with kc1:
            st.markdown(f'<div class="lbl" style="color:#10B981;">✓ Matched ({len(ats.get("keyword_matches",[]))})</div>', unsafe_allow_html=True)
            st.markdown(_chips(ats.get("keyword_matches",[])[:14],"g"), unsafe_allow_html=True)
        with kc2:
            st.markdown(f'<div class="lbl" style="color:#EF4444;">✗ Missing ({len(ats.get("missing_keywords",[]))})</div>', unsafe_allow_html=True)
            st.markdown(_chips(ats.get("missing_keywords",[])[:14],"r"), unsafe_allow_html=True)

        for issue in ats.get("formatting_issues",[]):
            st.markdown(f'<div class="al al-a">⚠ {issue}</div>', unsafe_allow_html=True)

    # ── SKILLS ──
    with t2:
        score=sk.get("match_score",0)
        c1,c2=st.columns([1,1.2],gap="large")
        with c1:
            if CHARTS:
                fig=_gauge(score,"SKILLS MATCH");
                if fig: _pc(fig)
            traj=sk.get("skill_trajectory","")
            if traj: st.markdown(f'<div class="card" style="padding:12px 15px;"><div class="lbl">Skill Trajectory</div><div style="font-size:12px;color:#94A3B8;margin-top:4px;line-height:1.6;">{traj}</div></div>', unsafe_allow_html=True)
        with c2:
            fig2=_radar(sk.get("matched_skills",[]));
            if fig2: _pc(fig2)
            top5=sk.get("top_5_missing",[])
            if top5:
                st.markdown('<div class="sec">Top 5 Missing</div>', unsafe_allow_html=True)
                for s in top5: st.markdown(f'<div style="display:flex;gap:8px;align-items:center;padding:6px 0;border-bottom:1px solid #1E293B;"><span style="color:#EF4444;font-family:DM Mono,monospace;font-size:13px;">✗</span><span style="font-size:13px;color:#CBD5E1;">{s}</span></div>', unsafe_allow_html=True)

        ac="al-g" if score>=70 else "al-a" if score>=45 else "al-r"
        st.markdown(f'<div class="al {ac}" style="margin:10px 0;">{sk.get("skills_verdict","")}</div>', unsafe_allow_html=True)

        missing=sk.get("missing_critical",[])
        if missing:
            st.markdown('<div class="sec">Critical Gaps — Days to Learn</div>', unsafe_allow_html=True)
            fig3=_bar(missing);
            if fig3: _pc(fig3)
            for item in missing:
                imp=item.get("importance","Medium")
                ic={"Critical":"r","High":"a","Medium":"b"}.get(imp,"b")
                why=item.get("why_it_matters",""); res=item.get("recommended_resource","")
                bc={"Critical":"#EF4444","High":"#F59E0B","Medium":"#3B82F6"}.get(imp,"#3B82F6")
                why_html = f'<div style="font-size:12px;color:#64748B;margin-bottom:3px;">{why}</div>' if why else ""
                res_html  = f'<div style="font-size:12px;color:#10B981;">→ {res}</div>' if res else ""
                st.markdown(f'<div class="card" style="padding:12px 16px;margin-bottom:7px;border-left:3px solid {bc};"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;"><span style="font-size:13px;font-weight:600;color:#E2E8F0;">{item.get("skill","")}</span><span class="chip chip-{ic}">{imp} · ~{item.get("learn_time_days","?")}d</span></div>{why_html}{res_html}</div>', unsafe_allow_html=True)

        matched=sk.get("matched_skills",[])
        if matched:
            st.markdown('<div class="sec">Matched Skills</div>', unsafe_allow_html=True)
            imap={"Required":"r","Preferred":"a","Nice-to-have":"b"}
            for s in matched:
                prof=s.get("proficiency",""); imp=s.get("jd_importance","Required")
                pc2={"Expert":"#10B981","Advanced":"#3B82F6","Intermediate":"#F59E0B","Beginner":"#64748B"}.get(prof,"#64748B")
                st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #1E293B;"><div><span style="font-size:13px;color:#E2E8F0;">{s.get("skill","")}</span><div style="font-size:11px;color:#475569;margin-top:1px;">{s.get("evidence","")[:60]}</div></div><div style="display:flex;gap:6px;align-items:center;flex-shrink:0;"><span class="chip chip-{imap.get(imp,"b")}" style="font-size:9px;">{imp}</span><span style="font-family:DM Mono,monospace;font-size:11px;color:{pc2};">{prof}</span></div></div>', unsafe_allow_html=True)

        for t in sk.get("transferable_skills",[]):
            st.markdown(f'<div class="al al-b">↔ {t}</div>', unsafe_allow_html=True)

    # ── EXPERIENCE ──
    with t3:
        escore=exp.get("experience_score",0); quant=exp.get("quantification_score",0)
        sm=exp.get("seniority_match","?"); prog=exp.get("career_progression","?"); verb=exp.get("action_verb_quality","?")
        cols5=st.columns(5,gap="small")
        for col,(lbl,val,clr) in zip(cols5,[
            ("Score",f"{escore}/100",_sc(escore)),
            ("Seniority",sm,{"Under":"#EF4444","Match":"#10B981","Over":"#F59E0B"}.get(sm,"#3B82F6")),
            ("Quantified",f"{quant}%",_sc(quant)),
            ("Verbs",verb,{"Strong":"#10B981","Mixed":"#F59E0B","Weak":"#EF4444"}.get(verb,"#64748B")),
            ("Progression",prog,{"Strong":"#10B981","Lateral":"#F59E0B","Unclear":"#EF4444"}.get(prog,"#64748B")),
        ]):
            with col: st.markdown(f'<div class="card" style="text-align:center;padding:14px 8px;"><div class="lbl">{lbl}</div><div style="font-family:DM Mono,monospace;font-size:16px;font-weight:600;color:{clr};margin-top:5px;">{val}</div></div>', unsafe_allow_html=True)

        yr=exp.get("years_apparent"); req=exp.get("years_required")
        if yr or req: st.markdown(f'<div class="card" style="display:flex;gap:24px;align-items:center;padding:12px 18px;"><div><div class="lbl">Years Apparent</div><div style="font-family:DM Mono,monospace;font-size:22px;color:#3B82F6;">{yr or "?"}</div></div><div style="color:#1E293B;font-size:22px;">→</div><div><div class="lbl">Years Required</div><div style="font-family:DM Mono,monospace;font-size:22px;color:#64748B;">{req or "?"}</div></div></div>', unsafe_allow_html=True)

        ac="al-g" if escore>=70 else "al-a" if escore>=45 else "al-r"
        st.markdown(f'<div class="al {ac}" style="margin:10px 0;">{exp.get("experience_verdict","")}</div>', unsafe_allow_html=True)

        bullets=exp.get("bullet_quality",[])
        if bullets:
            st.markdown('<div class="sec">Bullet Critique + AI Rewrites</div>', unsafe_allow_html=True)
            for b in bullets:
                rw=b.get("rewritten","")
                rw_html = f'<div><div class="lbl" style="color:#8B5CF6;">Rewritten</div><div style="font-size:13px;color:#C4B5FD;font-style:italic;">{rw}</div></div>' if rw else ""
                st.markdown(f'<div class="card" style="border-left:3px solid #EF4444;padding:14px 18px;margin-bottom:8px;"><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:10px;"><div><div class="lbl" style="color:#EF4444;">Original</div><div style="font-size:13px;color:#94A3B8;font-style:italic;">"{b.get("bullet_excerpt","")}"</div></div><div><div class="lbl" style="color:#F59E0B;">Issue</div><div style="font-size:13px;color:#CBD5E1;">{b.get("issue","")}</div></div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;"><div><div class="lbl" style="color:#3B82F6;">Fix</div><div style="font-size:13px;color:#CBD5E1;">{b.get("fix","")}</div></div>{rw_html}</div></div>', unsafe_allow_html=True)

        bc1,bc2=st.columns(2,gap="medium")
        with bc1:
            if exp.get("best_bullets"):
                st.markdown('<div class="sec">Best Bullets</div>', unsafe_allow_html=True)
                for b in exp.get("best_bullets",[]): st.markdown(f'<div class="al al-g">✨ "{b}"</div>', unsafe_allow_html=True)
        with bc2:
            if exp.get("weakest_bullets"):
                st.markdown('<div class="sec">Weakest Bullets — Rewrite</div>', unsafe_allow_html=True)
                for b in exp.get("weakest_bullets",[]): st.markdown(f'<div class="al al-r">✗ "{b}"</div>', unsafe_allow_html=True)

        projs=exp.get("project_evaluations",[])
        if projs:
            st.markdown('<div class="sec">Project Evaluations</div>', unsafe_allow_html=True)
            pc_cols=st.columns(min(len(projs),3),gap="medium")
            rmap={"High":"g","Medium":"a","Low":"r"}
            for col,proj in zip(pc_cols,projs):
                with col:
                    rc=rmap.get(proj.get("relevance","Low"),"r")
                    ic2={"Strong":"#10B981","Moderate":"#F59E0B","Weak":"#EF4444"}.get(proj.get("impact_clarity","Weak"),"#EF4444")
                    miss=proj.get("missing_info","")
                    miss_html=f'<div style="font-size:11px;color:#F59E0B;margin-top:3px;">{miss[:60]}</div>' if miss else ""
                    st.markdown(f'<div class="card" style="padding:13px;"><div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:7px;">{proj.get("title","")[:40]}</div><span class="chip chip-{rc}">Rel: {proj.get("relevance","")}</span><div style="font-size:11px;color:#64748B;margin-top:6px;">Impact: <span style="color:{ic2};">{proj.get("impact_clarity","")}</span></div>{miss_html}</div>', unsafe_allow_html=True)

    # ── HIRING MANAGER ──
    with t4:
        gut=hm.get("gut_score",0); wi=hm.get("would_interview","No")
        conf=hm.get("decision_confidence","Medium"); hs=hm.get("headline_strength","Adequate")
        wi_c={"Yes":"#10B981","Maybe":"#F59E0B","No":"#EF4444"}.get(wi,"#EF4444")
        wi_lbl={"Yes":"✅ WOULD INTERVIEW","Maybe":"🤔 MAYBE","No":"❌ WOULD NOT INTERVIEW"}.get(wi,"❌ NO")

        c1,c2=st.columns([1,1.5],gap="large")
        with c1:
            if CHARTS:
                fig=_gauge(gut,"HM GUT SCORE");
                if fig: _pc(fig)
            st.markdown(f'<div style="text-align:center;margin-top:-6px;"><span style="background:{wi_c}18;border:1px solid {wi_c};border-radius:20px;padding:7px 18px;font-family:DM Mono,monospace;font-size:12px;color:{wi_c};">{wi_lbl}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;margin-top:7px;font-family:DM Mono,monospace;font-size:10px;color:#64748B;">Confidence: {conf}  ·  Headline: {hs}</div>', unsafe_allow_html=True)
            fi=hm.get("first_impression","")
            if fi: st.markdown(f'<div class="card" style="margin-top:12px;padding:13px 15px;"><div class="lbl">6-Second Impression</div><div style="font-size:13px;color:#94A3B8;font-style:italic;margin-top:5px;line-height:1.6;">"{fi}"</div></div>', unsafe_allow_html=True)

        with c2:
            ko=hm.get("knockout_factors",[])
            if ko:
                st.markdown('<div class="sec" style="margin-top:0;">💀 Knockout Factors</div>', unsafe_allow_html=True)
                for f in ko: st.markdown(f'<div style="background:#1A0505;border:1px solid #7F1D1D;border-left:3px solid #EF4444;border-radius:8px;padding:10px 14px;margin-bottom:6px;font-size:13px;color:#FCA5A5;">{f}</div>', unsafe_allow_html=True)

            reasons=hm.get("rejection_reasons",[])
            if reasons:
                st.markdown('<div class="sec">Rejection Reasons</div>', unsafe_allow_html=True)
                for r in reasons:
                    sev=r.get("severity","Major")
                    sc3={"Knockout":"#EF4444","Major":"#F59E0B","Minor":"#64748B"}.get(sev,"#F59E0B")
                    chip_cls="r" if sev=="Knockout" else "a"
                    fix2=r.get("how_to_fix","")
                    fix_html=f'<div style="font-size:12px;color:#10B981;">→ {fix2}</div>' if fix2 else ""
                    st.markdown(f'<div class="card" style="border-left:3px solid {sc3};padding:12px 16px;margin-bottom:7px;"><div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:13px;color:#CBD5E1;">{r.get("reason","")}</span><span class="chip chip-{chip_cls}" style="font-size:9px;">{sev}</span></div>{fix_html}</div>', unsafe_allow_html=True)

            tp=hm.get("interview_talking_points",[])
            if tp:
                st.markdown('<div class="sec">Interview Talking Points</div>', unsafe_allow_html=True)
                for i,p in enumerate(tp,1): st.markdown(f'<div style="display:flex;gap:10px;align-items:flex-start;background:#0E1420;border:1px solid #1E293B;border-radius:8px;padding:9px 13px;margin-bottom:6px;"><span style="background:#3B82F6;color:#fff;border-radius:50%;min-width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;">{i}</span><span style="font-size:13px;color:#94A3B8;line-height:1.5;">{p}</span></div>', unsafe_allow_html=True)

        rf1,rf2=st.columns(2,gap="medium")
        with rf1:
            if hm.get("red_flags"):
                st.markdown('<div class="sec">Red Flags</div>', unsafe_allow_html=True)
                for f in hm.get("red_flags",[]): st.markdown(f'<div class="al al-r">🚩 {f}</div>', unsafe_allow_html=True)
        with rf2:
            if hm.get("green_flags"):
                st.markdown('<div class="sec">Green Flags</div>', unsafe_allow_html=True)
                for f in hm.get("green_flags",[]): st.markdown(f'<div class="al al-g">✓ {f}</div>', unsafe_allow_html=True)

        nc1,nc2=st.columns(2,gap="medium")
        with nc1:
            if hm.get("narrative_arc"): st.markdown(f'<div class="al al-b"><b>Narrative:</b> {hm.get("narrative_arc","")}</div>', unsafe_allow_html=True)
        with nc2:
            if hm.get("culture_fit_signals"): st.markdown(f'<div class="al al-b"><b>Culture:</b> {hm.get("culture_fit_signals","")}</div>', unsafe_allow_html=True)

        em=hm.get("rejection_email_draft","")
        if em: st.markdown(f'<div class="card" style="border-left:3px solid #EF4444;margin-top:8px;padding:14px 18px;"><div class="lbl" style="color:#EF4444;">The Rejection Email They\'d Send</div><div style="font-family:DM Mono,monospace;font-size:12px;color:#94A3B8;margin-top:7px;font-style:italic;">{em}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="al al-{"g" if gut>=70 else "a" if gut>=45 else "r"}" style="margin-top:10px;">{hm.get("hiring_manager_verdict","")}</div>', unsafe_allow_html=True)

    # ── COORDINATOR ──
    with t5:
        prob=coord.get("rejection_probability","High"); root=coord.get("root_cause_category","Multiple")
        app_v=coord.get("application_verdict","Apply After Fixes"); est=coord.get("estimated_success_after_fixes",0)
        comp2=coord.get("competitor_comparison",""); overall=coord.get("overall_score",0)
        enc=coord.get("encouragement",""); final=coord.get("final_verdict","")

        prob_c={"Very High":"#EF4444","High":"#EF4444","Medium":"#F59E0B","Low":"#10B981"}.get(prob,"#EF4444")
        root_c={"Skills Gap":"#EF4444","Experience Level":"#F59E0B","ATS Filtering":"#3B82F6","Narrative Clarity":"#8B5CF6","Multiple":"#EF4444"}.get(root,"#EF4444")
        av_c={"Apply Now":"#10B981","Apply After Fixes":"#F59E0B","Not Ready Yet":"#EF4444"}.get(app_v,"#F59E0B")
        av_icon={"Apply Now":"🎯","Apply After Fixes":"🔧","Not Ready Yet":"⏳"}.get(app_v,"🔧")
        emoji="💀" if prob in ("Very High","High") else "⚠" if prob=="Medium" else "✓"

        st.markdown(f'<div style="background:linear-gradient(135deg,#0A1628,#0D1219);border:1px solid {prob_c}25;border-left:4px solid {prob_c};border-radius:12px;padding:22px 26px;margin-bottom:18px;display:flex;align-items:center;gap:22px;flex-wrap:wrap;"><div style="font-size:42px;">{emoji}</div><div style="flex:1;min-width:200px;"><div style="font-family:DM Mono,monospace;font-size:11px;color:{prob_c};text-transform:uppercase;letter-spacing:2px;margin-bottom:6px;">{prob} REJECTION RISK</div><div style="font-size:13px;color:#94A3B8;line-height:1.6;">{coord.get("primary_rejection_reason","")}</div></div><div style="text-align:center;"><div style="font-family:DM Mono,monospace;font-size:42px;font-weight:700;color:{_sc(overall)};line-height:1;">{overall}</div><div style="font-family:DM Mono,monospace;font-size:9px;color:#64748B;">OVERALL /100</div><div style="margin-top:8px;font-size:22px;">{av_icon}</div><div style="font-family:DM Mono,monospace;font-size:9px;color:{av_c};text-transform:uppercase;max-width:70px;">{app_v}</div></div></div>', unsafe_allow_html=True)

        rc1,rc2=st.columns([1.2,1],gap="medium")
        with rc1: st.markdown(f'<div class="card" style="border-left:3px solid {root_c};padding:14px 18px;"><div class="lbl">Root Cause Category</div><div style="font-family:DM Mono,monospace;font-size:18px;font-weight:600;color:{root_c};margin:5px 0;">{root}</div></div>', unsafe_allow_html=True)
        with rc2: st.markdown(f'<div class="card" style="text-align:center;padding:14px;"><div class="lbl">After All Fixes</div><div style="font-family:DM Mono,monospace;font-size:36px;font-weight:700;color:{_sc(est)};margin:6px 0;">{est}%</div><div style="font-size:9px;color:#64748B;">Estimated Pass Rate</div></div>', unsafe_allow_html=True)

        if comp2: st.markdown(f'<div class="al al-b">{comp2}</div>', unsafe_allow_html=True)

        gaps=coord.get("top_3_fixable_gaps",[])
        if gaps:
            st.markdown('<div class="sec">Top 3 Fixable Gaps</div>', unsafe_allow_html=True)
            for i,g in enumerate(gaps[:3],1):
                ec={"Days":"g","Weeks":"a","Months":"r"}.get(g.get("effort","Weeks"),"a")
                st.markdown(f'<div class="card" style="padding:13px 17px;margin-bottom:8px;"><div style="display:flex;align-items:flex-start;gap:11px;"><div style="background:linear-gradient(135deg,#10B981,#3B82F6);color:#080C14;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:DM Mono,monospace;font-size:11px;font-weight:600;flex-shrink:0;">#{i}</div><div style="flex:1;"><div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:14px;font-weight:600;color:#E2E8F0;">{g.get("gap","")}</span><span class="chip chip-{ec}">{g.get("effort","")}</span></div><div style="font-size:12px;color:#64748B;margin-bottom:4px;">{g.get("impact","")}</div><div style="font-size:13px;color:#10B981;">→ {g.get("fix","")}</div></div></div></div>', unsafe_allow_html=True)

        qw=coord.get("quick_wins",[]); sec2=coord.get("secondary_rejection_reasons",[])
        if qw or sec2:
            wc1,wc2=st.columns(2,gap="medium")
            with wc1:
                if qw:
                    st.markdown('<div class="sec">⚡ Quick Wins</div>', unsafe_allow_html=True)
                    for w in qw: st.markdown(f'<div class="al al-g">⚡ {w}</div>', unsafe_allow_html=True)
            with wc2:
                if sec2:
                    st.markdown('<div class="sec">Secondary Reasons</div>', unsafe_allow_html=True)
                    for r in sec2: st.markdown(f'<div class="al al-a">⚠ {r}</div>', unsafe_allow_html=True)

        if final: st.markdown(f'<div class="al al-{"g" if overall>=70 else "a" if overall>=45 else "r"}" style="margin-top:8px;">{final}</div>', unsafe_allow_html=True)
        if enc: st.markdown(f'<div class="card" style="border-left:3px solid #10B981;padding:14px 18px;margin-top:8px;"><div class="lbl" style="color:#10B981;">💙 One Genuine Strength</div><div style="font-size:14px;color:#CBD5E1;font-style:italic;margin-top:6px;line-height:1.6;">"{enc}"</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ROADMAP
# ══════════════════════════════════════════════════════
def render_roadmap(results):
    coord=results.get("coordinator",{})
    roadmap=coord.get("30_day_roadmap",coord.get("roadmap",[]))
    if not roadmap: return
    st.markdown('<div class="sec">30-Day Career Improvement Plan</div>', unsafe_allow_html=True)
    wc=["#10B981","#3B82F6","#F59E0B","#10B981"]
    for row in [roadmap[:2],roadmap[2:4]]:
        cols=st.columns(len(row),gap="medium")
        for col,week in zip(cols,row):
            wn=week.get("week",1); c=wc[(int(wn)-1)%4]
            acts="".join([f'<div style="font-size:12px;color:#64748B;padding:5px 0;border-bottom:1px solid #1E293B;line-height:1.4;">› {a}</div>' for a in week.get("actions",[])])
            sm_lbl=week.get("success_metric","")
            sm_html=f'<div style="font-size:11px;color:#10B981;margin-top:8px;padding-top:7px;border-top:1px solid #1E293B;">✓ Done when: {sm_lbl}</div>' if sm_lbl else ""
            with col: st.markdown(f'<div class="card" style="border-top:2px solid {c};padding:15px;"><div style="display:flex;align-items:center;gap:9px;margin-bottom:11px;"><div style="background:{c};color:#080C14;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-family:DM Mono,monospace;font-size:11px;font-weight:600;">{wn}</div><div style="font-size:13px;font-weight:600;color:{c};">{week.get("theme","")}</div></div>{acts}{sm_html}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# DOWNLOAD
# ══════════════════════════════════════════════════════
def render_download(results, company):
    st.markdown('<div class="sec">📥 Download Report</div>', unsafe_allow_html=True)
    c1,c2=st.columns(2,gap="small")
    with c1:
        try:
            pdf=generate_pdf_report(results,company or "N/A")
            if pdf: st.download_button("⬇  Download PDF Report",data=pdf,file_name=f"HireLens_{(company or 'report').replace(' ','_')}.pdf",mime="application/pdf",use_container_width=True)
        except Exception as e: st.warning(f"PDF: {e}")
    with c2:
        st.download_button("⬇  Download JSON Data",data=json.dumps(results,indent=2,default=str).encode(),file_name="HireLens_data.json",mime="application/json",use_container_width=True)


# ══════════════════════════════════════════════════════
# EMPTY STATE
# ══════════════════════════════════════════════════════
def render_empty():
    _s = ("background:linear-gradient(145deg,var(--bg2),var(--bg3));"
          "border:1px solid var(--border2);border-radius:12px;"
          "padding:14px 16px;text-align:left;display:flex;align-items:flex-start;gap:10px;")
    _features = [
        ("\U0001f916", "ATS Analysis",  "Score, format checks & keyword audit"),
        ("\U0001f52c", "Skills Gap",    "Compare vs JD with learn timelines"),
        ("\U0001f4ca", "Experience",    "Bullet critique with AI rewrites"),
        ("\U0001f9e0", "HM Simulator",  "Recruiter gut reaction & knockout flags"),
        ("\U0001f3af", "Root Cause",    "Why you got rejected, specifically"),
        ("\U0001f4c5", "30-Day Plan",   "Week-by-week career improvement roadmap"),
    ]
    cards = "".join(
        '<div style="' + _s + '">'
        '<span style="font-size:18px;flex-shrink:0;">' + ic + '</span>'
        '<div>'
        '<div style="font-size:13px;font-weight:600;color:var(--text);margin-bottom:2px;">' + ti + '</div>'
        '<div style="font-size:11px;color:var(--muted);line-height:1.4;">' + de + '</div>'
        '</div></div>'
        for ic, ti, de in _features
    )

    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                min-height:65vh;text-align:center;padding:40px 20px;">

      <div style="width:80px;height:80px;background:linear-gradient(145deg,#0D1F30,#060E18);
                  border-radius:20px;border:1px solid rgba(0,217,163,.3);
                  display:flex;align-items:center;justify-content:center;margin:0 auto 24px;
                  box-shadow:0 0 40px rgba(0,217,163,.12),0 0 80px rgba(0,217,163,.05);">
        <svg width="40" height="40" viewBox="0 0 46 46" fill="none">
          <circle cx="23" cy="23" r="11" fill="rgba(0,217,163,.08)" stroke="#00D9A3" stroke-width="1.5"/>
          <line x1="23" y1="15" x2="23" y2="18.5" stroke="#00D9A3" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="23" y1="27.5" x2="23" y2="31" stroke="#00D9A3" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="15" y1="23" x2="18.5" y2="23" stroke="#00D9A3" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="27.5" y1="23" x2="31" y2="23" stroke="#00D9A3" stroke-width="1.5" stroke-linecap="round"/>
          <circle cx="23" cy="23" r="2.5" fill="#00D9A3"/>
          <line x1="31.5" y1="31.5" x2="37" y2="37" stroke="#00D9A3" stroke-width="2" stroke-linecap="round"/>
          <circle cx="23" cy="23" r="19" stroke="#00D9A3" stroke-width=".75" stroke-dasharray="4 3" opacity=".3"/>
        </svg>
      </div>

      <div style="font-family:'Outfit',sans-serif;font-size:clamp(26px,3vw,36px);font-weight:800;
                  background:linear-gradient(135deg,#F0F4FF,#00D9A3 55%,#4D9EFF);
                  -webkit-background-clip:text;background-clip:text;color:transparent;
                  letter-spacing:-1px;margin-bottom:10px;">Ready to Analyze</div>

      <div style="font-size:15px;color:var(--muted);max-width:420px;line-height:1.7;margin:0 auto 36px;">
        Upload your resume PDF, paste the job description,
        and click <strong style="color:var(--green);">Analyze Application</strong> in the sidebar.
      </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;'
        'max-width:480px;width:100%;margin:0 auto 32px;">' + cards + '</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
      <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;max-width:500px;margin:0 auto;">
        <span class="tag">ATS Agent</span>
        <span class="tag">Skills Gap</span>
        <span class="tag">Experience</span>
        <span class="tag">HM Sim</span>
        <span class="tag">Coordinator</span>
      </div>
    </div>
    """, unsafe_allow_html=True)



# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
def main():
    if _errs:
        st.warning("Optional modules missing: " + ", ".join(_errs[:2]))

    uploaded, company, jd, brutal, analyze = render_sidebar()

    api_key = (os.environ.get("ANTHROPIC_API_KEY") or
               os.environ.get("OPENAI_API_KEY")     or
               os.environ.get("GOOGLE_API_KEY"))
    demo_mode = not bool(api_key)

    # ── Show results if already done ──
    if st.session_state.get("done") and st.session_state.get("results"):
        results = st.session_state["results"]
        co      = st.session_state.get("company","")
        render_header(co)
        render_scores(results)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="sec">Agent Analysis</div>', unsafe_allow_html=True)
        render_agent_tabs(results)
        st.markdown("<hr>", unsafe_allow_html=True)
        render_roadmap(results)
        st.markdown("<hr>", unsafe_allow_html=True)
        render_download(results,co)
        with st.expander("🔧 Raw JSON"):
            st.json(results)
        return

    # ── Show intro only when not showing results ──
    maybe_show_intro()

    # ── Analyze button ──
    if analyze:
        render_header(company)

        if demo_mode:
            st.markdown('<div class="al al-a">⚡ <b>Demo Mode</b> — No API key. Showing sample analysis. Add ANTHROPIC_API_KEY to .env for live AI.</div>', unsafe_allow_html=True)
            pb=st.progress(0)
            for i in range(5): pb.progress((i+1)*20); time.sleep(0.1)
            pb.progress(100)
            if HAS_MOCK:
                st.session_state["results"] = MOCK_RESULT
                st.session_state["company"] = company or "Demo Company"
                st.session_state["done"]    = True
                st.rerun()
            else:
                st.error("Mock data not found.")
            return

        if not uploaded:
            st.markdown('<div class="al al-r">❌ Please upload your resume PDF in the sidebar.</div>', unsafe_allow_html=True)
            return
        if not jd or len(jd.strip()) < 20:
            st.markdown('<div class="al al-a">⚡ Please paste a job description (at least 20 characters).</div>', unsafe_allow_html=True)
            return

        with st.spinner("📄 Parsing resume PDF..."):
            resume_text = extract_text_from_pdf(uploaded)
        if not resume_text or len(resume_text.strip()) < 50:
            st.error("Could not read PDF text. Use a text-based PDF (not a scanned image).")
            return

        pb=st.progress(5)
        stat=st.empty()
        stat.markdown('<div class="al al-b">🤖 Running 5 specialist AI agents — this takes 60-120 seconds...</div>', unsafe_allow_html=True)
        try:
            from agents.crew_agents import run_hirelens_analysis
            raw=run_hirelens_analysis(resume_text=resume_text,job_description=jd,
                                      company_name=company.strip() or "the company",brutal_mode=brutal)
            pb.progress(100)
            stat.markdown('<div class="al al-g">✅ Analysis complete!</div>', unsafe_allow_html=True)
            result=raw.model_dump(by_alias=True) if hasattr(raw,"model_dump") else raw
            st.session_state["results"]=result; st.session_state["company"]=company
            st.session_state["resume_text"]=resume_text; st.session_state["done"]=True
            st.rerun()
        except Exception as e:
            pb.progress(0); stat.empty()
            st.error(f"Analysis failed: {e}")
            with st.expander("Error details"): st.exception(e)
        return

    # ── Empty state ──
    render_header()
    render_empty()


if __name__ == "__main__":
    main()
