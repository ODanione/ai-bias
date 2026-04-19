#!/usr/bin/env python3
"""Generate publication figures from statistics.json."""

import json
from collections import Counter, OrderedDict
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

STATS_FILE = Path(__file__).parent.parent / "statistics.json"
OUT_DIR = Path(__file__).parent / "figures"
OUT_DIR.mkdir(exist_ok=True)

SOURCE_ORDER = ["GoogleSearch", "AdobeStock", "FLUX", "FLUX2", "NanoBanana", "Qwen", "Sora"]
SOURCE_LABELS = {
    "GoogleSearch": "Google\nSearch",
    "AdobeStock": "Adobe\nStock",
    "FLUX": "FLUX",
    "FLUX2": "FLUX 2",
    "NanoBanana": "Nano\nBanana",
    "Qwen": "Qwen",
    "Sora": "Sora",
}
REFERENCE_SOURCES = {"GoogleSearch", "AdobeStock"}

PALETTE = {
    # Gender
    "female": "#e07b8e",
    "male": "#5b8db8",
    "unknown": "#c0c0c0",
    # Ancestry
    "West Eurasian": "#4e79a7",
    "Sub-Saharan African": "#f28e2b",
    "East Asian": "#59a14f",
    "South Asian": "#e15759",
    "Other": "#bab0ac",
    # Skin tone
    "light": "#f5cba7",
    "medium": "#d4a76a",
    "brown": "#9e6b3e",
    "dark": "#4a2c0a",
    # Age buckets (sequential, light → dark)
    "0–14": "#c6dbef",
    "15–29": "#6baed6",
    "30–44": "#2171b5",
    "45–59": "#08519c",
    "60+": "#08306b",
}

# Real-world baselines (UN WPP 2024 / World Bank)
WORLD_GENDER = {"female": 0.497, "male": 0.503, "unknown": 0.0}

# Ancestry mapped to chart categories:
# East Asian ~30% (E+SE Asia), South Asian ~25%, West Eurasian ~20%,
# Sub-Saharan African ~15%, Other (Americas + rest) ~10%
WORLD_ANCESTRY = {
    "West Eurasian": 0.20,
    "Sub-Saharan African": 0.15,
    "East Asian": 0.30,
    "South Asian": 0.25,
    "Other": 0.10,
}

# Age bucket baseline (UN WPP 2024)
WORLD_AGE = {
    "0–14":  0.25,
    "15–29": 0.24,
    "30–44": 0.21,
    "45–59": 0.17,
    "60+":   0.13,
}
AGE_BUCKETS = list(WORLD_AGE.keys())
AGE_EDGES = [0, 15, 30, 45, 60, 999]

WORLD_POP = OrderedDict([
    ("South/Southeast\n& East Asian", 0.55),
    ("Sub-Saharan\nAfrican", 0.15),
    ("West Eurasian\n/ Europe / MENA", 0.20),
    ("Americas", 0.08),
    ("Other", 0.02),
])


def load_data():
    with open(STATS_FILE, encoding="utf-8") as f:
        return json.load(f)


def stacked_bar(ax, sources, categories, data_matrix, colors, title,
                world_baseline=None, ylabel="%"):
    """
    Draw a stacked bar chart.
    data_matrix: dict[category] -> list of fractions, one per source.
    world_baseline: dict[category] -> fraction; if given, prepends a hatched baseline bar.
    """
    all_sources = (["_world_"] + sources) if world_baseline else sources
    n = len(all_sources)
    x = np.arange(n)
    width = 0.6
    bottom = np.zeros(n)

    for cat in categories:
        source_vals = np.array(data_matrix[cat])
        if world_baseline is not None:
            vals = np.concatenate([[world_baseline.get(cat, 0)], source_vals])
        else:
            vals = source_vals

        bars = ax.bar(x, vals * 100, width, bottom=bottom * 100,
                      label=cat, color=colors.get(cat, "#aaaaaa"))

        # Hatch the world baseline bar
        if world_baseline is not None:
            bars[0].set_hatch("///")
            bars[0].set_edgecolor("white")
            bars[0].set_linewidth(0.5)

        for i, (bar, v) in enumerate(zip(bars, vals)):
            # Skip label on world bar for small segments; use slightly lower threshold
            threshold = 0.05 if (world_baseline and i == 0) else 0.07
            if v > threshold:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{v*100:.0f}%",
                    ha="center", va="center", fontsize=7,
                    color="white", fontweight="bold"
                )
        bottom += vals

    # X-axis labels
    labels = []
    if world_baseline is not None:
        labels.append("World\n(baseline)")
    labels += [SOURCE_LABELS.get(s, s) for s in sources]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)

    # Bold the world baseline tick label
    if world_baseline is not None:
        ax.get_xticklabels()[0].set_fontweight("bold")
        ax.get_xticklabels()[0].set_color("#444444")

    ax.set_title(title, fontsize=11, pad=8)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.spines[["top", "right"]].set_visible(False)

    # Vertical separator after world baseline bar
    if world_baseline is not None:
        ax.axvline(0.5, color="#cccccc", linewidth=1, linestyle="--", zorder=1)

    # Shade internet reference sources
    offset = 1 if world_baseline else 0
    for i, src in enumerate(sources):
        if src in REFERENCE_SOURCES:
            ax.axvspan(i + offset - 0.4, i + offset + 0.4, color="#f0f0f0", zorder=0)

    return ax


def figure_gender(data):
    by_source = {s: Counter() for s in SOURCE_ORDER}
    for rec in data:
        src = rec.get("source")
        if src in by_source:
            by_source[src][rec.get("perceived_gender", "unknown")] += 1

    categories = ["female", "male", "unknown"]
    totals = {s: sum(by_source[s].values()) or 1 for s in SOURCE_ORDER}
    matrix = {cat: [by_source[s][cat] / totals[s] for s in SOURCE_ORDER] for cat in categories}

    fig, ax = plt.subplots(figsize=(9, 4))
    stacked_bar(ax, SOURCE_ORDER, categories, matrix, PALETTE,
                "Perceived gender by source", world_baseline=WORLD_GENDER)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.7)
    _add_reference_note(ax)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "gender_by_source.png", dpi=150)
    plt.close(fig)
    print("Saved gender_by_source.png")


def figure_ancestry(data):
    by_source = {s: Counter() for s in SOURCE_ORDER}
    for rec in data:
        src = rec.get("source")
        if src in by_source:
            val = rec.get("perceived_ancestry_cluster", "Other") or "Other"
            by_source[src][val] += 1

    all_cats = ["West Eurasian", "Sub-Saharan African", "East Asian", "South Asian", "Other"]
    totals = {s: sum(by_source[s].values()) or 1 for s in SOURCE_ORDER}
    matrix = {cat: [by_source[s].get(cat, 0) / totals[s] for s in SOURCE_ORDER] for cat in all_cats}

    fig, ax = plt.subplots(figsize=(9, 4))
    stacked_bar(ax, SOURCE_ORDER, all_cats, matrix, PALETTE,
                "Perceived ancestry cluster by source", world_baseline=WORLD_ANCESTRY)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.7)
    _add_reference_note(ax)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "ancestry_by_source.png", dpi=150)
    plt.close(fig)
    print("Saved ancestry_by_source.png")


def figure_skin_tone(data):
    by_source = {s: Counter() for s in SOURCE_ORDER}
    for rec in data:
        src = rec.get("source")
        if src in by_source:
            by_source[src][rec.get("skin_tone", "unknown")] += 1

    categories = ["light", "medium", "brown", "dark"]
    totals = {s: sum(by_source[s].values()) or 1 for s in SOURCE_ORDER}
    matrix = {cat: [by_source[s].get(cat, 0) / totals[s] for s in SOURCE_ORDER] for cat in categories}

    fig, ax = plt.subplots(figsize=(8, 4))
    # No world baseline for skin tone — no reliable global statistic available
    stacked_bar(ax, SOURCE_ORDER, categories, matrix, PALETTE, "Skin tone by source")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.7)
    _add_reference_note(ax)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "skin_tone_by_source.png", dpi=150)
    plt.close(fig)
    print("Saved skin_tone_by_source.png")


def _age_bucket(age):
    for i, edge in enumerate(AGE_EDGES[1:]):
        if age < edge:
            return AGE_BUCKETS[i]
    return AGE_BUCKETS[-1]


def figure_age(data):
    by_source = {s: Counter() for s in SOURCE_ORDER}
    for rec in data:
        src = rec.get("source")
        age = rec.get("age_estimate")
        if src in by_source and isinstance(age, (int, float)):
            by_source[src][_age_bucket(age)] += 1

    totals = {s: sum(by_source[s].values()) or 1 for s in SOURCE_ORDER}
    matrix = {
        bucket: [by_source[s].get(bucket, 0) / totals[s] for s in SOURCE_ORDER]
        for bucket in AGE_BUCKETS
    }

    fig, ax = plt.subplots(figsize=(9, 4))
    stacked_bar(ax, SOURCE_ORDER, AGE_BUCKETS, matrix, PALETTE,
                "Perceived age distribution by source", world_baseline=WORLD_AGE)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.7)
    _add_reference_note(ax)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "age_by_source.png", dpi=150)
    plt.close(fig)
    print("Saved age_by_source.png")


def figure_world_pop_vs_ai(data):
    """Bar chart comparing world population ancestry shares vs. combined AI output."""
    ai_sources = [s for s in SOURCE_ORDER if s not in REFERENCE_SOURCES]
    ancestry_map = {
        "West Eurasian": "West Eurasian\n/ Europe / MENA",
        "Sub-Saharan African": "Sub-Saharan\nAfrican",
        "East Asian": "South/Southeast\n& East Asian",
        "South Asian": "South/Southeast\n& East Asian",
    }

    ai_counter = Counter()
    for rec in data:
        if rec.get("source") in ai_sources:
            val = rec.get("perceived_ancestry_cluster", "Other") or "Other"
            mapped = ancestry_map.get(val, "Other")
            ai_counter[mapped] += 1

    total_ai = sum(ai_counter.values()) or 1
    categories = list(WORLD_POP.keys())
    world_vals = [WORLD_POP[c] * 100 for c in categories]
    ai_vals = [ai_counter.get(c, 0) / total_ai * 100 for c in categories]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x - width / 2, world_vals, width, label="World population", color="#7fb3d3")
    ax.bar(x + width / 2, ai_vals, width, label="AI-generated (combined)", color="#f0a500")

    ax.set_title("World population vs. AI-generated perceived ancestry", fontsize=11, pad=8)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=8)
    ax.set_ylabel("%", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "world_pop_vs_ai_ancestry.png", dpi=150)
    plt.close(fig)
    print("Saved world_pop_vs_ai_ancestry.png")


def _add_reference_note(ax):
    ax.annotate(
        "Shaded = internet reference sources  ·  Hatched = real-world baseline",
        xy=(0.01, 0.01), xycoords="axes fraction",
        fontsize=7, color="#888888"
    )


def main():
    data = load_data()
    print(f"Loaded {len(data)} records from {STATS_FILE}")
    figure_gender(data)
    figure_ancestry(data)
    figure_skin_tone(data)
    figure_age(data)
    figure_world_pop_vs_ai(data)
    print(f"\nAll figures saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()
