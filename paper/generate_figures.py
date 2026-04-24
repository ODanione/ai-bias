#!/usr/bin/env python3
"""Generate publication figures from statistics.json using plotnine."""

import json
import warnings
from collections import Counter, OrderedDict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
import matplotlib.font_manager as fm
import matplotlib.lines as mlines
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import pandas as pd
from plotnine import (
    ggplot, aes,
    geom_col, geom_hline, geom_vline, geom_point, geom_text,
    scale_fill_manual, scale_fill_identity, scale_color_identity, scale_alpha_identity,
    scale_y_continuous, scale_x_discrete,
    annotate,
    coord_flip, facet_grid,
    labs, theme, theme_minimal,
    element_text, element_blank, element_rect, element_line,
    position_stack, guides, guide_legend,
)

warnings.filterwarnings("ignore")

# Register Lato and make it the default font
_LATO_DIR = Path("/usr/share/fonts/truetype/lato")
for _ttf in _LATO_DIR.glob("*.ttf"):
    fm.fontManager.addfont(str(_ttf))
_FONT = "Lato"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
STATS_FILE  = Path(__file__).parent.parent / "statistics.json"
OUT_DIR     = Path(__file__).parent / "figures"
LI_DIR      = OUT_DIR / "linkedin"
OUT_DIR.mkdir(exist_ok=True)
LI_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Source ordering & labels
# ---------------------------------------------------------------------------
SOURCE_ORDER = ["GoogleSearch", "AdobeStock", "FLUX", "FLUX2", "NanoBanana", "Qwen", "DALL-E", "GPTImages2"]
SOURCE_LABELS = {
    "GoogleSearch": "Google\nSearch",
    "AdobeStock":   "Adobe\nStock",
    "FLUX":         "FLUX",
    "FLUX2":        "FLUX 2",
    "NanoBanana":   "Nano\nBanana",
    "Qwen":         "Qwen",
    "DALL-E":       "DALL-E",
    "GPTImages2":   "GPT\nImages 2",
}
REFERENCE_SOURCES = {"GoogleSearch", "AdobeStock"}
BASELINE_LABEL    = "World\nbaseline"

# ---------------------------------------------------------------------------
# Cohesive color palette
# ---------------------------------------------------------------------------
PALETTE = {
    # Gender
    "female":              "#C7486A",
    "male":                "#2E72B8",
    "unknown":             "#BBBBBB",
    # Ancestry
    "West Eurasian":       "#2E72B8",
    "Sub-Saharan African": "#E07B2A",
    "Asian":               "#29956A",
    "Other":               "#999999",
    # Skin tone (warm sequential)
    "light":               "#F5C9A3",
    "medium":              "#D4956A",
    "brown":               "#9B6340",
    "dark":                "#5C3317",
    # Age buckets (cool sequential)
    "0–14":                "#C6DBEF",
    "15–29":               "#6BAED6",
    "30–44":               "#2171B5",
    "45–59":               "#08519C",
    "60+":                 "#08306B",
}

# Label colour per fill: black on light backgrounds, white on dark
TEXT_COLOR = {
    "female":              "white",
    "male":                "white",
    "unknown":             "#333333",
    "West Eurasian":       "white",
    "Sub-Saharan African": "white",
    "Asian":               "white",
    "Other":               "white",
    "light":               "#333333",
    "medium":              "#333333",
    "brown":               "white",
    "dark":                "white",
    "0–14":                "#333333",
    "15–29":               "#333333",
    "30–44":               "white",
    "45–59":               "white",
    "60+":                 "white",
}

# ---------------------------------------------------------------------------
# Real-world baselines
# ---------------------------------------------------------------------------
WORLD_GENDER = {
    "female": 0.497, "male": 0.503, "unknown": 0.0,
}
WORLD_ANCESTRY = {
    "West Eurasian":       0.20,
    "Sub-Saharan African": 0.15,
    "Asian":               0.55,  # South, Southeast & East Asia combined (UN WPP 2024)
    "Other":               0.10,  # Americas + remaining; no separate labeling category
}
WORLD_AGE = OrderedDict([
    ("0–14",  0.25),
    ("15–29", 0.24),
    ("30–44", 0.21),
    ("45–59", 0.17),
    ("60+",   0.13),
])
AGE_BUCKETS = list(WORLD_AGE.keys())
AGE_EDGES   = [0, 15, 30, 45, 60, 999]

WORLD_POP_ANCESTRY = OrderedDict([
    ("South/Southeast\n& East Asian", 0.55),
    ("Sub-Saharan\nAfrican",           0.15),
    ("West Eurasian\n/ Europe / MENA", 0.20),
    ("Americas",                        0.08),
    ("Other",                           0.02),
])

CAPTION      = "Data: own analysis · n=24 per source · Baseline: UN WPP 2024, World Bank"
ACCENT_COLOR = "#2E72B8"
BAR_WIDTH    = 0.55

FINDINGS = {
    "gender":    "Most sources skew female — but AI models diverge significantly from the near-equal world baseline",
    "ancestry":  "West Eurasian faces dominate across all sources — 3× the real-world share",
    "skin_tone": "Over 75% of generated images show light skin across nearly all sources",
    "age":       "AI models skew toward young adults — children and seniors are virtually absent",
    "world_pop": "AI ancestry output is the mirror image of world demographics",
}

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
def _theme(style: str):
    base = 13 if style == "paper" else 16
    return (
        theme_minimal(base_size=base) +
        theme(
            text                  = element_text(family=_FONT, color="#222222"),
            plot_title            = element_text(family=_FONT, size=base + 5, face="bold",
                                                 margin={"b": 2}),
            plot_subtitle         = element_text(family=_FONT, size=base - 2, color="#777777",
                                                 margin={"b": 10}),
            plot_caption          = element_text(family=_FONT, size=base - 4, color="#999999",
                                                 ha="right", margin={"t": 8}),
            axis_title            = element_blank(),
            axis_text_x           = element_text(family=_FONT, size=base, color="#444444"),
            axis_text_y           = element_blank(),
            axis_ticks_major_x    = element_line(color="#CCCCCC", size=0.5),
            axis_line_x           = element_line(color="#CCCCCC", size=0.6),
            panel_grid_major_x    = element_blank(),
            panel_grid_minor      = element_blank(),
            panel_grid_major_y    = element_line(color="#EEEEEE", size=0.5),
            legend_title          = element_blank(),
            legend_text           = element_text(family=_FONT, size=base - 1),
            legend_position       = "bottom",
            legend_direction      = "horizontal",
            legend_key_size       = 12,
            legend_background     = element_rect(fill="white", color="#E0E0E0", size=0.5),
            legend_box_margin     = 6,
            plot_background       = element_rect(fill="white", color="none"),
            panel_background      = element_rect(fill="white", color="none"),
        )
    )

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _load_data():
    with open(STATS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _age_bucket(age):
    for i, edge in enumerate(AGE_EDGES[1:]):
        if age < edge:
            return AGE_BUCKETS[i]
    return AGE_BUCKETS[-1]


def _build_stacked_df(by_source, categories, world_baseline=None):
    """Long-format DataFrame for stacked bar charts."""
    rows = []

    if world_baseline:
        for cat in categories:
            rows.append({
                "source":      BASELINE_LABEL,
                "category":    cat,
                "pct":         world_baseline.get(cat, 0.0) * 100,
                "is_baseline": True,
            })

    for src in SOURCE_ORDER:
        total = sum(by_source[src].values()) or 1
        for cat in categories:
            rows.append({
                "source":      SOURCE_LABELS.get(src, src),
                "category":    cat,
                "pct":         by_source[src].get(cat, 0) / total * 100,
                "is_baseline": False,
            })

    df = pd.DataFrame(rows)

    # Segment labels — shown for all non-zero segments
    df["label"] = df["pct"].apply(lambda v: f"{v:.0f}%" if v > 0 else "")

    # Label colour: black on light fills, white on dark fills
    df["label_color"] = df["category"].map(TEXT_COLOR).fillna("white")

    # Baseline bar is slightly transparent to distinguish it visually
    df["bar_alpha"] = df["is_baseline"].map({True: 0.65, False: 1.0})

    # Factor ordering
    all_labels = ([BASELINE_LABEL] if world_baseline else []) + \
                 [SOURCE_LABELS.get(s, s) for s in SOURCE_ORDER]
    df["source"]   = pd.Categorical(df["source"],   categories=all_labels,  ordered=True)
    df["category"] = pd.Categorical(df["category"], categories=categories,  ordered=True)

    return df


def _stacked_bar_plot(df, categories, palette, title, finding, style="paper"):
    has_baseline = BASELINE_LABEL in df["source"].cat.categories.tolist()
    label_size   = 10 if style == "paper" else 12
    nrow         = 1

    p = (
        ggplot(df, aes(x="source", y="pct", fill="category", alpha="bar_alpha"))
        + geom_col(position="stack", width=BAR_WIDTH, color="none", size=0)
        + geom_text(
            aes(label="label", color="label_color"),
            position=position_stack(vjust=0.5),
            size=label_size, fontweight="bold", na_rm=True,
        )
        + scale_fill_manual(values=palette, breaks=list(reversed(categories)))
        + scale_color_identity()
        + scale_alpha_identity()
        + scale_y_continuous(
            labels=lambda ticks: [f"{int(t)}%" for t in ticks],
            limits=(0, 105),
            expand=(0, 0),
        )
        + guides(fill=guide_legend(nrow=nrow, reverse=True))
        + labs(title=title, subtitle=finding, caption=CAPTION)
        + _theme(style)
    )

    if has_baseline:
        p = p + geom_vline(xintercept=1.5, color="#CCCCCC", linetype="dashed", size=0.6)

    return p


def _postprocess_bars(fig, df):
    """Add subtle hairline segment dividers using DataFrame positions.

    Plotnine renders bars as PatchCollection (ax.collections), not ax.patches,
    so positions are computed directly from the data instead.
    """

    if df is None or "category" not in df.columns:
        return

    ax = fig.axes[0]
    sources    = df["source"].cat.categories.tolist()
    categories = df["category"].cat.categories.tolist()

    for x_idx, source in enumerate(sources, start=1):
        src_rows = df[df["source"] == source]
        if src_rows.empty:
            continue
        src_data = {r["category"]: r for _, r in src_rows.iterrows()}

        cum        = 0.0
        top_color  = None
        top_alpha  = 1.0

        # Plotnine stacks in reversed category order (last category → bottom)
        for cat in reversed(categories):
            row = src_data.get(cat)
            pct = float(row["pct"]) if row is not None else 0.0

            if pct > 0:
                if cum > 0:
                    # Subtle hairline divider at bottom of this segment
                    ax.plot(
                        [x_idx - BAR_WIDTH / 2, x_idx + BAR_WIDTH / 2],
                        [cum, cum],
                        color="white", linewidth=0.6, alpha=0.6, zorder=10,
                        solid_capstyle="butt",
                    )
                cum += pct


def _save(p, name, style, df=None):
    outdir    = OUT_DIR if style == "paper" else LI_DIR
    w, h, dpi = (10, 5.6, 150) if style == "paper" else (10, 6.8, 200)

    fig = p if isinstance(p, Figure) else p.draw()
    fig.set_size_inches(w, h)
    if df is not None:
        _postprocess_bars(fig, df)

    # Thin accent line at the very top of the figure
    fig.add_artist(mlines.Line2D(
        [0, 1], [1, 1],
        transform=fig.transFigure,
        color=ACCENT_COLOR, linewidth=6,
        solid_capstyle="butt", clip_on=False, zorder=100,
    ))
    fig.savefig(str(outdir / f"{name}.png"), dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  {'paper' if style == 'paper' else 'linkedin':8s}  →  {outdir / (name + '.png')}")


def _render(make_fn, name):
    """Render both paper and LinkedIn versions of a chart."""
    for style in ("paper", "linkedin"):
        result = make_fn(style)
        p, df  = result if isinstance(result, tuple) else (result, None)
        _save(p, name, style, df)

# ---------------------------------------------------------------------------
# Individual charts
# ---------------------------------------------------------------------------
def figure_gender(data):
    def make(style):
        by_source = {s: Counter() for s in SOURCE_ORDER}
        for rec in data:
            src = rec.get("source")
            if src in by_source:
                by_source[src][rec.get("perceived_gender", "unknown")] += 1
        categories = ["female", "male", "unknown"]
        df = _build_stacked_df(by_source, categories, world_baseline=WORLD_GENDER)
        return _stacked_bar_plot(df, categories, PALETTE,
                                 "Perceived gender by source", FINDINGS["gender"], style), df
    _render(make, "gender_by_source")


def figure_ancestry(data):
    def make(style):
        by_source = {s: Counter() for s in SOURCE_ORDER}
        for rec in data:
            src = rec.get("source")
            if src in by_source:
                val = rec.get("perceived_ancestry_cluster") or "Other"
                if val in ("East Asian", "South Asian"):
                    val = "Asian"
                by_source[src][val] += 1
        categories = ["West Eurasian", "Sub-Saharan African", "Asian", "Other"]
        df = _build_stacked_df(by_source, categories, world_baseline=WORLD_ANCESTRY)
        return _stacked_bar_plot(df, categories, PALETTE,
                                 "Perceived ancestry cluster by source", FINDINGS["ancestry"], style), df
    _render(make, "ancestry_by_source")


def figure_skin_tone(data):
    def make(style):
        by_source = {s: Counter() for s in SOURCE_ORDER}
        for rec in data:
            src = rec.get("source")
            if src in by_source:
                by_source[src][rec.get("skin_tone", "unknown")] += 1
        categories = ["light", "medium", "brown", "dark"]
        df = _build_stacked_df(by_source, categories)  # no world baseline
        return _stacked_bar_plot(df, categories, PALETTE,
                                 "Perceived skin tone by source", FINDINGS["skin_tone"], style), df
    _render(make, "skin_tone_by_source")


def figure_age(data):
    def make(style):
        by_source = {s: Counter() for s in SOURCE_ORDER}
        for rec in data:
            src = rec.get("source")
            age = rec.get("age_estimate")
            if src in by_source and isinstance(age, (int, float)):
                by_source[src][_age_bucket(age)] += 1
        df = _build_stacked_df(by_source, AGE_BUCKETS, world_baseline=WORLD_AGE)
        return _stacked_bar_plot(df, AGE_BUCKETS, PALETTE,
                                 "Perceived age distribution by source", FINDINGS["age"], style), df
    _render(make, "age_by_source")


def figure_world_pop_vs_ai(data):
    def make(style):
        base = 10 if style == "paper" else 13
        ai_sources = [s for s in SOURCE_ORDER if s not in REFERENCE_SOURCES]
        ancestry_map = {
            "West Eurasian":       "West Eurasian\n/ Europe / MENA",
            "Sub-Saharan African": "Sub-Saharan\nAfrican",
            "East Asian":          "South/Southeast\n& East Asian",
            "South Asian":         "South/Southeast\n& East Asian",
        }
        ai_counter = Counter()
        for rec in data:
            if rec.get("source") in ai_sources:
                val    = rec.get("perceived_ancestry_cluster") or "Other"
                mapped = ancestry_map.get(val, "Other")
                ai_counter[mapped] += 1

        total_ai = sum(ai_counter.values()) or 1
        categories = list(WORLD_POP_ANCESTRY.keys())
        rows = []
        for cat in categories:
            rows.append({"category": cat, "group": "World population",
                         "pct": WORLD_POP_ANCESTRY[cat] * 100})
            rows.append({"category": cat, "group": "AI-generated (combined)",
                         "pct": ai_counter.get(cat, 0) / total_ai * 100})

        df = pd.DataFrame(rows)
        df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)
        df["label"]    = df["pct"].apply(lambda v: f"{v:.0f}%")

        p = (
            ggplot(df, aes(x="category", y="pct", fill="group"))
            + geom_col(position="dodge", width=0.7, color="white", size=0.25)
            + geom_text(
                aes(label="label"),
                position="dodge", nudge_y=1.5,
                size=base - 3, color="#444444",
            )
            + scale_fill_manual(values={
                "World population":        "#7CB9D8",
                "AI-generated (combined)": "#F0A030",
            })
            + scale_y_continuous(
                labels=lambda ticks: [f"{int(t)}%" for t in ticks],
                limits=(0, 65),
                expand=(0, 0),
            )
            + guides(fill=guide_legend(nrow=1))
            + labs(
                title="World population vs. AI-generated perceived ancestry",
                subtitle=FINDINGS["world_pop"],
                caption=CAPTION,
            )
            + _theme(style)
        )
        return p
    _render(make, "world_pop_vs_ai_ancestry")


# ---------------------------------------------------------------------------
# Model profile charts (deviation from real-world baseline)
# ---------------------------------------------------------------------------
_PROFILE_ITEMS = [
    # (group, label, baseline_pct, bar_color)
    ("Gender",   "male",                WORLD_GENDER["male"]               * 100, PALETTE["male"]),
    ("Gender",   "female",              WORLD_GENDER["female"]             * 100, PALETTE["female"]),
    ("Ancestry", "Asian",               WORLD_ANCESTRY["Asian"]               * 100, PALETTE["Asian"]),
    ("Ancestry", "West Eurasian",       WORLD_ANCESTRY["West Eurasian"]       * 100, PALETTE["West Eurasian"]),
    ("Ancestry", "Sub-Saharan African", WORLD_ANCESTRY["Sub-Saharan African"] * 100, PALETTE["Sub-Saharan African"]),
    ("Ancestry", "Other",               WORLD_ANCESTRY["Other"]               * 100, PALETTE["Other"]),
    ("Age",      "0–14",               WORLD_AGE["0–14"]                  * 100, PALETTE["0–14"]),
    ("Age",      "15–29",              WORLD_AGE["15–29"]                 * 100, PALETTE["15–29"]),
    ("Age",      "30–44",              WORLD_AGE["30–44"]                 * 100, PALETTE["30–44"]),
    ("Age",      "45–59",              WORLD_AGE["45–59"]                 * 100, PALETTE["45–59"]),
    ("Age",      "60+",               WORLD_AGE["60+"]                   * 100, PALETTE["60+"]),
]


def figure_model_profile(data, source_name, style="paper"):
    """Observed-share chart with baseline markers for a single source."""
    src_recs  = [r for r in data if r.get("source") == source_name]
    n         = len(src_recs) or 1
    age_recs  = [r for r in src_recs if isinstance(r.get("age_estimate"), (int, float))]
    n_age     = len(age_recs) or 1

    g_ctr  = Counter(r.get("perceived_gender", "unknown") for r in src_recs)
    def _norm_ancestry(r):
        val = r.get("perceived_ancestry_cluster") or "Other"
        return "Asian" if val in ("East Asian", "South Asian") else val
    an_ctr = Counter(_norm_ancestry(r) for r in src_recs)
    ag_ctr = Counter(_age_bucket(r["age_estimate"]) for r in age_recs)

    def _ai(group, label):
        if group == "Gender":   return g_ctr.get(label,  0) / n     * 100
        if group == "Ancestry": return an_ctr.get(label, 0) / n     * 100
        if group == "Age":      return ag_ctr.get(label,  0) / n_age * 100
        return 0.0

    def _score(group_rows):
        tvd = 0.005 * sum(abs(row["ai_pct"] - row["baseline"]) for row in group_rows)
        max_tvd = 1 - min(row["baseline"] / 100 for row in group_rows)
        baseline_mismatch = tvd / max_tvd if max_tvd > 0 else 0.0

        max_generated_share = max(row["ai_pct"] / 100 for row in group_rows)
        max_baseline_share = max(row["baseline"] / 100 for row in group_rows)
        concentration_gap = (
            (max_generated_share - max_baseline_share) / (1 - max_baseline_share)
            if max_generated_share > max_baseline_share and max_baseline_share < 1
            else 0.0
        )

        return 10 * max(baseline_mismatch, concentration_gap)

    def _score_color(score):
        if score < 2: return "#2EAD66"
        if score < 4: return "#A6C84C"
        if score < 6: return "#F2B84B"
        if score < 8: return "#E67E22"
        return "#D64545"

    rows = []
    for group, label, baseline, color in _PROFILE_ITEMS:
        ai_val  = _ai(group, label)
        if group == "Gender":
            count = g_ctr.get(label, 0)
            denom = n
        elif group == "Ancestry":
            count = an_ctr.get(label, 0)
            denom = n
        else:
            count = ag_ctr.get(label, 0)
            denom = n_age
        rows.append({
            "group":     group,
            "label":     label,
            "ai_pct":    ai_val,
            "baseline":  baseline,
            "color":     color,
            "count":     count,
            "denom":     denom,
            "label_x":   103,
            "bar_label": f"{count}/{denom} · {ai_val:.0f}%",
        })

    df = pd.DataFrame(rows)
    display = SOURCE_LABELS.get(source_name, source_name).replace("\n", " ")
    base    = 13 if style == "paper" else 16
    lsz     = 10 if style == "paper" else 12
    groups  = ["Gender", "Ancestry", "Age"]
    heights = [2, 4, 5]

    fig, axes = plt.subplots(
        len(groups), 1,
        gridspec_kw={"height_ratios": heights, "hspace": 0.10},
        constrained_layout=False,
    )

    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.16, right=0.84, top=0.76, bottom=0.16)
    fig.suptitle(
        f"Diversity profile: {display}",
        x=0.16, y=0.945, ha="left",
        fontsize=base + 7, fontweight="bold", fontfamily=_FONT, color="#222222",
    )
    fig.text(
        0.16, 0.875,
        "Bar = generated share · black diamond = real-world baseline · label = generated count · ring = gap score",
        ha="left", va="center", fontsize=base - 2, fontfamily=_FONT, color="#777777",
    )

    for ax, group in zip(axes, groups):
        group_rows = df[df["group"] == group].to_dict("records")
        y = list(range(len(group_rows)))
        labels = [row["label"] for row in group_rows]

        ax.barh(y, [row["ai_pct"] for row in group_rows],
                height=0.65, color=[row["color"] for row in group_rows], edgecolor="none")
        ax.scatter([row["baseline"] for row in group_rows], y,
                   marker="D", s=54 if style == "paper" else 70,
                   facecolors="white", edgecolors="#222222", linewidths=1.3, zorder=5)

        for yi, row in zip(y, group_rows):
            ax.text(103, yi, row["bar_label"],
                    ha="left", va="center", fontsize=lsz,
                    fontfamily=_FONT, color="#555555")

        ax.set_xlim(-4, 132)
        ax.set_ylim(-0.6, len(group_rows) - 0.4)
        ax.invert_yaxis()
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontfamily=_FONT, fontsize=base, color="#444444")
        ax.tick_params(axis="y", length=0, pad=8)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xticklabels([f"{tick}%" for tick in [0, 25, 50, 75, 100]],
                           fontfamily=_FONT, fontsize=base, color="#444444")
        ax.grid(axis="x", color="#E5E5E5", linewidth=0.8)
        ax.grid(axis="y", color="#EEEEEE", linewidth=0.6)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#CCCCCC")

        score = _score(group_rows)
        score_color = _score_color(score)

        ax.add_patch(Rectangle(
            (1.010, 0.0), 0.055, 1.0,
            transform=ax.transAxes,
            facecolor="#F0F0F0",
            edgecolor="none",
            clip_on=False,
            zorder=2,
        ))
        ax.text(1.0375, 0.50, group, transform=ax.transAxes,
                rotation=-90, ha="center", va="center",
                fontsize=base, fontweight="bold", fontfamily=_FONT, color="#222222",
                clip_on=False, zorder=3)
        ax.scatter([1.135], [0.50], transform=ax.transAxes,
                   s=1120 if style == "paper" else 1500,
                   facecolors="white", edgecolors=score_color, linewidths=5,
                   clip_on=False, zorder=10)
        ax.annotate("GAP", xy=(1.135, 0.50), xycoords=ax.transAxes,
                    xytext=(0, 6), textcoords="offset points",
                    ha="center", va="center", fontsize=base - 6,
                    fontweight="bold", fontfamily=_FONT, color="#666666",
                    clip_on=False, zorder=11)
        ax.annotate(f"{score:.1f}", xy=(1.135, 0.50), xycoords=ax.transAxes,
                    xytext=(0, -5), textcoords="offset points",
                    ha="center", va="center", fontsize=base + 2,
                    fontweight="bold", fontfamily=_FONT, color="#222222",
                    clip_on=False, zorder=11)

    for ax in axes[:-1]:
        ax.tick_params(axis="x", labelbottom=False)
        ax.spines["bottom"].set_visible(False)

    fig.text(0.16, 0.065, CAPTION, ha="left", va="center",
             fontsize=base - 5, fontfamily=_FONT, color="#A0A0A0")
    return fig


def figure_all_profiles(data):
    for src in SOURCE_ORDER:
        def make(style, _src=src):
            return figure_model_profile(data, _src, style)
        _render(make, f"profile_{src.lower()}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    data = _load_data()
    print(f"Loaded {len(data)} records\n")
    print("gender_by_source")
    figure_gender(data)
    print("ancestry_by_source")
    figure_ancestry(data)
    print("skin_tone_by_source")
    figure_skin_tone(data)
    print("age_by_source")
    figure_age(data)
    print("world_pop_vs_ai_ancestry")
    figure_world_pop_vs_ai(data)
    print("model profiles")
    figure_all_profiles(data)
    print(f"\nDone. Paper figures → {OUT_DIR}/")
    print(f"      LinkedIn figures → {LI_DIR}/")


if __name__ == "__main__":
    main()
