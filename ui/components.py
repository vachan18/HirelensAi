"""
Reusable Streamlit UI components for HireLens AI.
"""
import streamlit as st

try:
    import plotly.graph_objects as go
    import plotly.express as px  # noqa: F401
    import pandas as pd
    _CHARTS_AVAILABLE = True
except ImportError:
    _CHARTS_AVAILABLE = False
    go = None   # type: ignore
    px = None   # type: ignore
    pd = None   # type: ignore


# ─────────────────────────────────────────────
# SCORE GAUGE CHART
# ─────────────────────────────────────────────

def score_gauge(score: int, title: str, size: int = 200) -> go.Figure:
    """Render a gauge chart for a score 0-100."""
    if score >= 75:
        color = "#00C896"
    elif score >= 50:
        color = "#F5A623"
    else:
        color = "#FF4B4B"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"size": 13, "color": "#8B9BB4", "family": "Space Mono"}},
        number={"font": {"size": 32, "color": color, "family": "Space Mono"}, "suffix": "/100"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#2D3748"},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "#1A1F2E",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "#1E2436"},
                {"range": [40, 70], "color": "#1E2A36"},
                {"range": [70, 100], "color": "#1E3629"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.75,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=size,
        margin=dict(l=20, r=20, t=30, b=10),
        font={"family": "Space Mono"},
    )
    return fig


# ─────────────────────────────────────────────
# SKILLS RADAR CHART
# ─────────────────────────────────────────────

def skills_radar(matched_skills: list) -> go.Figure:
    """Radar chart of matched skill proficiencies."""
    proficiency_map = {"Beginner": 25, "Intermediate": 50, "Advanced": 75, "Expert": 100}
    if not matched_skills:
        return None
    labels = [s.get("skill", "?")[:20] for s in matched_skills[:8]]
    values = [proficiency_map.get(s.get("proficiency", "Intermediate"), 50) for s in matched_skills[:8]]
    labels.append(labels[0])
    values.append(values[0])

    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        fillcolor="rgba(0, 200, 150, 0.15)",
        line=dict(color="#00C896", width=2),
        marker=dict(color="#00C896", size=6),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#4A5568", gridcolor="#2D3748"),
            angularaxis=dict(color="#8B9BB4", gridcolor="#2D3748"),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=320,
        margin=dict(l=40, r=40, t=20, b=20),
        font={"color": "#8B9BB4", "family": "Space Mono", "size": 10},
    )
    return fig


# ─────────────────────────────────────────────
# SKILLS GAP BAR CHART
# ─────────────────────────────────────────────

def skills_gap_chart(missing_critical: list) -> go.Figure:
    """Horizontal bar chart of missing skills by learn time."""
    if not missing_critical:
        return None

    df = pd.DataFrame(missing_critical)
    df = df.sort_values("learn_time_days", ascending=True)

    importance_colors = {
        "Critical": "#FF4B4B",
        "High": "#F5A623",
        "Medium": "#4299E1",
    }
    colors = [importance_colors.get(imp, "#4299E1") for imp in df.get("importance", ["Medium"] * len(df))]

    fig = go.Figure(go.Bar(
        x=df.get("learn_time_days", [0] * len(df)),
        y=df.get("skill", [""]),
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f'{d}d' for d in df.get("learn_time_days", [])],
        textposition="outside",
        textfont=dict(color="#8B9BB4", size=10, family="Space Mono"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(200, len(df) * 45),
        xaxis=dict(
            title="Days to Learn",
            color="#4A5568",
            gridcolor="#2D3748",
            titlefont=dict(color="#8B9BB4", size=11),
        ),
        yaxis=dict(color="#C5D0E6", tickfont=dict(size=11, family="Space Mono")),
        margin=dict(l=10, r=60, t=10, b=40),
        font={"color": "#8B9BB4", "family": "Space Mono"},
    )
    return fig


# ─────────────────────────────────────────────
# METRIC CARD
# ─────────────────────────────────────────────

def metric_card(label: str, value: str, subtitle: str = "", color: str = "#00C896"):
    """Render a styled metric card."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1A1F2E 0%, #1E2436 100%);
        border: 1px solid #2D3748;
        border-left: 3px solid {color};
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 12px;
    ">
        <div style="color: #8B9BB4; font-size: 11px; font-family: 'Space Mono', monospace; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">{label}</div>
        <div style="color: {color}; font-size: 24px; font-weight: 700; font-family: 'Space Mono', monospace;">{value}</div>
        {f'<div style="color: #4A5568; font-size: 12px; margin-top: 4px;">{subtitle}</div>' if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# STATUS BADGE
# ─────────────────────────────────────────────

def status_badge(text: str, kind: str = "neutral"):
    colors = {
        "success": ("#00C896", "#0D2420"),
        "warning": ("#F5A623", "#2A1F0D"),
        "danger": ("#FF4B4B", "#2A0D0D"),
        "neutral": ("#4299E1", "#0D1A2A"),
    }
    fg, bg = colors.get(kind, colors["neutral"])
    st.markdown(f"""
    <span style="
        background: {bg};
        color: {fg};
        border: 1px solid {fg};
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 12px;
        font-family: 'Space Mono', monospace;
        font-weight: 600;
        letter-spacing: 0.5px;
    ">{text}</span>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ROADMAP WEEK CARD
# ─────────────────────────────────────────────

def roadmap_week(week_num: int, theme: str, actions: list):
    week_colors = ["#FF6B6B", "#F5A623", "#4299E1", "#00C896"]
    color = week_colors[(week_num - 1) % 4]
    actions_html = "".join([
        f'<div style="color:#C5D0E6;font-size:13px;padding:5px 0;border-bottom:1px solid #2D3748;">→ {a}</div>'
        for a in actions
    ])
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1A1F2E 0%, #1E2436 100%);
        border: 1px solid #2D3748;
        border-top: 3px solid {color};
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
    ">
        <div style="display:flex;align-items:center;margin-bottom:12px;">
            <div style="
                background: {color};
                color: #0D1117;
                border-radius: 50%;
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-family: 'Space Mono', monospace;
                font-size: 12px;
                margin-right: 12px;
                flex-shrink: 0;
            ">W{week_num}</div>
            <div style="color:{color};font-weight:700;font-family:'Space Mono',monospace;font-size:14px;">{theme}</div>
        </div>
        {actions_html}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# VERDICT BANNER
# ─────────────────────────────────────────────

def verdict_banner(prob: str, reason: str, score: int):
    prob_config = {
        "Very High": ("#FF4B4B", "💀", "REJECTION VERY LIKELY"),
        "High": ("#F5A623", "⚠️", "HIGH REJECTION RISK"),
        "Medium": ("#4299E1", "🎯", "MODERATE CHANCES"),
        "Low": ("#00C896", "✅", "STRONG CANDIDATE"),
    }
    color, emoji, label = prob_config.get(prob, ("#4299E1", "🎯", "MODERATE CHANCES"))
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1A1F2E 0%, #1E2436 100%);
        border: 2px solid {color};
        border-radius: 14px;
        padding: 28px 32px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 0 40px {color}20;
    ">
        <div style="font-size: 48px; margin-bottom: 12px;">{emoji}</div>
        <div style="color: {color}; font-size: 22px; font-weight: 700; font-family: 'Space Mono', monospace; letter-spacing: 2px; margin-bottom: 8px;">{label}</div>
        <div style="color: #C5D0E6; font-size: 15px; max-width: 600px; margin: 0 auto; line-height: 1.6;">{reason}</div>
        <div style="color: {color}; font-size: 40px; font-family: 'Space Mono', monospace; font-weight: 700; margin-top: 16px;">{score}<span style="font-size:18px;color:#4A5568;">/100</span></div>
    </div>
    """, unsafe_allow_html=True)
