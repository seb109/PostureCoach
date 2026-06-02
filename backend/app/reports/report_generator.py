"""
reports/report_generator.py — Assembles all chart panels into a single figure.

This is the only module that creates a matplotlib Figure or writes PNG files.
"""
from __future__ import annotations

import os

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from app.config import BG_DARK, BG_PANEL, TEXT_BRIGHT, TEXT_DIM
from app.reports.analytics import SessionStats, compute_stats
from app.reports.charts import (
    draw_bad_streak_bars,
    draw_pie,
    draw_ratio_timeline,
    draw_score_card,
)
from app.reports.parser import SessionData, find_latest_csv, load_session


def generate_report(csv_path: str | None = None, show: bool = True) -> str:
    """
    Build and save the PostureCoach session report.

    Parameters
    ----------
    csv_path:
        Path to a session CSV.  If *None*, the latest file is auto-selected.
    show:
        Whether to call ``plt.show()`` after saving.

    Returns
    -------
    str
        Absolute path of the saved PNG.
    """
    if csv_path is None:
        csv_path = find_latest_csv()

    print(f"[ReportGenerator] Loading: {csv_path}")
    data  = load_session(csv_path)
    stats = compute_stats(data)

    _apply_theme()
    fig = _build_figure(data, stats, csv_path)

    out_png = csv_path.replace(".csv", "_report.png")
    fig.savefig(out_png, dpi=130, bbox_inches="tight", facecolor=BG_DARK)
    print(f"[ReportGenerator] Report saved to {out_png}")

    if show:
        plt.show()

    plt.close(fig)
    return out_png


# ── Private helpers ────────────────────────────────────────────────────────

def _apply_theme() -> None:
    plt.rcParams.update({
        "font.family":      "DejaVu Sans",
        "text.color":       TEXT_BRIGHT,
        "axes.labelcolor":  TEXT_DIM,
        "xtick.color":      TEXT_DIM,
        "ytick.color":      TEXT_DIM,
        "axes.edgecolor":   "#2a2a44",
        "grid.color":       "#1e1e36",
        "grid.alpha":       1.0,
        "figure.facecolor": BG_DARK,
        "axes.facecolor":   BG_PANEL,
    })


def _build_figure(
    data: SessionData,
    stats: SessionStats,
    csv_path: str,
) -> plt.Figure:
    fig = plt.figure(figsize=(17, 9.5))
    fig.patch.set_facecolor(BG_DARK)

    session_label = (
        os.path.basename(csv_path)
        .replace(".csv", "")
        .replace("session_", "")
        .replace("_", " - ")
    )
    score_color = (
        "#00DC64" if stats.score >= 75 else
        "#FFA040" if stats.score >= 50 else
        "#FF4444"
    )

    fig.suptitle(
        f"PostureCoach  -  {session_label}   |   "
        f"Duration: {stats.duration_min:.1f} min   |   "
        f"Score: {stats.score:.0f} / 100",
        fontsize=14, fontweight="bold", color=TEXT_BRIGHT, y=0.985,
    )

    gs = GridSpec(
        2, 3, figure=fig,
        top=0.94, bottom=0.07,
        left=0.06, right=0.97,
        hspace=0.42, wspace=0.35,
        height_ratios=[1.7, 1],
    )

    ax_line  = fig.add_subplot(gs[0, :])
    ax_pie   = fig.add_subplot(gs[1, 0])
    ax_score = fig.add_subplot(gs[1, 1])
    ax_stats = fig.add_subplot(gs[1, 2])

    draw_ratio_timeline(ax_line,  data,  stats)
    draw_pie(ax_pie,              stats)
    draw_score_card(ax_score,     stats)
    draw_bad_streak_bars(ax_stats, stats)

    return fig
