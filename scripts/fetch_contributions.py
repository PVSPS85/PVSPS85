#!/usr/bin/env python3

import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup


USERNAME = os.environ.get("GH_PROFILE_USER", "PVSPS85")

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "contributions.json"
)

URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_contributions():
    response = requests.get(
        URL,
        headers={
            "User-Agent": "PVPSP85-github-profile"
        },
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")

    if not cells:
        print("ERROR: GitHub contribution cells were not found.")
        sys.exit(1)

    days = []

    for cell in cells:
        date = cell.get("data-date")

        if not date:
            continue

        cell_id = cell.get("id")

        tooltip = ""

        if cell_id:
            tooltip_element = soup.find(
                "tool-tip",
                attrs={"for": cell_id}
            )

            if tooltip_element:
                tooltip = tooltip_element.get_text(
                    " ",
                    strip=True
                )

        if re.search(
            r"no contributions",
            tooltip,
            re.IGNORECASE
        ):
            count = 0
        else:
            match = re.search(
                r"(\d+)",
                tooltip
            )

            count = int(match.group(1)) if match else 0

        level = int(
            cell.get("data-level") or 0
        )

        days.append({
            "date": date,
            "count": count,
            "level": level
        })

    days.sort(
        key=lambda item: item["date"]
    )

    return days


def calculate_streaks(days):
    current = 0
    longest = 0
    running = 0

    for day in reversed(days):
        if day["count"] > 0:
            current += 1
        else:
            break

    for day in days:
        if day["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    return current, longest


def build_data(days):
    total = sum(
        day["count"]
        for day in days
    )

    active_days = sum(
        1
        for day in days
        if day["count"] > 0
    )

    best_day = max(
        days,
        key=lambda day: day["count"]
    )

    current_streak, longest_streak = calculate_streaks(days)

    monthly = {}

    for day in days:
        month = day["date"][:7]

        monthly[month] = (
            monthly.get(month, 0)
            + day["count"]
        )

    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),

        "range": {
            "start": days[0]["date"],
            "end": days[-1]["date"]
        },

        "total_contributions": total,

        "active_days": active_days,

        "average_per_active_day": (
            round(total / active_days, 1)
            if active_days
            else 0
        ),

        "current_streak": current_streak,

        "longest_streak": longest_streak,

        "best_day": {
            "date": best_day["date"],
            "count": best_day["count"]
        },

        "monthly": [
            {
                "month": month,
                "total": total_count
            }
            for month, total_count
            in sorted(monthly.items())
        ],

        "days": days
    }


def main():
    print(
        f"Fetching contributions for {USERNAME}..."
    )

    days = fetch_contributions()

    data = build_data(days)

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=2
        )

    print(
        f"Saved {OUTPUT_FILE}"
    )

    print(
        f"Total contributions: "
        f"{data['total_contributions']}"
    )

    print(
        f"Current streak: "
        f"{data['current_streak']} days"
    )

    print(
        f"Longest streak: "
        f"{data['longest_streak']} days"
    )


if __name__ == "__main__":
    main()
