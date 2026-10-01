import os
import subprocess
import tempfile
import unittest
from datetime import datetime

from commit_constellation.demo import demo_commits
from commit_constellation.gitdata import Commit, parse_log, read_commits
from commit_constellation.render import render_svg
from commit_constellation.stats import longest_streak, persona, summarize


class TestStats(unittest.TestCase):
    def test_persona(self):
        self.assertEqual(persona(7), "Early Bird")
        self.assertEqual(persona(14), "Daylight Coder")
        self.assertEqual(persona(19), "Evening Builder")
        self.assertEqual(persona(2), "Night Owl")

    def test_streak(self):
        cs = [Commit("r", "x", datetime(2026, 1, d, 10), "m") for d in (1, 2, 3, 7, 8)]
        self.assertEqual(longest_streak(cs), 3)

    def test_summary(self):
        s = summarize(demo_commits())
        self.assertEqual(s["total"], 220)
        self.assertEqual(s["repos"], 3)


class TestParse(unittest.TestCase):
    def test_parse_log_handles_pipes_and_binary(self):
        raw = ("@@abc|2026-01-02T10:00:00+05:30|fix a | b\n\n"
               "3\t1\tfile.py\n-\t-\timg.png\n")
        c = parse_log(raw, "repo")[0]
        self.assertEqual(c.message, "fix a | b")
        self.assertEqual((c.additions, c.deletions), (3, 1))

    def test_real_repo(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
            run = lambda *a: subprocess.run(["git", "-C", d, *a], check=True,
                                            capture_output=True, env=env)
            run("init", "-q")
            with open(os.path.join(d, "a.txt"), "w") as f:
                f.write("hello\nworld\n")
            run("add", ".")
            run("commit", "-qm", "first")
            commits = read_commits(d)
            self.assertEqual(len(commits), 1)
            self.assertEqual(commits[0].additions, 2)


class TestRender(unittest.TestCase):
    def test_svg(self):
        svg = render_svg(demo_commits(), title="A & B")
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("A &amp; B", svg)

    def test_empty(self):
        with self.assertRaises(ValueError):
            render_svg([])


if __name__ == "__main__":
    unittest.main()
