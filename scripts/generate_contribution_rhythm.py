"""
Generate the warm editorial-style contribution heatmap used by the profile README.

The visual style is fixed here; the actual cells, dates, month labels, and intensity
are generated from GitHub's real contribution data on every run.

Usage:
    GH_TOKEN=... python scripts/generate_contribution_rhythm.py --user takagibit18

Output:
    assets/contribution-rhythm.png
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = REPO_ROOT / "assets" / "contribution-rhythm.png"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""

PALETTE = ["#efe7db", "#e5dac7", "#d6c7aa", "#b9aa79", "#978b57", "#6f6635"]


def load_font(candidates: list[str], size: int):
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def fetch_contributions(user: str, token: str):
    now = dt.datetime.now(dt.timezone.utc)
    start = now - dt.timedelta(days=364)

    response = requests.post(
        "https://api.github.com/graphql",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={
            "query": QUERY,
            "variables": {
                "login": user,
                "from": start.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "to": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            },
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("errors"):
        raise RuntimeError(payload["errors"])

    user_data = payload.get("data", {}).get("user")
    if not user_data:
        raise RuntimeError(f"GitHub user not found: {user}")

    calendar = user_data["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]

    # Preserve the actual date for every cell.
    columns = []
    for week in weeks:
        column = [None] * 7  # Monday first
        for day in week["contributionDays"]:
            github_weekday = int(day["weekday"])  # Sunday=0 ... Saturday=6
            monday_index = (github_weekday - 1) % 7
            column[monday_index] = {
                "date": dt.date.fromisoformat(day["date"]),
                "count": int(day["contributionCount"]),
            }
        columns.append(column)

    return columns, int(calendar["totalContributions"])


def intensity_levels(columns):
    positive_counts = sorted(
        cell["count"]
        for col in columns
        for cell in col
        if cell is not None and cell["count"] > 0
    )
    if not positive_counts:
        return [1, 2, 3, 4]

    def percentile(p: float) -> int:
        idx = round((len(positive_counts) - 1) * p)
        return positive_counts[max(0, min(idx, len(positive_counts) - 1))]

    thresholds = [
        max(1, percentile(0.25)),
        max(1, percentile(0.50)),
        max(1, percentile(0.75)),
        max(1, percentile(0.90)),
    ]

    # Ensure strict non-decreasing thresholds even on sparse calendars.
    for i in range(1, len(thresholds)):
        thresholds[i] = max(thresholds[i], thresholds[i - 1])
    return thresholds


def level_for_count(count: int, thresholds: list[int]) -> int:
    if count <= 0:
        return 0
    if count <= thresholds[0]:
        return 1
    if count <= thresholds[1]:
        return 2
    if count <= thresholds[2]:
        return 3
    if count <= thresholds[3]:
        return 4
    return 5


def month_markers(columns):
    """Return (column_index, short_month, year) where a new month begins."""
    markers = []
    previous_month = None

    for col_idx, col in enumerate(columns):
        dated_cells = [cell for cell in col if cell is not None]
        if not dated_cells:
            continue

        # Choose the earliest real date present in the week.
        first_date = min(cell["date"] for cell in dated_cells)
        month_key = (first_date.year, first_date.month)

        if month_key != previous_month:
            markers.append((col_idx, first_date.strftime("%b"), first_date.year))
            previous_month = month_key

    # Avoid crowded labels when a month begins in consecutive very narrow positions.
    filtered = []
    last_idx = -99
    for marker in markers:
        if marker[0] - last_idx >= 3:
            filtered.append(marker)
            last_idx = marker[0]
    return filtered


def render(columns, total_contributions: int, user: str):
    W, H = 1800, 720
    image = Image.new("RGB", (W, H), "#f6f2eb")
    draw = ImageDraw.Draw(image)

    title_font = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
    ], 54)
    subtitle_font = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
    ], 24)
    month_font = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
    ], 16)
    small_font = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ], 15)
    caption_font = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Italic.ttf",
    ], 28)

    ink = "#2c2a27"
    muted = "#a38f72"
    line = "#ddd3c5"

    draw.text((W // 2, 60), "✦", font=subtitle_font, fill=muted, anchor="mm")
    draw.text((W // 2, 140), "CONTRIBUTION RHYTHM", font=title_font, fill=ink, anchor="mm")
    draw.line((W // 2 - 220, 196, W // 2 - 120, 196), fill=line, width=2)
    draw.line((W // 2 + 120, 196, W // 2 + 220, 196), fill=line, width=2)
    draw.text((W // 2, 196), "LAST 365 DAYS", font=subtitle_font, fill=muted, anchor="mm")

    grid_left = 250
    grid_top = 300
    cell = 22
    gap = 6
    rows = 7
    grid_height = rows * cell + (rows - 1) * gap

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for row, name in enumerate(weekdays):
        y = grid_top + row * (cell + gap) + cell / 2
        draw.text((145, y), name, font=small_font, fill="#5a5145", anchor="lm")

    for col_idx, label, year in month_markers(columns):
        x = grid_left + col_idx * (cell + gap) + cell / 2
        draw.text((x, grid_top - 48), label, font=month_font, fill="#4b4135", anchor="mm")
        draw.line((x, grid_top - 20, x, grid_top - 4), fill=line, width=1)

    thresholds = intensity_levels(columns)
    for col_idx, col in enumerate(columns):
        for row, cell_data in enumerate(col):
            if cell_data is None:
                continue
            x0 = grid_left + col_idx * (cell + gap)
            y0 = grid_top + row * (cell + gap)
            x1 = x0 + cell
            y1 = y0 + cell
            color = PALETTE[level_for_count(cell_data["count"], thresholds)]
            draw.rounded_rectangle((x0, y0, x1, y1), radius=5, fill=color)

    legend_y = grid_top + grid_height + 62
    legend_x = W // 2 - 135
    draw.text((legend_x - 42, legend_y + 10), "Less", font=subtitle_font, fill="#4f463c", anchor="rm")
    for i, color in enumerate(PALETTE):
        x = legend_x + i * (cell + 12)
        draw.rounded_rectangle((x, legend_y, x + cell + 10, legend_y + 18), radius=6, fill=color)
    draw.text((legend_x + 6 * (cell + 12) + 35, legend_y + 10), "More", font=subtitle_font, fill="#4f463c", anchor="lm")

    # Real aggregate metadata, also regenerated daily.
    draw.text(
        (W // 2, legend_y + 58),
        f"{total_contributions:,} contributions · @{user}",
        font=small_font,
        fill="#8c7b63",
        anchor="mm",
    )

    caption_y = legend_y + 122
    draw.line((190, caption_y, 610, caption_y), fill=line, width=2)
    draw.line((1190, caption_y, 1610, caption_y), fill=line, width=2)
    draw.text((W // 2, caption_y), "quiet work, consistently.", font=caption_font, fill="#5e4f3b", anchor="mm")

    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=True)
    args = parser.parse_args()

    token = os.environ["GH_TOKEN"]
    columns, total = fetch_contributions(args.user, token)
    image = render(columns, total, args.user)

    ASSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(ASSET_PATH, format="PNG", optimize=True)
    print(f"Wrote {ASSET_PATH}")


if __name__ == "__main__":
    main()
