import os

import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

HIGHLIGHT_REGIONS = {"부산", "대구"}
HIGHLIGHT_COLOR = "#d03b3b"
DEFAULT_COLOR = "#2a78d6"
CAPTION_REGION = "인천"


def main():
    customers = pd.read_csv(os.path.join(DATA_DIR, "data_customers.csv"), encoding="utf-8-sig")

    summary = (
        customers.groupby("region")
        .agg(
            customer_count=("customer_id", "count"),
            churned_count=("churn_yn", lambda s: (s == "Y").sum()),
        )
        .reset_index()
    )
    summary["churn_rate"] = summary["churned_count"] / summary["customer_count"] * 100

    color_map = {
        region: (HIGHLIGHT_COLOR if region in HIGHLIGHT_REGIONS else DEFAULT_COLOR)
        for region in summary["region"]
    }

    fig = px.bar(
        summary,
        x="region",
        y="churn_rate",
        color="region",
        color_discrete_map=color_map,
        custom_data=["customer_count", "churned_count"],
        text=summary["churn_rate"].map(lambda v: f"{v:.1f}%"),
        title="지역별 고객 수 및 이탈율",
        labels={"region": "지역", "churn_rate": "이탈율 (%)"},
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "고객 수: %{customdata[0]}명<br>"
            "이탈 고객 수: %{customdata[1]}명<br>"
            "이탈율: %{y:.1f}%"
            "<extra></extra>"
        ),
    )

    caption_row = summary[summary["region"] == CAPTION_REGION].iloc[0]
    caption_text = (
        f"* {CAPTION_REGION}은 표본이 {int(caption_row['customer_count'])}건이지만 "
        f"이탈 {int(caption_row['churned_count'])}건뿐이라 이탈율 수치의 신뢰도가 낮습니다."
    )

    fig.update_layout(
        showlegend=False,
        yaxis_range=[0, summary["churn_rate"].max() * 1.3],
        margin=dict(b=100),
        annotations=[
            dict(
                text=caption_text,
                xref="paper",
                yref="paper",
                x=0,
                y=-0.25,
                showarrow=False,
                font=dict(size=12, color="#52514e"),
                align="left",
            )
        ],
    )

    fig.show()


if __name__ == "__main__":
    main()
