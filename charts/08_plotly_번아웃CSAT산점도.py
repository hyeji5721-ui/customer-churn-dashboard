import plotly.express as px
from google.cloud import bigquery

PROJECT = "project-6fcaf3a6-ee2b-4616-8de"
DATASET = "data"


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


def main():
    df = load_agent_burnout_csat()

    corr = df["overtime_hours_avg"].corr(df["csat_avg"])

    fig = px.scatter(
        df,
        x="overtime_hours_avg",
        y="csat_avg",
        trendline="ols",
        custom_data=["agent_id", "overtime_hours_avg", "csat_avg"],
        title="번아웃(초과근무 시간)과 CSAT 평균의 관계",
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

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.98,
        y=0.98,
        text=f"r = {corr:.2f}",
        showarrow=False,
        font=dict(size=16, color="#0b0b0b"),
        align="right",
    )

    fig.show()


if __name__ == "__main__":
    main()
