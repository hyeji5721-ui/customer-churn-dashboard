import csv
import os

import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "charts", "output")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8-sig") as fp:
        return list(csv.DictReader(fp))


def churn_rate(customers):
    total = len(customers)
    churned = sum(1 for r in customers if r["churn_yn"].strip().upper() == "Y")
    return churned / total * 100 if total else 0.0


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

    overall_rate = churn_rate(customers)
    voc_rate = churn_rate(voc_customers)

    labels = ["전체 고객", "해지관련 부정 VOC 이력 있음"]
    values = [overall_rate, voc_rate]
    colors = ["#2a78d6", "#d03b3b"]

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(labels, values, color=colors, width=0.5)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.6,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=13,
            fontweight="bold",
            color="#0b0b0b",
        )

    ax.set_ylabel("이탈율 (%)")
    ax.set_title("전체 고객 vs 해지관련 부정 VOC 고객 이탈율 비교")
    ax.set_ylim(0, max(values) * 1.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e1e0d9", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    fig.tight_layout()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "01_matplotlib_voc이탈비교.png")
    fig.savefig(output_path, dpi=150)
    print(f"저장 완료: {output_path}")


if __name__ == "__main__":
    main()
