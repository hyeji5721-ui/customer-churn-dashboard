import os

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def main():
    consultations = pd.read_csv(os.path.join(DATA_DIR, "data_consultations.csv"), encoding="utf-8-sig")
    satisfaction = pd.read_csv(os.path.join(DATA_DIR, "data_satisfaction.csv"), encoding="utf-8-sig")

    merged = satisfaction.merge(
        consultations[["consult_id", "channel", "is_recontact"]],
        on="consult_id",
        how="inner",
    )

    summary = (
        merged.groupby("channel")
        .agg(
            csat_avg=("csat", "mean"),
            recontact_rate=("is_recontact", lambda s: (s == "Y").mean() * 100),
            count=("consult_id", "count"),
        )
        .reset_index()
        .sort_values("csat_avg", ascending=True)
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=summary["channel"],
            y=summary["csat_avg"],
            name="CSAT 평균",
            marker_color="#2a78d6",
            customdata=summary[["recontact_rate", "count"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "CSAT 평균: %{y:.2f}<br>"
                "재문의율: %{customdata[0]:.1f}%"
                "<extra></extra>"
            ),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=summary["channel"],
            y=summary["recontact_rate"],
            name="재문의율",
            mode="lines+markers",
            line=dict(color="#d03b3b", width=3),
            marker=dict(size=9, color="#d03b3b"),
            customdata=summary[["csat_avg", "count"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "재문의율: %{y:.1f}%<br>"
                "CSAT 평균: %{customdata[0]:.2f}"
                "<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="채널별 CSAT 평균 vs 재문의율 (CSAT 낮은 순)",
        xaxis_title="채널",
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="CSAT 평균", secondary_y=False)
    fig.update_yaxes(title_text="재문의율 (%)", secondary_y=True)

    fig.show()


if __name__ == "__main__":
    main()
