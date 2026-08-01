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

MAX_CONTENT_WIDTH = 1200  # 넓은 화면에서 카테고리 적은 차트가 과하게 늘어지는 것을 막기 위한 콘텐츠 최대 폭(px)


def apply_page_style():
    """페이지 전체 콘텐츠 폭을 제한(가운데 정렬). st.navigation 페이지마다 새로 렌더링되므로 매번 호출."""
    st.markdown(
        f"""
<style>
[data-testid="stMain"] .block-container {{
    max-width: {MAX_CONTENT_WIDTH}px;
    margin-left: auto;
    margin-right: auto;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_hero(title, subtitle=None, meta=None):
    """페이지 상단 히어로 배너. meta는 작성자 등 부가 정보용 선택적 3번째 줄."""
    apply_page_style()
    subtitle_html = (
        f'<div style="font-size:0.95rem;color:{COLOR_NEUTRAL};margin-top:0.3rem;">{subtitle}</div>'
        if subtitle
        else ""
    )
    meta_html = (
        f'<div style="font-size:0.8rem;color:{COLOR_NEUTRAL};margin-top:0.5rem;">{meta}</div>'
        if meta
        else ""
    )
    st.markdown(
        f"""
<div style="background:{COLOR_BAR}12;border-left:4px solid {COLOR_BAR};
border-radius:8px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
    <div style="font-size:28px;font-weight:700;color:#0b0b0b;">{title}</div>
    {subtitle_html}
    {meta_html}
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
