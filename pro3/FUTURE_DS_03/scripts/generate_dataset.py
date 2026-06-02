"""
Generate a realistic synthetic marketing funnel dataset.

Creates ~600 rows spanning 12 months (Jan 2024 – Dec 2024) across 5 marketing
channels, each with distinct conversion profiles and seasonal trends.
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)

# ── Channel profiles ────────────────────────────────────────────────────────
# Each channel has base impressions, CTR, lead_rate, signup_rate, customer_rate,
# and a base monthly cost.
CHANNELS = {
    "Google Ads": {
        "impressions_range": (150_000, 500_000),
        "ctr": 0.045,          # 4.5%
        "lead_rate": 0.12,     # 12%
        "signup_rate": 0.35,   # 35%
        "customer_rate": 0.25, # 25%
        "base_cost": 12_000,
    },
    "Facebook Ads": {
        "impressions_range": (100_000, 350_000),
        "ctr": 0.035,
        "lead_rate": 0.10,
        "signup_rate": 0.30,
        "customer_rate": 0.20,
        "base_cost": 8_500,
    },
    "Instagram": {
        "impressions_range": (80_000, 300_000),
        "ctr": 0.030,
        "lead_rate": 0.08,
        "signup_rate": 0.28,
        "customer_rate": 0.18,
        "base_cost": 6_000,
    },
    "Email Marketing": {
        "impressions_range": (20_000, 80_000),
        "ctr": 0.15,
        "lead_rate": 0.25,
        "signup_rate": 0.50,
        "customer_rate": 0.40,
        "base_cost": 2_000,
    },
    "Organic Search": {
        "impressions_range": (60_000, 250_000),
        "ctr": 0.055,
        "lead_rate": 0.14,
        "signup_rate": 0.38,
        "customer_rate": 0.30,
        "base_cost": 1_500,
    },
}

# Seasonal multipliers (Jan–Dec) — Q4 holiday bump, slight summer dip
SEASONAL = [0.85, 0.88, 0.95, 1.00, 1.02, 0.97,
            0.93, 0.90, 0.98, 1.05, 1.15, 1.25]

MONTHS = pd.date_range("2024-01-01", periods=12, freq="MS")


def add_noise(value: float, noise_pct: float = 0.10) -> int:
    """Add random noise to a value and return a non-negative integer."""
    noisy = value * np.random.uniform(1 - noise_pct, 1 + noise_pct)
    return max(0, int(round(noisy)))


def generate() -> pd.DataFrame:
    """Generate the synthetic marketing funnel dataset."""
    rows = []

    for month_idx, date in enumerate(MONTHS):
        season = SEASONAL[month_idx]

        for channel_name, profile in CHANNELS.items():
            lo, hi = profile["impressions_range"]
            base_impressions = np.random.randint(lo, hi)
            impressions = add_noise(base_impressions * season, 0.08)

            clicks = add_noise(impressions * profile["ctr"], 0.12)
            leads = add_noise(clicks * profile["lead_rate"], 0.15)
            signups = add_noise(leads * profile["signup_rate"], 0.15)
            customers = add_noise(signups * profile["customer_rate"], 0.18)

            cost = round(
                profile["base_cost"] * season * np.random.uniform(0.85, 1.15), 2
            )

            rows.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Marketing_Channel": channel_name,
                "Impressions": impressions,
                "Clicks": clicks,
                "Leads": leads,
                "Signups": signups,
                "Customers": customers,
                "Campaign_Cost": cost,
            })

    df = pd.DataFrame(rows)
    return df


def main():
    df = generate()

    # Ensure output directory exists
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "marketing_data.csv")

    df.to_csv(out_path, index=False)
    print(f"[OK] Dataset saved to {out_path}")
    print(f"   Shape: {df.shape}")
    print(f"   Channels: {df['Marketing_Channel'].nunique()}")
    print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
    print()
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
