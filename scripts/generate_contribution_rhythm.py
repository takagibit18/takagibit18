"""
Generate a warm editorial-style contribution heatmap for the GitHub profile README.

Usage:
  GH_TOKEN=... python scripts/generate_contribution_rhythm.py --user takagibit18

This writes:
  assets/contribution-rhythm.png
"""

from __future__ import annotations
import argparse
import datetime as dt
import math
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

def font(candidates, size):
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

def fetch_contributions(user: str, token: str):
    to_date = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    from_date = (dt.datetime.utcnow() - dt.timedelta(days=365)).replace(microsecond=0).isoformat() + "Z"
    r = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": QUERY, "variables": {"login": user, "from": from_date, "to": to_date}},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    # normalize to Monday-first rows
    cols = []
    for week in weeks:
        days = week["contributionDays"]
        day_map = {d["weekday"]: d["contributionCount"] for d in days}  # Sun=0 .. Sat=6
        monday_first = [day_map.get(i % 7, 0) for i in range(1,7)] + [day_map.get(0, 0)]
        cols.append(monday_first)
    return cols

def level(count, max_count):
    if count <= 0:
        return 0
    steps = [0.08, 0.22, 0.42, 0.68, 1.0]
    ratio = count / max(max_count, 1)
    for i, s in enumerate(steps, start=1):
        if ratio <= s:
            return i
    return 5

def render(cols):
    W, H = 1800, 720
    img = Image.new("RGB", (W, H), "#f6f2eb")
    draw = ImageDraw.Draw(img)

    title_font = font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"], 54)
    subtitle_font = font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"], 24)
    month_font = font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"], 16)
    small_font = font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"], 15)
    caption_font = font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Italic.ttf"], 28)

    ink = "#2c2a27"
    muted = "#a38f72"
    line = "#ddd3c5"
    palette = ["#efe7db", "#e5dac7", "#d6c7aa", "#b9aa79", "#978b57", "#6f6635"]

    draw.text((W//2, 60), "✦", font=subtitle_font, fill=muted, anchor="mm")
    draw.text((W//2, 140), "CONTRIBUTION RHYTHM", font=title_font, fill=ink, anchor="mm")
    draw.line((W//2-220, 196, W//2-120, 196), fill=line, width=2)
    draw.line((W//2+120, 196, W//2+220, 196), fill=line, width=2)
    draw.text((W//2, 196), "LAST 365 DAYS", font=subtitle_font, fill=muted, anchor="mm")

    grid_left = 260
    grid_top = 300
    cell = 22
    gap = 6
    rows = 7
    grid_width = len(cols)*cell + (len(cols)-1)*gap
    grid_height = rows*cell + (rows-1)*gap

    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for i, d in enumerate(days):
        y = grid_top + i*(cell+gap) + cell/2
        draw.text((150, y), d, font=small_font, fill="#5a5145", anchor="lm")

    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_positions = [0, 4, 8, 12, 17, 21, 25, 29, 33, 38, 43, 48]
    for m, pos in zip(month_names, month_positions):
        x = grid_left + pos*(cell+gap) + 10
        draw.text((x, grid_top-48), m, font=month_font, fill="#4b4135", anchor="mm")
        draw.line((x, grid_top-20, x, grid_top-4), fill=line, width=1)

    max_count = max(max(col) for col in cols) if cols else 1
    for c, col in enumerate(cols):
        for r, count in enumerate(col):
            x0 = grid_left + c*(cell+gap)
            y0 = grid_top + r*(cell+gap)
            x1 = x0 + cell
            y1 = y0 + cell
            color = palette[level(count, max_count)]
            draw.rounded_rectangle((x0, y0, x1, y1), radius=5, fill=color)

    legend_y = grid_top + grid_height + 62
    legend_x = W//2 - 120
    draw.text((legend_x-40, legend_y+11), "Less", font=subtitle_font, fill="#4f463c", anchor="rm")
    for i, color in enumerate(palette):
        x = legend_x + i*(cell+12)
        draw.rounded_rectangle((x, legend_y, x+cell+10, legend_y+18), radius=6, fill=color)
    draw.text((legend_x + 6*(cell+12) + 40, legend_y+11), "More", font=subtitle_font, fill="#4f463c", anchor="lm")

    cap_y = legend_y + 118
    draw.line((190, cap_y, 610, cap_y), fill=line, width=2)
    draw.line((1190, cap_y, 1610, cap_y), fill=line, width=2)
    draw.text((W//2, cap_y), "quiet work, consistently.", font=caption_font, fill="#5e4f3b", anchor="mm")
    draw.text((W//2, cap_y-35), "✦", font=subtitle_font, fill=muted, anchor="mm")
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    args = ap.parse_args()
    token = os.environ["GH_TOKEN"]
    cols = fetch_contributions(args.user, token)
    img = render(cols)
    ASSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(ASSET_PATH, quality=95)
    print(f"Wrote {ASSET_PATH}")

if __name__ == "__main__":
    main()
