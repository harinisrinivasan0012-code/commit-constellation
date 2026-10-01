"""Summary statistics and a playful 'coder persona'."""

from collections import Counter
from datetime import timedelta
from statistics import median
from typing import Dict, List

from .gitdata import Commit


def persona(median_hour: float) -> str:
    if 5 <= median_hour < 11:
        return "Early Bird"
    if 11 <= median_hour < 17:
        return "Daylight Coder"
    if 17 <= median_hour < 22:
        return "Evening Builder"
    return "Night Owl"


def longest_streak(commits: List[Commit]) -> int:
    days = sorted({c.when.date() for c in commits})
    best = run = 0
    prev = None
    for d in days:
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return best


def summarize(commits: List[Commit]) -> Dict:
    if not commits:
        raise ValueError("No commits to summarize")
    hours = [c.when.hour + c.when.minute / 60 for c in commits]
    busiest_hour = Counter(c.when.hour for c in commits).most_common(1)[0][0]
    biggest = max(commits, key=lambda c: c.size)
    return {
        "total": len(commits),
        "repos": len({c.repo for c in commits}),
        "busiest_hour": busiest_hour,
        "longest_streak": longest_streak(commits),
        "persona": persona(median(hours)),
        "biggest_commit": biggest,
    }
