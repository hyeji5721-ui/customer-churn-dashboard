import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery
from plotly.subplots import make_subplots

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

REFERENCE_DATE = pd.Timestamp("2024-12-31")

BQ_PROJECT = "project-6fcaf3a6-ee2b-4616-8de"
BQ_DATASET = "data"


@st.cache_data
def load_csv(filename):
    return pd.read_csv(os.path.join(DATA_DIR, filename), encoding="utf-8-sig")


@st.cache_data
def load_all():
    return {
        "customers": load_csv("data_customers.csv"),
        "consultations": load_csv("data_consultations.csv"),
        "satisfaction": load_csv("data_satisfaction.csv"),
        "voc": load_csv("data_voc.csv"),
        "usage_history": load_csv("data_usage_history.csv"),
    }


@st.cache_data
def load_burnout_csat_bq():
    client = bigquery.Client(project=BQ_PROJECT)
    query = f"""
        SELECT
            a.agent_id AS agent_id,
            a.team AS team,
            a.overtime_hours_avg AS overtime_hours_avg,
            AVG(s.csat) AS csat_avg
        FROM `{BQ_DATASET}.data_agents` AS a
        JOIN `{BQ_DATASET}.data_consultations` AS c ON a.agent_id = c.agent_id
        JOIN `{BQ_DATASET}.data_satisfaction` AS s ON c.consult_id = s.consult_id
        GROUP BY a.agent_id, a.team, a.overtime_hours_avg
    """
    return client.query(query).result().to_dataframe()


@st.cache_data
def load_training_csat_bq():
    client = bigquery.Client(project=BQ_PROJECT)
    query = f"""
        SELECT a.team AS team, a.training_completed_yn AS training_completed_yn, s.csat AS csat
        FROM `{BQ_DATASET}.data_agents` AS a
        JOIN `{BQ_DATASET}.data_consultations` AS c ON a.agent_id = c.agent_id
        JOIN `{BQ_DATASET}.data_satisfaction` AS s ON c.consult_id = s.consult_id
    """
    return client.query(query).result().to_dataframe()


@st.cache_data
def load_training_recontact_bq():
    client = bigquery.Client(project=BQ_PROJECT)
    query = f"""
        SELECT a.team AS team, a.training_completed_yn AS training_completed_yn, c.is_recontact AS is_recontact
        FROM `{BQ_DATASET}.data_agents` AS a
        JOIN `{BQ_DATASET}.data_consultations` AS c ON a.agent_id = c.agent_id
    """
    return client.query(query).result().to_dataframe()


@st.cache_data
def load_agent_enps_bq():
    client = bigquery.Client(project=BQ_PROJECT)
    query = f"""
        SELECT agent_id, team, agent_satisfaction
        FROM `{BQ_DATASET}.data_agents`
        WHERE agent_satisfaction IS NOT NULL
    """
    return client.query(query).result().to_dataframe()


def churn_stats(customers):
    total = len(customers)
    churned = int((customers["churn_yn"] == "Y").sum())
    rate = churned / total * 100 if total else 0.0
    return total, churned, rate


# ---------------------------------------------------------------------------
# ① VOC로 본 이탈
# ---------------------------------------------------------------------------
def build_chart_1(customers, voc):
    cust_by_id = customers.set_index("customer_id")
    target_ids = set(
        voc.loc[(voc["category"] == "해지관련") & (voc["sentiment"] == "부정"), "customer_id"]
    )
    voc_customers = cust_by_id.loc[cust_by_id.index.intersection(target_ids)]

    overall_total, overall_churned, overall_rate = churn_stats(customers)
    voc_total, voc_churned, voc_rate = churn_stats(voc_customers.reset_index())

    df_rows = [
        {"구분": "전체 고객", "이탈율": overall_rate, "고객수": overall_total, "이탈고객수": overall_churned},
        {"구분": "해지관련 부정 VOC 이력 있음", "이탈율": voc_rate, "고객수": voc_total, "이탈고객수": voc_churned},
    ]

    fig = px.bar(
        df_rows,
        x="구분",
        y="이탈율",
        color="구분",
        color_discrete_map={"전체 고객": "#2a78d6", "해지관련 부정 VOC 이력 있음": "#d03b3b"},
        custom_data=["고객수", "이탈고객수"],
        title="전체 고객 vs 해지관련 부정 VOC 고객 이탈율 비교",
        labels={"이탈율": "이탈율 (%)"},
        text=[f"{r['이탈율']:.1f}%" for r in df_rows],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>고객 수: %{customdata[0]}명<br>"
            "이탈 고객 수: %{customdata[1]}명<br>이탈율: %{y:.1f}%<extra></extra>"
        ),
    )
    fig.update_layout(showlegend=False, yaxis_range=[0, max(r["이탈율"] for r in df_rows) * 1.3])
    return fig


# ---------------------------------------------------------------------------
# ② 채널·만족도로 본 이탈
# ---------------------------------------------------------------------------
def build_chart_2(consultations, satisfaction):
    merged = satisfaction.merge(
        consultations[["consult_id", "channel", "is_recontact"]], on="consult_id", how="inner"
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
            hovertemplate="<b>%{x}</b><br>CSAT 평균: %{y:.2f}<br>재문의율: %{customdata[0]:.1f}%<extra></extra>",
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
            hovertemplate="<b>%{x}</b><br>재문의율: %{y:.1f}%<br>CSAT 평균: %{customdata[0]:.2f}<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_layout(title="채널별 CSAT 평균 vs 재문의율 (CSAT 낮은 순)", xaxis_title="채널", hovermode="x unified")
    fig.update_yaxes(title_text="CSAT 평균", secondary_y=False)
    fig.update_yaxes(title_text="재문의율 (%)", secondary_y=True)
    return fig


# ---------------------------------------------------------------------------
# ③ 재문의 반복으로 본 이탈
# ---------------------------------------------------------------------------
def build_chart_3(consultations, customers):
    def bucket_label(count):
        if count == 0:
            return "0회"
        if count == 1:
            return "1회"
        return "2회 이상"

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
        color_discrete_map={"0회": "#2a78d6", "1회": "#2a78d6", "2회 이상": "#d03b3b"},
        custom_data=["customer_count", "churned_count"],
        text=summary["churn_rate"].map(lambda v: f"{v:.1f}%"),
        title="재문의 횟수 구간별 이탈율",
        labels={"bucket": "재문의 횟수", "churn_rate": "이탈율 (%)"},
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>고객 수: %{customdata[0]}명<br>"
            "이탈 고객 수: %{customdata[1]}명<br>이탈율: %{y:.1f}%<extra></extra>"
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
    return fig


# ---------------------------------------------------------------------------
# ④ 요금제로 본 이탈
# ---------------------------------------------------------------------------
def build_chart_4(customers):
    highlight_plan = "베이직"
    summary = (
        customers.groupby("plan")
        .agg(customer_count=("customer_id", "count"), churned_count=("churn_yn", lambda s: (s == "Y").sum()))
        .reset_index()
    )
    summary["churn_rate"] = summary["churned_count"] / summary["customer_count"] * 100
    color_map = {plan: ("#d03b3b" if plan == highlight_plan else "#2a78d6") for plan in summary["plan"]}

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
            "<b>%{x}</b><br>고객 수: %{customdata[0]}명<br>"
            "이탈 고객 수: %{customdata[1]}명<br>이탈율: %{y:.1f}%<extra></extra>"
        ),
    )
    fig.update_layout(showlegend=False, yaxis_range=[0, summary["churn_rate"].max() * 1.3])
    return fig


# ---------------------------------------------------------------------------
# ⑤ 지역으로 본 이탈
# ---------------------------------------------------------------------------
def build_chart_5(customers):
    highlight_regions = {"부산", "대구"}
    caption_region = "인천"

    summary = (
        customers.groupby("region")
        .agg(customer_count=("customer_id", "count"), churned_count=("churn_yn", lambda s: (s == "Y").sum()))
        .reset_index()
    )
    summary["churn_rate"] = summary["churned_count"] / summary["customer_count"] * 100
    color_map = {
        region: ("#d03b3b" if region in highlight_regions else "#2a78d6") for region in summary["region"]
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
            "<b>%{x}</b><br>고객 수: %{customdata[0]}명<br>"
            "이탈 고객 수: %{customdata[1]}명<br>이탈율: %{y:.1f}%<extra></extra>"
        ),
    )

    caption_row = summary[summary["region"] == caption_region].iloc[0]
    caption_text = (
        f"* {caption_region}은 표본이 {int(caption_row['customer_count'])}건이지만 "
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
    return fig


# ---------------------------------------------------------------------------
# ⑥ 가입기간·이용량으로 본 이탈
# ---------------------------------------------------------------------------
def build_chart_6(customers, usage_history):
    customers = customers.copy()
    customers["join_date"] = pd.to_datetime(customers["join_date"])
    customers["tenure_months"] = (
        (REFERENCE_DATE.to_period("M") - customers["join_date"].dt.to_period("M")).apply(lambda o: o.n)
    )
    avg_usage = usage_history.groupby("customer_id")["data_gb"].mean().rename("avg_data_gb")
    merged = customers.merge(avg_usage, on="customer_id", how="inner")

    fig = px.scatter(
        merged,
        x="tenure_months",
        y="avg_data_gb",
        color="churn_yn",
        color_discrete_map={"N": "#2a78d6", "Y": "#d03b3b"},
        custom_data=["customer_id", "tenure_months", "avg_data_gb", "churn_yn"],
        title="가입기간 vs 평균 데이터 사용량 (이탈 여부별)",
        labels={"tenure_months": "가입기간 (개월)", "avg_data_gb": "평균 데이터 사용량 (GB)", "churn_yn": "이탈 여부"},
    )
    fig.update_traces(
        marker=dict(size=8, opacity=0.75),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>가입기간: %{customdata[1]}개월<br>"
            "평균 데이터 사용량: %{customdata[2]:.2f}GB<br>이탈 여부: %{customdata[3]}<extra></extra>"
        ),
    )
    return fig


TEAM_ORDER = ["1팀", "2팀", "3팀"]


def calc_enps(scores):
    total = len(scores)
    if total == 0:
        return 0.0
    promoters = (scores >= 9).sum()
    detractors = (scores <= 6).sum()
    return (promoters - detractors) / total * 100


# ---------------------------------------------------------------------------
# 07 직원만족도 eNPS 스코어카드 (BigQuery, 팀 필터)
# ---------------------------------------------------------------------------
def build_chart_enps(enps_df, team):
    scope_df = enps_df if team == "전체" else enps_df[enps_df["team"] == team]
    scope_enps = calc_enps(scope_df["agent_satisfaction"])
    gauge_color = "#d03b3b" if scope_enps < 0 else "#0ca30c"

    fig = go.Figure()
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=scope_enps,
            number={"font": {"size": 48}},
            title={"text": f"eNPS — {team}", "font": {"size": 20}},
            domain={"x": [0, 0.55], "y": [0, 1]},
            gauge={
                "axis": {"range": [-100, 100], "tickwidth": 1},
                "bar": {"color": gauge_color},
                "steps": [
                    {"range": [-100, 0], "color": "#f6d6d5"},
                    {"range": [0, 100], "color": "#e1e0d9"},
                ],
                "threshold": {"line": {"color": "#0b0b0b", "width": 2}, "thickness": 0.8, "value": scope_enps},
            },
        )
    )

    card_width = 0.12
    card_gap = 0.02
    start_x = 0.6
    for i, t in enumerate(TEAM_ORDER):
        value = calc_enps(enps_df.loc[enps_df["team"] == t, "agent_satisfaction"])
        x0 = start_x + i * (card_width + card_gap)
        x1 = x0 + card_width
        is_selected = team == t
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=value,
                number={
                    "font": {
                        "size": 34 if is_selected else 26,
                        "color": "#d03b3b" if value < 0 else "#0ca30c",
                    },
                },
                title={"text": f"{t} eNPS" + (" ✓" if is_selected else ""), "font": {"size": 16}},
                domain={"x": [x0, x1], "y": [0.35, 0.65]},
            )
        )

    fig.update_layout(height=350, margin=dict(t=80, b=20, l=20, r=20))
    return fig


# ---------------------------------------------------------------------------
# 08 팀별 번아웃×CSAT 산점도 (BigQuery, 팀 필터)
# ---------------------------------------------------------------------------
def build_chart_burnout(burnout_df, team):
    df = burnout_df if team == "전체" else burnout_df[burnout_df["team"] == team]

    corr = df["overtime_hours_avg"].corr(df["csat_avg"]) if len(df) >= 2 else float("nan")

    fig = px.scatter(
        df,
        x="overtime_hours_avg",
        y="csat_avg",
        trendline="ols" if len(df) >= 2 else None,
        custom_data=["agent_id", "overtime_hours_avg", "csat_avg"],
        title=f"번아웃(초과근무 시간)과 CSAT 평균의 관계 — {team}",
        labels={"overtime_hours_avg": "월평균 초과근무 시간", "csat_avg": "CSAT 평균"},
    )
    fig.update_traces(
        selector=dict(mode="markers"),
        marker=dict(size=10, color="#2a78d6", opacity=0.8),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>초과근무 시간: %{customdata[1]}시간<br>"
            "CSAT 평균: %{customdata[2]:.2f}<extra></extra>"
        ),
    )
    fig.update_traces(selector=dict(mode="lines"), line=dict(color="#d03b3b", width=2))

    if corr == corr:  # not NaN
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.98,
            y=0.98,
            text=f"r = {corr:.2f}",
            showarrow=False,
            font=dict(size=16, color="#0b0b0b"),
        )
    return fig


# ---------------------------------------------------------------------------
# 09 교육이수 비교 — CSAT·재문의율 (BigQuery, 팀 필터)
# ---------------------------------------------------------------------------
def build_chart_training(training_csat_df, training_recontact_df, team):
    csat_df = training_csat_df if team == "전체" else training_csat_df[training_csat_df["team"] == team]
    recontact_df = (
        training_recontact_df if team == "전체" else training_recontact_df[training_recontact_df["team"] == team]
    )

    csat_by_training = csat_df.groupby("training_completed_yn")["csat"].mean().reindex([True, False])
    recontact_by_training = (
        recontact_df.groupby("training_completed_yn")["is_recontact"].mean().reindex([True, False]) * 100
    )

    labels = ["Y", "N"]
    csat_values = csat_by_training.fillna(0).tolist()
    recontact_values = recontact_by_training.fillna(0).tolist()
    colors = ["#2a78d6", "#898781"]

    fig = make_subplots(rows=1, cols=2, subplot_titles=["CSAT 평균", "재문의율 평균"])
    fig.add_trace(
        go.Bar(
            x=labels,
            y=csat_values,
            marker_color=colors,
            text=[f"{v:.2f}" for v in csat_values],
            textposition="outside",
            hovertemplate="교육이수: %{x}<br>CSAT 평균: %{y:.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=recontact_values,
            marker_color=colors,
            text=[f"{v:.1f}%" for v in recontact_values],
            textposition="outside",
            hovertemplate="교육이수: %{x}<br>재문의율: %{y:.1f}%<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.update_xaxes(title_text="교육 이수 여부", row=1, col=1)
    fig.update_xaxes(title_text="교육 이수 여부", row=1, col=2)
    fig.update_yaxes(title_text="CSAT 평균", range=[0, max(csat_values + [1]) * 1.3], row=1, col=1)
    fig.update_yaxes(title_text="재문의율 (%)", range=[0, max(recontact_values + [1]) * 1.3], row=1, col=2)
    fig.update_layout(
        title=f"교육 이수 여부에 따른 CSAT 평균 및 재문의율 비교 — {team}",
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# 앱 본문
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="고객은 왜 이탈하는가", layout="wide")

    data = load_all()
    customers = data["customers"]
    consultations = data["consultations"]
    satisfaction = data["satisfaction"]
    voc = data["voc"]
    usage_history = data["usage_history"]

    st.title("고객은 왜 이탈하는가 — 이탈 원인 진단 대시보드")
    st.caption("데이터 분석 7기_박혜지")

    total, churned, rate = churn_stats(customers)
    col1, col2, col3 = st.columns(3)
    col1.metric("전체 고객 수", f"{total}명")
    col2.metric("이탈 고객 수", f"{churned}명")
    col3.metric("전체 이탈율", f"{rate:.1f}%")

    st.subheader("① VOC로 본 이탈")
    st.plotly_chart(build_chart_1(customers, voc), use_container_width=True)

    st.subheader("② 채널·만족도로 본 이탈")
    st.plotly_chart(build_chart_2(consultations, satisfaction), use_container_width=True)

    st.subheader("③ 재문의 반복으로 본 이탈")
    st.plotly_chart(build_chart_3(consultations, customers), use_container_width=True)

    st.subheader("④ 요금제로 본 이탈")
    st.plotly_chart(build_chart_4(customers), use_container_width=True)

    st.subheader("⑤ 지역으로 본 이탈")
    st.plotly_chart(build_chart_5(customers), use_container_width=True)

    st.subheader("⑥ 가입기간·이용량으로 본 이탈")
    st.plotly_chart(build_chart_6(customers, usage_history), use_container_width=True)

    st.subheader("상담원 관점: 직원만족도와 고객 경험")
    enps_df = load_agent_enps_bq()
    burnout_df = load_burnout_csat_bq()
    training_csat_df = load_training_csat_bq()
    training_recontact_df = load_training_recontact_bq()

    team_options = ["전체"] + TEAM_ORDER
    selected_team = st.selectbox("팀 선택", team_options)

    st.plotly_chart(build_chart_enps(enps_df, selected_team), use_container_width=True)
    st.plotly_chart(build_chart_burnout(burnout_df, selected_team), use_container_width=True)
    st.plotly_chart(
        build_chart_training(training_csat_df, training_recontact_df, selected_team), use_container_width=True
    )


if __name__ == "__main__":
    main()
