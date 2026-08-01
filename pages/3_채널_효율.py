import streamlit as st
import plotly.graph_objects as go

import common as c
from dashboard_core import get_bq_client, BQ_DATASET

HIGHLIGHT_CHANNEL = "SNS광고"  # 가장 비효율적인 채널


@st.cache_data
def load_channel_cpl_recent():
    """완료 캠페인 기준 채널별 3개월(2024-05~07) 유입 1건당 비용."""
    client = get_bq_client()
    query = f"""
        SELECT channel, spend_completed, signups_completed, cost_per_lead
        FROM `{BQ_DATASET}.data_marketing_cpl_by_channel`
        ORDER BY cost_per_lead DESC
    """
    return client.query(query).result().to_dataframe()


@st.cache_data
def load_channel_cpl_cumulative():
    """채널별 누적(2019-01~2024-06) 유입 1건당 비용."""
    client = get_bq_client()
    query = f"""
        SELECT
            channel,
            SUM(spend) AS spend,
            SUM(signups) AS signups,
            ROUND(SUM(spend) / NULLIF(SUM(signups), 0), 0) AS cost_per_lead
        FROM `{BQ_DATASET}.data_marketing_spend`
        WHERE month BETWEEN '2019-01' AND '2024-06'
        GROUP BY channel
    """
    return client.query(query).result().to_dataframe()


def build_chart_cpl_by_channel(recent_df):
    df = recent_df.sort_values("cost_per_lead", ascending=False)
    colors = [c.COLOR_CRITICAL if ch == HIGHLIGHT_CHANNEL else c.COLOR_NEUTRAL for ch in df["channel"]]

    fig = go.Figure(
        go.Bar(
            x=df["channel"],
            y=df["cost_per_lead"],
            marker_color=colors,
            text=[f"{v:,.0f}원" for v in df["cost_per_lead"]],
            textposition="outside",
            customdata=df[["spend_completed", "signups_completed"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>유입 1건당 비용: %{y:,.0f}원<br>"
                "실집행: %{customdata[0]:,.0f}원<br>유입건수: %{customdata[1]}건<extra></extra>"
            ),
        )
    )
    layout = dict(c.CHART_LAYOUT)
    fig.update_layout(
        title="채널별 유입 1건당 비용 (완료 캠페인 기준, 2024-05~07)",
        xaxis_title="채널",
        yaxis_title="유입 1건당 비용 (원)",
        showlegend=False,
        **layout,
    )
    return fig


def build_chart_cpl_compare(recent_df, cumulative_df):
    merged = (
        recent_df[["channel", "cost_per_lead"]]
        .rename(columns={"cost_per_lead": "recent"})
        .merge(
            cumulative_df[["channel", "cost_per_lead"]].rename(columns={"cost_per_lead": "cumulative"}),
            on="channel",
            how="outer",
        )
        .sort_values("cumulative", ascending=False)
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=merged["channel"],
            y=merged["recent"],
            name="3개월 단가 (완료 캠페인)",
            marker_color=c.COLOR_NEUTRAL,
            text=[f"{v:,.0f}" for v in merged["recent"]],
            textposition="outside",
        )
    )
    fig.add_trace(
        go.Bar(
            x=merged["channel"],
            y=merged["cumulative"],
            name="누적 단가 (2019-01~2024-06)",
            marker_color=c.COLOR_BAR,
            text=[f"{v:,.0f}" for v in merged["cumulative"]],
            textposition="outside",
        )
    )
    layout = dict(c.CHART_LAYOUT)
    fig.update_layout(
        title="채널별 3개월 단가 vs 누적 단가 비교",
        xaxis_title="채널",
        yaxis_title="유입 1건당 비용 (원)",
        barmode="group",
        **layout,
    )
    return fig


def render_channel_efficiency_page():
    c.render_hero("채널 효율", "채널별 유입 1건당 비용 — 다음 분기 예산 배분의 근거")

    recent_df = load_channel_cpl_recent()
    cumulative_df = load_channel_cpl_cumulative()

    total_spend = recent_df["spend_completed"].sum()
    total_signups = recent_df["signups_completed"].sum()
    avg_cpl = total_spend / total_signups if total_signups else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        c.render_stat_tile("총 집행액", f"{total_spend:,.0f}원", "완료 캠페인, 2024-05~07")
    with col2:
        c.render_stat_tile("총 유입", f"{total_signups:,.0f}건", "완료 캠페인, 2024-05~07")
    with col3:
        c.render_stat_tile("평균 유입단가", f"{avg_cpl:,.0f}원", "총 집행액 ÷ 총 유입")

    st.subheader("① 채널별 유입 1건당 비용")
    st.plotly_chart(build_chart_cpl_by_channel(recent_df), width="stretch", config=c.PLOTLY_CONFIG)

    st.subheader("② 3개월 단가 vs 누적 단가 비교")
    st.plotly_chart(build_chart_cpl_compare(recent_df, cumulative_df), width="stretch", config=c.PLOTLY_CONFIG)


render_channel_efficiency_page()
