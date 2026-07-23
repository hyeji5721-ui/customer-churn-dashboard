import plotly.graph_objects as go
from google.cloud import bigquery
from plotly.subplots import make_subplots

PROJECT = "project-6fcaf3a6-ee2b-4616-8de"
DATASET = "data"

COLOR_Y = "#2a78d6"
COLOR_N = "#898781"


def load_csat_by_training():
    client = bigquery.Client(project=PROJECT)
    query = f"""
        SELECT
            a.training_completed_yn AS training_completed_yn,
            AVG(s.csat) AS csat_avg,
            COUNT(*) AS n
        FROM `{DATASET}.data_agents` AS a
        JOIN `{DATASET}.data_consultations` AS c ON a.agent_id = c.agent_id
        JOIN `{DATASET}.data_satisfaction` AS s ON c.consult_id = s.consult_id
        GROUP BY a.training_completed_yn
    """
    return {row["training_completed_yn"]: row for row in client.query(query).result()}


def load_recontact_by_training():
    client = bigquery.Client(project=PROJECT)
    query = f"""
        SELECT
            a.training_completed_yn AS training_completed_yn,
            AVG(CASE WHEN c.is_recontact THEN 1.0 ELSE 0.0 END) * 100 AS recontact_rate,
            COUNT(*) AS n
        FROM `{DATASET}.data_agents` AS a
        JOIN `{DATASET}.data_consultations` AS c ON a.agent_id = c.agent_id
        GROUP BY a.training_completed_yn
    """
    return {row["training_completed_yn"]: row for row in client.query(query).result()}


def main():
    csat_by_training = load_csat_by_training()
    recontact_by_training = load_recontact_by_training()

    labels = ["Y", "N"]
    keys = [True, False]
    colors = [COLOR_Y, COLOR_N]

    csat_values = [csat_by_training[k]["csat_avg"] for k in keys]
    recontact_values = [recontact_by_training[k]["recontact_rate"] for k in keys]

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
    fig.update_yaxes(title_text="CSAT 평균", range=[0, max(csat_values) * 1.3], row=1, col=1)
    fig.update_yaxes(title_text="재문의율 (%)", range=[0, max(recontact_values) * 1.3], row=1, col=2)

    fig.update_layout(
        title="교육 이수 여부에 따른 CSAT 평균 및 재문의율 비교",
        showlegend=False,
    )

    fig.show()


if __name__ == "__main__":
    main()
