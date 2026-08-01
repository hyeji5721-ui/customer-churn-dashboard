"""여러 페이지에서 공유하는 색상·레이아웃·공통 렌더링 컴포넌트."""

import streamlit as st

# ---------------------------------------------------------------------------
# 색상 팔레트 (기존 app.py에서 쓰던 색을 그대로 상수화)
# ---------------------------------------------------------------------------
COLOR_BAR = "#2a78d6"       # 기본 막대/강조 색상 (파랑)
COLOR_CRITICAL = "#d03b3b"  # 위험·부정 강조 (빨강)
COLOR_POSITIVE = "#0ca30c"  # 긍정·양호 (초록)
COLOR_WARNING = "#c9a227"   # 주의 (황색)
COLOR_NEUTRAL = "#898781"   # 중립·평균선·보조 텍스트 (회색)

CHART_LAYOUT = dict(
    font=dict(family="sans-serif", color="#0b0b0b"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=60, b=40, l=40, r=20),
    hoverlabel=dict(bgcolor="white", font_size=13),
)

PLOTLY_CONFIG = {"displayModeBar": False}


def render_hero(title, subtitle=None):
    """페이지 상단 히어로 배너."""
    subtitle_html = (
        f'<div style="font-size:0.95rem;color:{COLOR_NEUTRAL};margin-top:0.3rem;">{subtitle}</div>'
        if subtitle
        else ""
    )
    st.markdown(
        f"""
<div style="background:{COLOR_BAR}12;border-left:4px solid {COLOR_BAR};
border-radius:8px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
    <div style="font-size:1.5rem;font-weight:700;color:#0b0b0b;">{title}</div>
    {subtitle_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_stat_tile(label, value, caption=None):
    """KPI 카드 1개. st.columns()의 각 컬럼 안에서 호출."""
    caption_html = (
        f'<div style="font-size:0.8rem;color:{COLOR_NEUTRAL};margin-top:0.2rem;">{caption}</div>'
        if caption
        else ""
    )
    st.markdown(
        f"""
<div style="background:#f7f7f5;border:1px solid #e1e0d9;border-radius:8px;
padding:1rem 1.2rem;">
    <div style="font-size:0.85rem;color:{COLOR_NEUTRAL};font-weight:600;">{label}</div>
    <div style="font-size:1.6rem;font-weight:700;color:#0b0b0b;margin-top:0.2rem;">{value}</div>
    {caption_html}
</div>
""",
        unsafe_allow_html=True,
    )
