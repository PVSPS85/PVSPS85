#!/usr/bin/env python3

import json
import os
from datetime import datetime


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "contributions.json"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "contrib-heatmap.svg"
)


# GitHub-style contribution colors.
PALETTE = [
    "#161b22",  # 0
    "#0e4429",  # 1
    "#006d32",  # 2
    "#26a641",  # 3
    "#39d353",  # 4
]


CELL_SIZE = 13
GAP = 4
RADIUS = 3

LEFT = 20
TOP = 55

HEADER_HEIGHT = 35
FOOTER_HEIGHT = 45


def load_data():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Missing data file: {DATA_FILE}"
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_level(level):
    try:
        level = int(level)
    except (TypeError, ValueError):
        return 0

    return max(0, min(level, len(PALETTE) - 1))


def generate_svg(data):
    days = data.get("days", [])

    if not days:
        raise ValueError("No contribution data found.")

    # The GitHub calendar has 7 rows:
    # Sunday -> Saturday.
    #
    # We arrange the contribution days into
    # week columns.

    first_date = datetime.fromisoformat(
        days[0]["date"]
    )

    # Move backwards to Sunday.
    start_weekday = (
        first_date.weekday() + 1
    ) % 7

    total_cells = start_weekday + len(days)

    weeks = (total_cells + 6) // 7

    width = (
        LEFT * 2
        + weeks * (CELL_SIZE + GAP)
        - GAP
    )

    height = (
        TOP
        + 7 * (CELL_SIZE + GAP)
        + HEADER_HEIGHT
        + FOOTER_HEIGHT
    )

    svg = []

    svg.append(
        f'''<svg xmlns="http://www.w3.org/2000/svg"
        width="{width}"
        height="{height}"
        viewBox="0 0 {width} {height}">
'''
    )

    # Background
    svg.append(
        f'''
<rect width="100%" height="100%"
      rx="12"
      fill="#0d1117"/>
'''
    )

    # Terminal-style title.
    svg.append(
        f'''
<text x="{LEFT}"
      y="30"
      font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
      font-size="14"
      fill="#8b949e">
  pranav@github ~ $ ./contributions.sh
</text>
'''
    )

    # Animation definition.
    svg.append(
        '''
<defs>

  <style>
    .cell {
      opacity: 0;
      transform-box: fill-box;
      transform-origin: center;
      animation: reveal 0.45s ease-out forwards;
    }

    @keyframes reveal {
      from {
        opacity: 0;
        transform: translateY(-8px) scale(0.85);
      }

      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }
  </style>

</defs>
'''
    )

    # Render contribution cells.
    for index, day in enumerate(days):

        absolute_index = (
            start_weekday + index
        )

        week = absolute_index // 7
        row = absolute_index % 7

        x = (
            LEFT
            + week * (CELL_SIZE + GAP)
        )

        y = (
            TOP
            + row * (CELL_SIZE + GAP)
        )

        level = normalize_level(
            day.get("level", 0)
        )

        color = PALETTE[level]

        # Diagonal animation:
        # cells further right/down appear later.
        delay = (
            (week * 0.025)
            + (row * 0.035)
        )

        svg.append(
            f'''
<rect
  class="cell"
  x="{x}"
  y="{y}"
  width="{CELL_SIZE}"
  height="{CELL_SIZE}"
  rx="{RADIUS}"
  fill="{color}"
  style="animation-delay:{delay:.3f}s"
>
  <title>
    {day["date"]}: {day["count"]} contributions
  </title>
</rect>
'''
        )

    # Legend.
    legend_y = (
        TOP
        + 7 * (CELL_SIZE + GAP)
        + 15
    )

    svg.append(
        f'''
<text x="{LEFT}"
      y="{legend_y}"
      font-family="ui-sans-serif, system-ui, sans-serif"
      font-size="11"
      fill="#8b949e">
  Less
</text>
'''
    )

    legend_x = LEFT + 32

    for i, color in enumerate(PALETTE):

        svg.append(
            f'''
<rect
  x="{legend_x + i * 18}"
  y="{legend_y - 10}"
  width="12"
  height="12"
  rx="3"
  fill="{color}"
/>
'''
        )

    svg.append(
        f'''
<text x="{legend_x + len(PALETTE) * 18 + 5}"
      y="{legend_y}"
      font-family="ui-sans-serif, system-ui, sans-serif"
      font-size="11"
      fill="#8b949e">
  More
</text>
'''
    )

    # Statistics footer.
    footer_y = height - 15

    total = data.get(
        "total_contributions",
        0
    )

    current_streak = data.get(
        "current_streak",
        0
    )

    longest_streak = data.get(
        "longest_streak",
        0
    )

    stats = (
        f"{total:,} contributions in the last year"
        f"  •  current streak: {current_streak} days"
        f"  •  best streak: {longest_streak} days"
    )

    svg.append(
        f'''
<text x="{LEFT}"
      y="{footer_y}"
      font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
      font-size="11"
      fill="#8b949e">
  {stats}
</text>
'''
    )

    svg.append("</svg>")

    return "\n".join(svg)


def main():
    data = load_data()

    svg = generate_svg(data)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(svg)

    print(
        f"Generated: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
