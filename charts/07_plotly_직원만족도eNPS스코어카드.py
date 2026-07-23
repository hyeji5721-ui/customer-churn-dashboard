import plotly.graph_objects as go
from google.cloud import bigquery

PROJECT = "project-6fcaf3a6-ee2b-4616-8de"
DATASET = "data"
TABLE = "data_agents"

TEAM_ORDER = ["1팀", "2팀", "3팀"]


def load_agent_satisfaction():
    client = bigquery.Client(project=PROJECT)
    query = f"""
        SELECT team, agent_satisfaction
        FROM `{DATASET}.{TABLE}`
        WHERE agent_satisfaction IS NOT NULL
    """
    return list(client.query(query).result())


def calc_enps(scores):
    total = len(scores)
    if total == 0:
        return 0.0
    promoters = sum(1 for s in scores if s >= 9)
    detractors = sum(1 for s in scores if s <= 6)
    return (promoters - detractors) / total * 100


def main():
    rows = load_agent_satisfaction()

    all_scores = [r["agent_satisfaction"] for r in rows]
    overall_enps = calc_enps(all_scores)

    team_scores = {team: [] for team in TEAM_ORDER}
    for r in rows:
        if r["team"] in team_scores:
            team_scores[r["team"]].append(r["agent_satisfaction"])
    team_enps = {team: calc_enps(scores) for team, scores in team_scores.items()}

    gauge_color = "#d03b3b" if overall_enps < 0 else "#0ca30c"

    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=overall_enps,
            number={"suffix": "", "font": {"size": 48}},
            title={"text": "전체 eNPS", "font": {"size": 20}},
            domain={"x": [0, 0.55], "y": [0, 1]},
            gauge={
                "axis": {"range": [-100, 100], "tickwidth": 1},
                "bar": {"color": gauge_color},
                "steps": [
                    {"range": [-100, 0], "color": "#f6d6d5"},
                    {"range": [0, 100], "color": "#e1e0d9"},
                ],
                "threshold": {
                    "line": {"color": "#0b0b0b", "width": 2},
                    "thickness": 0.8,
                    "value": overall_enps,
                },
            },
        )
    )

    card_width = 0.12
    card_gap = 0.02
    start_x = 0.6
    for i, team in enumerate(TEAM_ORDER):
        value = team_enps[team]
        x0 = start_x + i * (card_width + card_gap)
        x1 = x0 + card_width
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=value,
                number={
                    "font": {"size": 32, "color": "#d03b3b" if value < 0 else "#0ca30c"},
                },
                title={"text": f"{team} eNPS", "font": {"size": 16}},
                domain={"x": [x0, x1], "y": [0.35, 0.65]},
            )
        )

    fig.update_layout(
        title="직원만족도 eNPS 스코어카드",
        height=450,
        margin=dict(t=80, b=40, l=20, r=20),
    )

    fig.show()


if __name__ == "__main__":
    main()
