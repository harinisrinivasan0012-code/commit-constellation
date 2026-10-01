"""Render commits as an SVG star map.

x-axis  -> time (oldest on the left)
y-axis  -> hour of day (midnight at the top)
size    -> lines changed in the commit
colour  -> repository; commits of one repo made close together are joined
           into a "constellation".
"""

import math
import random
from collections import Counter
from typing import List
from xml.sax.saxutils import escape

from .gitdata import Commit
from .stats import summarize

PALETTE = ["#7dd3fc", "#f9a8d4", "#fde68a", "#86efac",
           "#c4b5fd", "#fdba74", "#5eead4", "#fca5a5"]
LINK_GAP_SECONDS = 3 * 24 * 3600


def render_svg(commits: List[Commit], width: int = 1200, height: int = 720,
               title: str = "My Commit Constellation") -> str:
    if not commits:
        raise ValueError("No commits to render")
    commits = sorted(commits, key=lambda c: c.when)
    info = summarize(commits)

    t0, t1 = commits[0].when.timestamp(), commits[-1].when.timestamp()
    span = max(t1 - t0, 1.0)
    ml, mr, mt, mb = 80, 40, 120, 90
    pw, ph = width - ml - mr, height - mt - mb

    ranking = [r for r, _ in Counter(c.repo for c in commits).most_common()]
    colour = {r: PALETTE[i % len(PALETTE)] for i, r in enumerate(ranking)}

    def pos(c: Commit):
        x = ml + (c.when.timestamp() - t0) / span * pw
        y = mt + (c.when.hour + c.when.minute / 60) / 24 * ph
        return x, y

    rng = random.Random(7)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
        '<defs>'
        '<radialGradient id="bg" cx="50%" cy="40%" r="80%">'
        '<stop offset="0%" stop-color="#1b1f4b"/><stop offset="100%" stop-color="#05060f"/>'
        '</radialGradient>'
        '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%">'
        '<feGaussianBlur stdDeviation="2.5" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter></defs>',
        f'<rect width="{width}" height="{height}" rx="18" fill="url(#bg)"/>',
    ]

    # background dust
    for _ in range(150):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        r, o = rng.uniform(0.3, 1.2), rng.uniform(0.15, 0.6)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#fff" opacity="{o:.2f}"/>')

    # hour grid
    for h in (0, 6, 12, 18, 24):
        y = mt + h / 24 * ph
        out.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{width - mr}" y2="{y:.1f}" '
                   f'stroke="#fff" stroke-opacity="0.08" stroke-dasharray="4 6"/>')
        if h < 24:
            out.append(f'<text x="{ml - 12}" y="{y + 4:.1f}" text-anchor="end" '
                       f'fill="#94a3b8" font-size="12">{h:02d}:00</text>')

    # constellation lines
    by_repo = {}
    for c in commits:
        by_repo.setdefault(c.repo, []).append(c)
    for repo, items in by_repo.items():
        for a, b in zip(items, items[1:]):
            if b.when.timestamp() - a.when.timestamp() <= LINK_GAP_SECONDS:
                (x1, y1), (x2, y2) = pos(a), pos(b)
                out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                           f'stroke="{colour[repo]}" stroke-opacity="0.35" stroke-width="1"/>')

    # stars
    for c in commits:
        x, y = pos(c)
        r = min(2 + math.sqrt(c.size) * 0.45, 9)
        tip = escape(f"{c.repo} · {c.when:%Y-%m-%d %H:%M} · +{c.additions}/-{c.deletions}\n{c.message}")
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{colour[c.repo]}" '
                   f'filter="url(#glow)"><title>{tip}</title></circle>')

    # header
    out.append(f'<text x="{ml}" y="48" fill="#f8fafc" font-size="28" font-weight="700">{escape(title)}</text>')
    sub = (f'{info["total"]} commits · {info["repos"]} repos · '
           f'peak hour {info["busiest_hour"]:02d}:00 · best streak {info["longest_streak"]} days')
    out.append(f'<text x="{ml}" y="76" fill="#cbd5e1" font-size="15">{sub}</text>')
    out.append(f'<text x="{width - mr}" y="48" text-anchor="end" fill="#fde68a" '
               f'font-size="22" font-weight="600">✦ {info["persona"]}</text>')
    out.append(f'<text x="{width - mr}" y="76" text-anchor="end" fill="#94a3b8" font-size="13">'
               f'{commits[0].when:%b %Y} → {commits[-1].when:%b %Y}</text>')

    # legend
    lx = ml
    ly = height - 40
    for repo in ranking[:6]:
        out.append(f'<circle cx="{lx}" cy="{ly}" r="5" fill="{colour[repo]}"/>')
        label = escape(repo if len(repo) <= 18 else repo[:17] + "…")
        out.append(f'<text x="{lx + 12}" y="{ly + 4}" fill="#cbd5e1" font-size="13">{label}</text>')
        lx += 30 + 8 * len(label)
    out.append(f'<text x="{width - mr}" y="{ly + 4}" text-anchor="end" fill="#64748b" font-size="12">'
               f'x = time · y = hour of day · size = lines changed</text>')
    out.append('</svg>')
    return "\n".join(out)
