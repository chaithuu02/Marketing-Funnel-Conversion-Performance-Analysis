"""
Marketing Funnel & Conversion Performance Analysis — Standalone Script

Loads the synthetic dataset, performs full analysis (cleaning, KPI calculation,
channel comparison, drop-off analysis), prints summary tables, and saves
publication-quality charts to the screenshots/ directory.
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(ROOT, "dataset", "marketing_data.csv")
SCREENSHOTS = os.path.join(ROOT, "screenshots")
os.makedirs(SCREENSHOTS, exist_ok=True)

# ── Style ────────────────────────────────────────────────────────────────────
COLORS = {
    "Google Ads":       "#4285F4",
    "Facebook Ads":     "#1877F2",
    "Instagram":        "#E4405F",
    "Email Marketing":  "#FFB900",
    "Organic Search":   "#34A853",
}
FUNNEL_COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"]
BG_COLOR = "#0f172a"
CARD_COLOR = "#1e293b"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "#334155"

plt.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": CARD_COLOR,
    "axes.edgecolor": GRID_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "text.color": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "grid.color": GRID_COLOR,
    "grid.alpha": 0.3,
    "font.family": "sans-serif",
    "font.size": 11,
})


# ═══════════════════════════════════════════════════════════════════════════
# 1. LOAD & CLEAN
# ═══════════════════════════════════════════════════════════════════════════
def load_and_clean(path: str) -> pd.DataFrame:
    """Load CSV, clean, and return a ready-to-analyze DataFrame."""
    df = pd.read_csv(path)

    # Remove duplicates
    before = len(df)
    df.drop_duplicates(inplace=True)
    dupes = before - len(df)

    # Handle missing values
    missing = df.isnull().sum().sum()
    df.fillna(0, inplace=True)

    # Fix data types
    df["Date"] = pd.to_datetime(df["Date"])
    for col in ["Impressions", "Clicks", "Leads", "Signups", "Customers"]:
        df[col] = df[col].astype(int)
    df["Campaign_Cost"] = df["Campaign_Cost"].astype(float)

    # Standardize channel names
    df["Marketing_Channel"] = df["Marketing_Channel"].str.strip().str.title()

    # Validate: ensure no negatives
    num_cols = ["Impressions", "Clicks", "Leads", "Signups", "Customers", "Campaign_Cost"]
    for col in num_cols:
        df[col] = df[col].clip(lower=0)

    print("=" * 60)
    print("  DATA CLEANING REPORT")
    print("=" * 60)
    print(f"  Rows loaded       : {before}")
    print(f"  Duplicates removed : {dupes}")
    print(f"  Missing filled     : {missing}")
    print(f"  Final shape        : {df.shape}")
    print("=" * 60)

    return df


# ═══════════════════════════════════════════════════════════════════════════
# 2. KPI CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════
def calculate_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate per-channel KPIs."""
    agg = df.groupby("Marketing_Channel").agg(
        Impressions=("Impressions", "sum"),
        Clicks=("Clicks", "sum"),
        Leads=("Leads", "sum"),
        Signups=("Signups", "sum"),
        Customers=("Customers", "sum"),
        Campaign_Cost=("Campaign_Cost", "sum"),
    )

    agg["CTR (%)"] = (agg["Clicks"] / agg["Impressions"] * 100).round(2)
    agg["Lead Conv (%)"] = (agg["Leads"] / agg["Clicks"] * 100).round(2)
    agg["Signup Conv (%)"] = (agg["Signups"] / agg["Leads"] * 100).round(2)
    agg["Customer Conv (%)"] = (agg["Customers"] / agg["Signups"] * 100).round(2)
    agg["CPA ($)"] = (agg["Campaign_Cost"] / agg["Customers"]).round(2)
    agg["Overall Conv (%)"] = (agg["Customers"] / agg["Impressions"] * 100).round(4)

    return agg


# ═══════════════════════════════════════════════════════════════════════════
# 3. FUNNEL DROP-OFF
# ═══════════════════════════════════════════════════════════════════════════
def funnel_dropoff(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate overall funnel drop-off between stages."""
    stages = ["Impressions", "Clicks", "Leads", "Signups", "Customers"]
    totals = {s: df[s].sum() for s in stages}

    rows = []
    for i in range(len(stages) - 1):
        from_stage = stages[i]
        to_stage = stages[i + 1]
        from_val = totals[from_stage]
        to_val = totals[to_stage]
        drop = from_val - to_val
        drop_pct = (drop / from_val * 100) if from_val else 0
        conv_pct = (to_val / from_val * 100) if from_val else 0
        rows.append({
            "From": from_stage,
            "To": to_stage,
            "From_Count": from_val,
            "To_Count": to_val,
            "Drop": drop,
            "Drop_Rate (%)": round(drop_pct, 2),
            "Conv_Rate (%)": round(conv_pct, 2),
        })

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════
# 4. VISUALIZATIONS
# ═══════════════════════════════════════════════════════════════════════════

def chart_funnel(df: pd.DataFrame):
    """Horizontal funnel bar chart."""
    stages = ["Impressions", "Clicks", "Leads", "Signups", "Customers"]
    values = [df[s].sum() for s in stages]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(stages[::-1], values[::-1], color=FUNNEL_COLORS, edgecolor="none",
                   height=0.6)

    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va="center", fontsize=12, fontweight="bold", color=TEXT_COLOR)

    ax.set_title("Marketing Funnel Overview", fontsize=18, fontweight="bold", pad=20)
    ax.set_xlabel("Count", fontsize=13)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(axis="x", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(SCREENSHOTS, "funnel_overview.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [OK] Saved funnel_overview.png")


def chart_channel_comparison(kpis: pd.DataFrame):
    """Grouped bar chart comparing channels on key metrics."""
    metrics = ["CTR (%)", "Lead Conv (%)", "Signup Conv (%)", "Customer Conv (%)"]
    channels = kpis.index.tolist()
    x = np.arange(len(channels))
    width = 0.18

    fig, ax = plt.subplots(figsize=(14, 7))
    metric_colors = ["#6366f1", "#f43f5e", "#10b981", "#f59e0b"]

    for i, metric in enumerate(metrics):
        vals = kpis[metric].values
        ax.bar(x + i * width, vals, width, label=metric, color=metric_colors[i],
               edgecolor="none", alpha=0.9)

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(channels, fontsize=11)
    ax.set_ylabel("Rate (%)", fontsize=13)
    ax.set_title("Conversion Rates by Channel", fontsize=18, fontweight="bold", pad=20)
    ax.legend(loc="upper right", framealpha=0.8, fontsize=10)
    ax.grid(axis="y", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(SCREENSHOTS, "channel_comparison.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [OK] Saved channel_comparison.png")


def chart_monthly_trend(df: pd.DataFrame):
    """Monthly conversion trend — line chart per channel."""
    df_m = df.copy()
    df_m["Month"] = df_m["Date"].dt.strftime("%b")
    df_m["Conv_Rate"] = (df_m["Customers"] / df_m["Impressions"] * 100)

    fig, ax = plt.subplots(figsize=(13, 6))
    for ch in df_m["Marketing_Channel"].unique():
        sub = df_m[df_m["Marketing_Channel"] == ch]
        ax.plot(sub["Month"], sub["Conv_Rate"], marker="o", linewidth=2.5,
                markersize=7, label=ch, color=COLORS.get(ch, "#888"))

    ax.set_title("Monthly Conversion Trend (Impressions → Customers)",
                 fontsize=18, fontweight="bold", pad=20)
    ax.set_ylabel("Conversion Rate (%)", fontsize=13)
    ax.set_xlabel("Month", fontsize=13)
    ax.legend(loc="upper left", framealpha=0.8, fontsize=10)
    ax.grid(axis="both", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(SCREENSHOTS, "monthly_trend.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [OK] Saved monthly_trend.png")


def chart_cpa(kpis: pd.DataFrame):
    """CPA by channel — horizontal bar chart."""
    sorted_kpis = kpis.sort_values("CPA ($)")
    channels = sorted_kpis.index.tolist()
    cpa_vals = sorted_kpis["CPA ($)"].values
    colors = [COLORS.get(c, "#888") for c in channels]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(channels, cpa_vals, color=colors, edgecolor="none", height=0.55)

    for bar, val in zip(bars, cpa_vals):
        ax.text(bar.get_width() + max(cpa_vals) * 0.02, bar.get_y() + bar.get_height() / 2,
                f"${val:,.2f}", va="center", fontsize=12, fontweight="bold", color=TEXT_COLOR)

    ax.set_title("Cost Per Acquisition (CPA) by Channel",
                 fontsize=18, fontweight="bold", pad=20)
    ax.set_xlabel("CPA ($)", fontsize=13)
    ax.grid(axis="x", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(SCREENSHOTS, "cpa_by_channel.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [OK] Saved cpa_by_channel.png")


def chart_dropoff(dropoff_df: pd.DataFrame):
    """Drop-off analysis bar chart."""
    labels = [f"{r['From']} → {r['To']}" for _, r in dropoff_df.iterrows()]
    drop_rates = dropoff_df["Drop_Rate (%)"].values
    conv_rates = dropoff_df["Conv_Rate (%)"].values

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(labels))
    width = 0.35

    ax.bar(x - width / 2, conv_rates, width, label="Conversion %",
           color="#10b981", edgecolor="none", alpha=0.9)
    ax.bar(x + width / 2, drop_rates, width, label="Drop-off %",
           color="#f43f5e", edgecolor="none", alpha=0.9)

    for i, (c, d) in enumerate(zip(conv_rates, drop_rates)):
        ax.text(i - width / 2, c + 1, f"{c:.1f}%", ha="center", fontsize=10,
                fontweight="bold", color="#10b981")
        ax.text(i + width / 2, d + 1, f"{d:.1f}%", ha="center", fontsize=10,
                fontweight="bold", color="#f43f5e")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Percentage (%)", fontsize=13)
    ax.set_title("Funnel Drop-off Analysis", fontsize=18, fontweight="bold", pad=20)
    ax.legend(loc="upper right", framealpha=0.8, fontsize=11)
    ax.grid(axis="y", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(SCREENSHOTS, "dropoff_analysis.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [OK] Saved dropoff_analysis.png")


def chart_heatmap(df: pd.DataFrame):
    """Heatmap of overall conversion rate by channel and month."""
    df_m = df.copy()
    df_m["Month"] = df_m["Date"].dt.strftime("%b")
    df_m["Conv_Rate"] = (df_m["Customers"] / df_m["Impressions"] * 100).round(3)
    pivot = df_m.pivot_table(index="Marketing_Channel", columns="Month",
                             values="Conv_Rate",
                             aggfunc="mean")

    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pivot = pivot[[m for m in month_order if m in pivot.columns]]

    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn")

    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=11)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=11)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:.2f}%", ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color="black" if val > pivot.values.mean() else "white")

    ax.set_title("Conversion Rate Heatmap (Channel × Month)",
                 fontsize=18, fontweight="bold", pad=20)
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Conversion Rate (%)", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(SCREENSHOTS, "heatmap.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [OK] Saved heatmap.png")


# ═══════════════════════════════════════════════════════════════════════════
# 5. BUSINESS INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════
def print_insights(kpis: pd.DataFrame, dropoff_df: pd.DataFrame):
    """Print key business insights derived from the analysis."""
    print("\n" + "=" * 60)
    print("  BUSINESS INSIGHTS")
    print("=" * 60)

    # Best conversion channel
    best_conv = kpis["Overall Conv (%)"].idxmax()
    best_conv_val = kpis.loc[best_conv, "Overall Conv (%)"]
    print(f"\n  [BEST] Highest overall conversion: {best_conv} ({best_conv_val:.3f}%)")

    # Most leads
    most_leads = kpis["Leads"].idxmax()
    print(f"  [TOP]  Most leads generated: {most_leads} ({kpis.loc[most_leads, 'Leads']:,})")

    # Lowest CPA
    lowest_cpa = kpis["CPA ($)"].idxmin()
    print(f"  [LOW]  Lowest CPA: {lowest_cpa} (${kpis.loc[lowest_cpa, 'CPA ($)']:,.2f})")

    # Highest CPA
    highest_cpa = kpis["CPA ($)"].idxmax()
    print(f"  [HIGH] Highest CPA: {highest_cpa} (${kpis.loc[highest_cpa, 'CPA ($)']:,.2f})")

    # Biggest drop-off
    worst_drop_idx = dropoff_df["Drop_Rate (%)"].idxmax()
    worst = dropoff_df.loc[worst_drop_idx]
    print(f"  [WARN] Biggest drop-off: {worst['From']} -> {worst['To']} "
          f"({worst['Drop_Rate (%)']:.1f}% loss)")

    # Most cost-effective
    kpis_temp = kpis.copy()
    kpis_temp["ROI_proxy"] = kpis_temp["Customers"] / kpis_temp["Campaign_Cost"]
    best_roi = kpis_temp["ROI_proxy"].idxmax()
    print(f"  [BEST] Most cost-effective channel: {best_roi}")

    print("\n" + "=" * 60)
    print("  RECOMMENDATIONS")
    print("=" * 60)
    print(f"""
  1. Increase budget allocation to {best_conv} -- it has the highest
     end-to-end conversion rate.

  2. Optimize the {worst['From']} -> {worst['To']} stage -- {worst['Drop_Rate (%)']:.1f}%
     of potential customers are lost here. Consider:
     - Simplifying signup forms
     - Adding progress indicators
     - A/B testing landing pages

  3. Reduce spend on {highest_cpa} or improve its funnel --
     it has the highest CPA (${kpis.loc[highest_cpa, 'CPA ($)']:,.2f}).

  4. Scale {lowest_cpa} campaigns -- lowest CPA at
     ${kpis.loc[lowest_cpa, 'CPA ($)']:,.2f} per customer.

  5. Run retargeting campaigns for leads that didn't sign up
     (especially from {most_leads}).

  6. Monitor seasonal trends -- Q4 shows the strongest performance,
     plan major campaigns accordingly.
""")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Dataset not found at {DATA_PATH}")
        print("   Run generate_dataset.py first.")
        sys.exit(1)

    # 1. Load & clean
    df = load_and_clean(DATA_PATH)

    # 2. KPIs
    kpis = calculate_kpis(df)
    print("\n" + "=" * 60)
    print("  KPI SUMMARY BY CHANNEL")
    print("=" * 60)
    display_cols = ["Impressions", "Clicks", "Leads", "Signups", "Customers",
                    "CTR (%)", "Lead Conv (%)", "Signup Conv (%)",
                    "Customer Conv (%)", "CPA ($)"]
    print(kpis[display_cols].to_string())

    # 3. Drop-off
    dropoff_df = funnel_dropoff(df)
    print("\n" + "=" * 60)
    print("  FUNNEL DROP-OFF ANALYSIS")
    print("=" * 60)
    print(dropoff_df.to_string(index=False))

    # 4. Charts
    print("\n  Generating charts...")
    chart_funnel(df)
    chart_channel_comparison(kpis)
    chart_monthly_trend(df)
    chart_cpa(kpis)
    chart_dropoff(dropoff_df)
    chart_heatmap(df)

    # 5. Insights
    print_insights(kpis, dropoff_df)

    print("[OK] Analysis complete. Charts saved to screenshots/\n")


if __name__ == "__main__":
    main()
