"""Synthetic data so the tool works before you point it at real repos."""

import random
from datetime import datetime, timedelta
from typing import List

from .gitdata import Commit

REPOS = {"portfolio-site": 0.4, "ml-experiments": 0.35, "leetcode-journey": 0.25}
MESSAGES = ["add feature", "fix bug", "refactor", "update docs", "tweak styles",
            "add tests", "initial commit", "improve performance"]


def demo_commits(n: int = 220, seed: int = 12) -> List[Commit]:
    rng = random.Random(seed)
    start = datetime(2025, 10, 1, 9, 0)
    names, weights = list(REPOS), list(REPOS.values())
    commits = []
    for i in range(n):
        day = start + timedelta(days=int(rng.triangular(0, 360, 300)))
        hour = int(rng.gauss(22, 4)) % 24  # a mild night-owl bias
        when = day.replace(hour=hour, minute=rng.randint(0, 59))
        add = int(rng.expovariate(1 / 40)) + 1
        commits.append(Commit(rng.choices(names, weights)[0], f"{i:040x}", when,
                              rng.choice(MESSAGES), add, int(add * rng.random())))
    return sorted(commits, key=lambda c: c.when)
