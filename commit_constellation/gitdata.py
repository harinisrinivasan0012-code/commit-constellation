"""Read commit data from local git repositories using only the git CLI."""

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional


@dataclass
class Commit:
    repo: str
    sha: str
    when: datetime
    message: str
    additions: int = 0
    deletions: int = 0

    @property
    def size(self) -> int:
        return self.additions + self.deletions


def find_repos(root: str, max_depth: int = 3) -> List[str]:
    """Return git repositories at or below `root` (up to `max_depth` levels)."""
    root = os.path.abspath(root)
    if os.path.isdir(os.path.join(root, ".git")):
        return [root]
    found = []
    base_depth = root.rstrip(os.sep).count(os.sep)
    for current, dirs, _ in os.walk(root):
        depth = current.count(os.sep) - base_depth
        if ".git" in dirs:
            found.append(current)
            dirs[:] = []  # don't descend into a repo
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        if depth >= max_depth:
            dirs[:] = []
    return sorted(found)


def parse_log(output: str, repo_name: str) -> List[Commit]:
    """Parse `git log --numstat` output produced with our custom format."""
    commits: List[Commit] = []
    current: Optional[Commit] = None
    for line in output.splitlines():
        if line.startswith("@@"):
            sha, iso, subject = line[2:].split("|", 2)
            current = Commit(repo_name, sha, datetime.fromisoformat(iso), subject)
            commits.append(current)
        elif line.strip() and current is not None:
            parts = line.split("\t")
            if len(parts) >= 3:
                add, dele = parts[0], parts[1]
                current.additions += int(add) if add.isdigit() else 0
                current.deletions += int(dele) if dele.isdigit() else 0
    return commits


def read_commits(repo_path: str, author: Optional[str] = None,
                 since: Optional[str] = None) -> List[Commit]:
    cmd = ["git", "-C", repo_path, "log", "--no-merges", "--numstat",
           "--pretty=format:@@%H|%aI|%s"]
    if author:
        cmd.append(f"--author={author}")
    if since:
        cmd.append(f"--since={since}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return parse_log(result.stdout, os.path.basename(repo_path.rstrip(os.sep)))


def collect(paths: Iterable[str], author: Optional[str] = None,
            since: Optional[str] = None) -> List[Commit]:
    commits: List[Commit] = []
    for path in paths:
        for repo in find_repos(path):
            commits.extend(read_commits(repo, author, since))
    return sorted(commits, key=lambda c: c.when)
