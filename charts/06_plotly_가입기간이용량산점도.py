import os

import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

REFERENCE_DATE = pd.Timestamp("2024-12-31")


def main():
    customers = pd.read_csv(os.path.join(DATA_DIR, "data_customers.csv"), encoding="utf-8-sig")
    usage = pd.read_csv(os.path.join(DATA_DIR, "data_usage_history.csv"), encoding="utf-8-sig")

    customers["join_date"] = pd.to_datetime(customers["join_date"])
    customers["tenure_months"] = (
        (REFERENCE_DATE.to_period("M") - customers["join_date"].dt.to_period("M"))
        .apply(lambda offset: offset.n)
    )

    avg_usage = usage.groupby("customer_id")["data_gb"].mean().rename("avg_data_gb")

    merged = customers.merge(avg_usage, on="customer_id", how="inner")

    fig = px.scatter(
        merged,
        x="tenure_months",
        y="avg_data_gb",
        color="churn_yn",
        color_discrete_map={"N": "#2a78d6", "Y": "#d03b3b"},
        custom_data=["customer_id", "tenure_months", "avg_data_gb", "churn_yn"],
        title="가입기간 vs 평균 데이터 사용량 (이탈 여부별)",
        labels={
            "tenure_months": "가입기간 (개월)",
            "avg_data_gb": "평균 데이터 사용량 (GB)",
            "churn_yn": "이탈 여부",
        },
    )

    fig.update_traces(
        marker=dict(size=8, opacity=0.75),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "가입기간: %{customdata[1]}개월<br>"
            "평균 데이터 사용량: %{customdata[2]:.2f}GB<br>"
            "이탈 여부: %{customdata[3]}"
            "<extra></extra>"
        ),
    )

    fig.show()


if __name__ == "__main__":
    main()
