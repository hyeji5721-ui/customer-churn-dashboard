import os

import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def bucket_label(count):
    if count == 0:
        return "0회"
    if count == 1:
        return "1회"
    return "2회 이상"


def main():
    consultations = pd.read_csv(os.path.join(DATA_DIR, "data_consultations.csv"), encoding="utf-8-sig")
    customers = pd.read_csv(os.path.join(DATA_DIR, "data_customers.csv"), encoding="utf-8-sig")

    recontact_counts = (
        consultations[consultations["is_recontact"] == "Y"]
        .groupby("customer_id")
        .size()
        .rename("recontact_count")
    )

    customers = customers.merge(recontact_counts, on="customer_id", how="left")
    customers["recontact_count"] = customers["recontact_count"].fillna(0).astype(int)
    customers["bucket"] = customers["recontact_count"].apply(bucket_label)

    overall_churn_rate = (customers["churn_yn"] == "Y").mean() * 100

    bucket_order = ["0회", "1회", "2회 이상"]
    summary = (
        customers.groupby("bucket")
        .agg(
            churn_rate=("churn_yn", lambda s: (s == "Y").mean() * 100),
            customer_count=("customer_id", "count"),
            churned_count=("churn_yn", lambda s: (s == "Y").sum()),
        )
        .reindex(bucket_order)
        .reset_index()
    )

    fig = px.bar(
        summary,
        x="bucket",
        y="churn_rate",
        color="bucket",
        category_orders={"bucket": bucket_order},
        color_discrete_map={
            "0회": "#2a78d6",
            "1회": "#2a78d6",
            "2회 이상": "#d03b3b",
        },
        custom_data=["customer_count", "churned_count"],
        text=summary["churn_rate"].map(lambda v: f"{v:.1f}%"),
        title="재문의 횟수 구간별 이탈율",
        labels={"bucket": "재문의 횟수", "churn_rate": "이탈율 (%)"},
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

    fig.add_hline(
        y=overall_churn_rate,
        line_dash="dash",
        line_color="#898781",
        annotation_text=f"전체 평균 이탈율 {overall_churn_rate:.1f}%",
        annotation_position="top right",
    )

    fig.update_layout(showlegend=False, yaxis_range=[0, summary["churn_rate"].max() * 1.3])

    fig.show()


if __name__ == "__main__":
    main()
