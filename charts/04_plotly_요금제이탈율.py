import os

import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

HIGHLIGHT_PLAN = "베이직"
HIGHLIGHT_COLOR = "#d03b3b"
DEFAULT_COLOR = "#2a78d6"


def main():
    customers = pd.read_csv(os.path.join(DATA_DIR, "data_customers.csv"), encoding="utf-8-sig")

    summary = (
        customers.groupby("plan")
        .agg(
            customer_count=("customer_id", "count"),
            churned_count=("churn_yn", lambda s: (s == "Y").sum()),
        )
        .reset_index()
    )
    summary["churn_rate"] = summary["churned_count"] / summary["customer_count"] * 100

    color_map = {
        plan: (HIGHLIGHT_COLOR if plan == HIGHLIGHT_PLAN else DEFAULT_COLOR)
        for plan in summary["plan"]
    }

    fig = px.bar(
        summary,
        x="plan",
        y="churn_rate",
        color="plan",
        color_discrete_map=color_map,
        custom_data=["customer_count", "churned_count"],
        text=summary["churn_rate"].map(lambda v: f"{v:.1f}%"),
        title="요금제별 고객 수 및 이탈율",
        labels={"plan": "요금제", "churn_rate": "이탈율 (%)"},
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

    fig.update_layout(showlegend=False, yaxis_range=[0, summary["churn_rate"].max() * 1.3])

    fig.show()


if __name__ == "__main__":
    main()
