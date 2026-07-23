import numpy as np
import pandas as pd
import plotly.express as px
from google.cloud import bigquery

PROJECT = "project-6fcaf3a6-ee2b-4616-8de"
DATASET = "data"

OUTLIER_THRESHOLD_HOURS = 25


def load_agent_burnout_csat():
    client = bigquery.Client(project=PROJECT)
    query = f"""
        SELECT
            a.agent_id AS agent_id,
            a.overtime_hours_avg AS overtime_hours_avg,
            AVG(s.csat) AS csat_avg
        FROM `{DATASET}.data_agents` AS a
        JOIN `{DATASET}.data_consultations` AS c ON a.agent_id = c.agent_id
        JOIN `{DATASET}.data_satisfaction` AS s ON c.consult_id = s.consult_id
        GROUP BY a.agent_id, a.overtime_hours_avg
    """
    return client.query(query).result().to_dataframe()


def corr_and_slope(df):
    r = df["overtime_hours_avg"].corr(df["csat_avg"])
    slope, intercept = np.polyfit(df["overtime_hours_avg"], df["csat_avg"], 1)
    return r, slope


def main():
    df = load_agent_burnout_csat()

    df_full = df.copy()
    df_excl = df[df["overtime_hours_avg"] < OUTLIER_THRESHOLD_HOURS].copy()

    GROUP_FULL = "전체 포함"
    GROUP_EXCL = "이상치 제외 (AG02·AG03)"

    df_full["구분"] = GROUP_FULL
    df_excl["구분"] = GROUP_EXCL
    combined = pd.concat([df_full, df_excl], ignore_index=True)

    r_full, slope_full = corr_and_slope(df_full)
    r_excl, slope_excl = corr_and_slope(df_excl)

    fig = px.scatter(
        combined,
        x="overtime_hours_avg",
        y="csat_avg",
        facet_col="구분",
        category_orders={"구분": [GROUP_FULL, GROUP_EXCL]},
        trendline="ols",
        custom_data=["agent_id", "overtime_hours_avg", "csat_avg"],
        title="번아웃(초과근무 시간)과 CSAT 평균 — 이상치 포함 vs 제외 비교",
        labels={"overtime_hours_avg": "월평균 초과근무 시간", "csat_avg": "CSAT 평균"},
    )

    fig.update_traces(
        selector=dict(mode="markers"),
        marker=dict(size=10, color="#2a78d6", opacity=0.8),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "초과근무 시간: %{customdata[1]}시간<br>"
            "CSAT 평균: %{customdata[2]:.2f}"
            "<extra></extra>"
        ),
    )
    fig.update_traces(selector=dict(mode="lines"), line=dict(color="#d03b3b", width=2))

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.add_annotation(
        xref="x domain",
        yref="y domain",
        x=0.98,
        y=0.98,
        text=f"r = {r_full:.3f}<br>기울기 = {slope_full:.3f}",
        showarrow=False,
        align="right",
        font=dict(size=14, color="#0b0b0b"),
        bgcolor="rgba(255,255,255,0.7)",
    )
    fig.add_annotation(
        xref="x2 domain",
        yref="y2 domain",
        x=0.98,
        y=0.98,
        text=f"r = {r_excl:.3f}<br>기울기 = {slope_excl:.3f}",
        showarrow=False,
        align="right",
        font=dict(size=14, color="#0b0b0b"),
        bgcolor="rgba(255,255,255,0.7)",
    )

    fig.update_layout(showlegend=False)

    print(f"[전체 포함]   n={len(df_full)}, r={r_full:.3f}, 기울기={slope_full:.3f}")
    print(f"[이상치 제외] n={len(df_excl)}, r={r_excl:.3f}, 기울기={slope_excl:.3f}")

    fig.show()


if __name__ == "__main__":
    main()
