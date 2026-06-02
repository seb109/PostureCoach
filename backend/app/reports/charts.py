"""
reports/charts.py — Individual matplotlib panel builders.

Each function receives an ``Axes`` object and the data it needs, then
populates the axes in-place.  No figure creation, no file I/O here —
that belongs in :mod:`report_generator`.
"""
from __future__ import annotations

import matplotlib.patches as mpatches
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection

from app.config import (
    BG_DARK,
    BG_PANEL,
    COLOR_BAD,
    COLOR_GOOD,
    COLOR_SLIGHT,
    TEXT_BRIGHT,
    TEXT_DIM,
)
from app.reports.analytics import SessionStats
from app.reports.parser import SessionData

STATUS_COLORS = {
    "GOOD POSTURE":  COLOR_GOOD,
    "SLIGHT SLOUCH": COLOR_SLIGHT,
    "BAD POSTURE":   COLOR_BAD,
}


def draw_ratio_timeline(ax: Axes, data: SessionData, stats: SessionStats) -> None:
    """Panel 1 — coloured ratio-over-time line with zone bands."""
    elapsed = data.elapsed
    ratios  = data.ratios

    ymin = max(0,   float(ratios.min()) - 8)
    ymax = min(160, float(ratios.max()) + 8)

    # Zone bands
    ax.axhspan(85,  ymax, alpha=0.07, color=COLOR_GOOD,   zorder=0)
    ax.axhspan(70,  85,   alpha=0.07, color=COLOR_SLIGHT,  zorder=0)
    ax.axhspan(ymin, 70,  alpha=0.07, color=COLOR_BAD,    zorder=0)

    # Threshold dashed lines
    ax.axhline(85, color=COLOR_GOOD, lw=0.9, ls="--", alpha=0.45)
    ax.axhline(70, color=COLOR_BAD,  lw=0.9, ls="--", alpha=0.45)

    # Worst BAD spans
    for i, (t0, t1) in enumerate(stats.top_bad_streaks):
        ax.axvspan(t0, t1, alpha=0.18, color=COLOR_BAD,
                   label="Worst BAD period" if i == 0 else "_")

    # Coloured line segments
    pts  = np.column_stack([elapsed, ratios]).reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    seg_colors = [
        STATUS_COLORS.get(data.statuses[i], "#ffffff")
        for i in range(len(data.statuses) - 1)
    ]
    lc = LineCollection(segs, colors=seg_colors, linewidth=2.2, alpha=0.92, zorder=3)
    ax.add_collection(lc)

    # Zone labels
    for y, label, col in [
        (107, "GOOD",   COLOR_GOOD),
        (77.5, "SLIGHT", COLOR_SLIGHT),
        (55,  "BAD",    COLOR_BAD),
    ]:
        if ymin < y < ymax:
            ax.text(float(elapsed[-1]) * 0.005, y, label,
                    color=col, fontsize=8, va="center", alpha=0.7)

    ax.set_xlim(float(elapsed[0]), float(elapsed[-1]))
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Elapsed (seconds)", fontsize=10)
    ax.set_ylabel("Posture ratio  (% of baseline)", fontsize=10)
    ax.set_title("Posture Ratio Over Time", color=TEXT_BRIGHT, fontsize=12, pad=8)
    ax.grid(True, axis="y", linestyle=":", linewidth=0.7)

    legend_handles = [
        mpatches.Patch(color=COLOR_GOOD,   label=f"Good   {stats.good_pct:.0f}%"),
        mpatches.Patch(color=COLOR_SLIGHT, label=f"Slight  {stats.slight_pct:.0f}%"),
        mpatches.Patch(color=COLOR_BAD,    label=f"Bad     {stats.bad_pct:.0f}%"),
    ]
    if stats.top_bad_streaks:
        legend_handles.append(
            mpatches.Patch(color=COLOR_BAD, alpha=0.35, label="Worst BAD periods")
        )
    ax.legend(handles=legend_handles, loc="upper right",
              facecolor=BG_DARK, edgecolor="#2a2a44",
              labelcolor=TEXT_BRIGHT, fontsize=9)


def draw_pie(ax: Axes, stats: SessionStats) -> None:
    """Panel 2 — time-split pie chart."""
    sizes   = [stats.good_pct, stats.slight_pct, stats.bad_pct]
    colors  = [COLOR_GOOD, COLOR_SLIGHT, COLOR_BAD]
    labels  = [
        f"Good\n{stats.good_pct:.1f}%",
        f"Slight\n{stats.slight_pct:.1f}%",
        f"Bad\n{stats.bad_pct:.1f}%",
    ]
    explode = (0.04, 0.04, 0.06)

    non_zero = [
        (s, c, l, e)
        for s, c, l, e in zip(sizes, colors, labels, explode)
        if s > 0
    ]
    if non_zero:
        _s, _c, _l, _e = zip(*non_zero)
        ax.pie(
            _s, labels=_l, colors=_c, explode=_e,
            textprops={"color": TEXT_BRIGHT, "fontsize": 9.5},
            wedgeprops={"edgecolor": BG_DARK, "linewidth": 2},
            startangle=90,
        )
    ax.set_title("Time Split", color=TEXT_BRIGHT, fontsize=11, pad=10)


def draw_score_card(ax: Axes, stats: SessionStats) -> None:
    """Panel 3 — numerical score card with summary stats."""
    score_color = (
        COLOR_GOOD   if stats.score >= 75 else
        COLOR_SLIGHT if stats.score >= 50 else
        COLOR_BAD
    )
    ax.axis("off")

    ax.text(0.5, 0.92, f"{stats.score:.0f}",
            fontsize=64, color=score_color, fontweight="bold",
            ha="center", va="top", transform=ax.transAxes)
    ax.text(0.5, 0.58, "SESSION SCORE",
            fontsize=11, color=TEXT_DIM, ha="center", va="top",
            transform=ax.transAxes)

    ax.axhline(0.50, lw=0.6, color="#2a2a44", xmin=0.1, xmax=0.9)

    summary = [
        (f"{stats.duration_min:.1f} min",      "Duration"),
        (f"{len(stats.bad_streaks)}",           "Bad periods"),
        (f"{stats.best_good_streak:.0f} s",     "Best good streak"),
        (f"{stats.total_frames}",               "Data points"),
    ]
    for i, (val, lbl) in enumerate(summary):
        y_pos = 0.44 - i * 0.115
        ax.text(0.28, y_pos, val,
                fontsize=11, color=TEXT_BRIGHT, fontweight="bold",
                ha="right", va="top", transform=ax.transAxes)
        ax.text(0.32, y_pos, lbl,
                fontsize=9, color=TEXT_DIM,
                ha="left", va="top", transform=ax.transAxes)

    ax.set_title("Session Summary", color=TEXT_BRIGHT, fontsize=11, pad=10)


def draw_bad_streak_bars(ax: Axes, stats: SessionStats) -> None:
    """Panel 4 — horizontal bars for top bad-posture streaks."""
    if not stats.top_bad_streaks:
        ax.axis("off")
        ax.text(0.5, 0.5, "No bad posture\nperiods detected!",
                ha="center", va="center", fontsize=13,
                color=COLOR_GOOD, transform=ax.transAxes, fontweight="bold")
        ax.set_title("Worst BAD POSTURE Streaks", color=TEXT_BRIGHT, fontsize=11, pad=10)
        return

    durations  = [t1 - t0 for t0, t1 in stats.top_bad_streaks]
    y_pos      = np.arange(len(durations))
    bar_labels = [f"#{i+1}  @ {t0:.0f}s" for i, (t0, _) in enumerate(stats.top_bad_streaks)]

    bars = ax.barh(y_pos, durations, color=COLOR_BAD, alpha=0.78,
                   edgecolor=BG_DARK, linewidth=1.2, height=0.5)
    for bar, dur in zip(bars, durations):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{dur:.0f}s", va="center", ha="left",
                color=TEXT_BRIGHT, fontsize=9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(bar_labels, fontsize=9)
    ax.set_xlabel("Duration (seconds)", fontsize=9)
    ax.set_title("Worst BAD POSTURE Streaks", color=TEXT_BRIGHT, fontsize=11, pad=10)
    ax.invert_yaxis()
    ax.grid(True, axis="x", linestyle=":", linewidth=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
