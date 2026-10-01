import argparse
import sys

from . import __version__
from .demo import demo_commits
from .gitdata import collect
from .render import render_svg


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="commit-constellation",
        description="Turn your git history into a glowing star map (SVG).")
    p.add_argument("paths", nargs="*", default=["."],
                   help="repo(s) or folder(s) containing repos (default: .)")
    p.add_argument("-o", "--output", default="constellation.svg")
    p.add_argument("--author", help="only commits by this author (name or email)")
    p.add_argument("--since", help='e.g. "1 year ago" or 2026-01-01')
    p.add_argument("--title", default="My Commit Constellation")
    p.add_argument("--demo", action="store_true", help="use generated sample data")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)

    commits = demo_commits() if args.demo else collect(args.paths, args.author, args.since)
    if not commits:
        print("No commits found. Check the path/author, or try --demo.", file=sys.stderr)
        return 1

    svg = render_svg(commits, title=args.title)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✦ Wrote {args.output} ({len(commits)} commits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
