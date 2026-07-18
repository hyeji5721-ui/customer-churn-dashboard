import csv
import os

import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8-sig") as fp:
        return list(csv.DictReader(fp))


def churn_stats(customers):
    total = len(customers)
    churned = sum(1 for r in customers if r["churn_yn"].strip().upper() == "Y")
    rate = churned / total * 100 if total else 0.0
    return total, churned, rate


def main():
    voc_rows = load_csv("data_voc.csv")
    customers = load_csv("data_customers.csv")
    cust_by_id = {r["customer_id"]: r for r in customers}

    target_ids = {
        r["customer_id"]
        for r in voc_rows
        if r["category"] == "해지관련" and r["sentiment"] == "부정"
    }
    voc_customers = [cust_by_id[cid] for cid in target_ids if cid in cust_by_id]

    overall_total, overall_churned, overall_rate = churn_stats(customers)
    voc_total, voc_churned, voc_rate = churn_stats(voc_customers)

    df_rows = [
        {
            "구분": "전체 고객",
            "이탈율": overall_rate,
            "고객수": overall_total,
            "이탈고객수": overall_churned,
        },
        {
            "구분": "해지관련 부정 VOC 이력 있음",
            "이탈율": voc_rate,
            "고객수": voc_total,
            "이탈고객수": voc_churned,
        },
    ]

    fig = px.bar(
        df_rows,
        x="구분",
        y="이탈율",
        color="구분",
        color_discrete_map={
            "전체 고객": "#2a78d6",
            "해지관련 부정 VOC 이력 있음": "#d03b3b",
        },
        custom_data=["고객수", "이탈고객수"],
        title="전체 고객 vs 해지관련 부정 VOC 고객 이탈율 비교",
        labels={"이탈율": "이탈율 (%)"},
        text=[f"{r['이탈율']:.1f}%" for r in df_rows],
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

    fig.update_layout(showlegend=False, yaxis_range=[0, max(r["이탈율"] for r in df_rows) * 1.3])

    fig.show()


if __name__ == "__main__":
    main()
