#!/usr/bin/env python3

import json
import os
from datetime import datetime, timedelta


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


# ---------------------------------------------------------
# DESIGN
# ---------------------------------------------------------

BG = "#0d1117"
TEXT = "#f0f6fc"
MUTED = "#8b949e"

PALETTE = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
]

CELL = 12
GAP = 3

LEFT = 44
TOP = 48

WEEKS = 53
ROWS = 7

GRID_WIDTH = WEEKS * (CELL + GAP) - GAP
GRID_HEIGHT = ROWS * (CELL + GAP) - GAP

WIDTH = LEFT + GRID_WIDTH + 20
HEIGHT = 220


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def level_for(day):
    try:
        return max(0, min(int(day.get("level", 0)), 4))
    except (TypeError, ValueError):
        return 0


def escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generate_svg(data):

    days = data.get("days", [])

    if not days:
        raise RuntimeError("No contribution data found.")

    # -----------------------------------------------------
    # Build lookup by date
    # -----------------------------------------------------

    day_lookup = {
        item["date"]: item
        for item in days
    }

    # Latest contribution date.
    last_date = datetime.strptime(
        days[-1]["date"],
        "%Y-%m-%d"
    ).date()

    # Find the Sunday at the beginning of the final week.
    final_sunday = (
        last_date
        - timedelta(days=(last_date.weekday() + 1) % 7)
    )

    # 53 weeks backwards.
    first_sunday = (
        final_sunday
        - timedelta(weeks=WEEKS - 1)
    )

    svg = []

    svg.append(
        f'''<svg xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">
'''
    )

    # -----------------------------------------------------
    # Background
    # -----------------------------------------------------

    svg.append(
        f'''
<rect
    x="0"
    y="0"
    width="{WIDTH}"
    height="{HEIGHT}"
    rx="14"
    fill="{BG}"
/>
'''
    )

    # -----------------------------------------------------
    # Terminal header
    # -----------------------------------------------------

    svg.append(
        f'''
<text
    x="20"
    y="27"
    font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    font-size="13"
    font-weight="600"
    fill="{TEXT}">
    pranav@github ~ $ ./contributions.sh
</text>
'''
    )

    svg.append(
        f'''
<circle
    cx="{WIDTH - 50}"
    cy="23"
    r="4"
    fill="{TEXT}"
    opacity="0.9"
/>

<circle
    cx="{WIDTH - 35}"
    cy="23"
    r="4"
    fill="#39d353"
    opacity="0.9"
/>

<circle
    cx="{WIDTH - 20}"
    cy="23"
    r="4"
    fill="#26a641"
    opacity="0.9"
/>
'''
    )

    # -----------------------------------------------------
    # Animation
    # -----------------------------------------------------

    svg.append(
        '''
<defs>

<style>
.cell {
    opacity: 0;
    transform-box: fill-box;
    transform-origin: center;
    animation: appear 0.38s cubic-bezier(.2,.7,.2,1) forwards;
}

@keyframes appear {
    0% {
        opacity: 0;
        transform: translateY(-7px) scale(0.72);
    }

    70% {
        opacity: 1;
        transform: translateY(1px) scale(1.04);
    }

    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

</style>

</defs>
'''
    )

    # -----------------------------------------------------
    # Month labels
    # -----------------------------------------------------

    last_month = None

    for week in range(WEEKS):

        week_date = (
            first_sunday
            + timedelta(weeks=week)
        )

        month = week_date.strftime("%b")

        if month != last_month:

            x = (
                LEFT
                + week * (CELL + GAP)
            )

            svg.append(
                f'''
<text
    x="{x}"
    y="43"
    font-family="ui-sans-serif, system-ui, sans-serif"
    font-size="9"
    fill="{MUTED}">
    {month}
</text>
'''
            )

            last_month = month

    # -----------------------------------------------------
    # Contribution grid
    # -----------------------------------------------------

    for week in range(WEEKS):

        for row in range(ROWS):

            current_date = (
                first_sunday
                + timedelta(weeks=week, days=row)
            )

            date_string = current_date.isoformat()

            day = day_lookup.get(
                date_string,
                {
                    "count": 0,
                    "level": 0
                }
            )

            level = level_for(day)

            color = PALETTE[level]

            x = (
                LEFT
                + week * (CELL + GAP)
            )

            y = (
                TOP
                + row * (CELL + GAP)
            )

            # Diagonal reveal:
            # left → right + top → bottom
            delay = (
                week * 0.018
                + row * 0.035
            )

            count = day.get("count", 0)

            if count == 1:
                contribution_word = "contribution"
            else:
                contribution_word = "contributions"

            tooltip = (
                f"{escape(date_string)}: "
                f"{count} {contribution_word}"
            )

            svg.append(
                f'''
<rect
    class="cell"
    x="{x}"
    y="{y}"
    width="{CELL}"
    height="{CELL}"
    rx="3"
    fill="{color}"
    style="animation-delay:{delay:.3f}s">
    <title>{tooltip}</title>
</rect>
'''
            )

    # -----------------------------------------------------
    # Day labels
    # -----------------------------------------------------

    labels = [
        ("Mon", 1),
        ("Wed", 3),
        ("Fri", 5),
    ]

    for label, row in labels:

        y = (
            TOP
            + row * (CELL + GAP)
            + 9
        )

        svg.append(
            f'''
<text
    x="8"
    y="{y}"
    font-family="ui-sans-serif, system-ui, sans-serif"
    font-size="8"
    fill="{MUTED}">
    {label}
</text>
'''
        )

    # -----------------------------------------------------
    # Legend
    # -----------------------------------------------------

    legend_y = 171

    svg.append(
        f'''
<text
    x="{LEFT}"
    y="{legend_y}"
    font-family="ui-sans-serif, system-ui, sans-serif"
    font-size="9"
    fill="{MUTED}">
    Less
</text>
'''
    )

    legend_x = LEFT + 28

    for i, color in enumerate(PALETTE):

        svg.append(
            f'''
<rect
    x="{legend_x + i * 17}"
    y="{legend_y - 9}"
    width="11"
    height="11"
    rx="3"
    fill="{color}"
/>
'''
        )

    svg.append(
        f'''
<text
    x="{legend_x + 90}"
    y="{legend_y}"
    font-family="ui-sans-serif, system-ui, sans-serif"
    font-size="9"
    fill="{MUTED}">
    More
</text>
'''
    )

    # -----------------------------------------------------
    # Stats
    # -----------------------------------------------------

    total = int(
        data.get("total_contributions", 0)
    )

    current_streak = int(
        data.get("current_streak", 0)
    )

    longest_streak = int(
        data.get("longest_streak", 0)
    )

    stats = (
        f"{total:,} contributions"
        f"   •   {current_streak} day current streak"
        f"   •   {longest_streak} day best streak"
    )

    svg.append(
        f'''
<text
    x="20"
    y="201"
    font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    font-size="10"
    fill="{MUTED}">
    {escape(stats)}
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
    ) as f:
        f.write(svg)

    print(
        f"Generated {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
