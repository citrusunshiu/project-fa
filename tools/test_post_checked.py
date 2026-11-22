# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Shows that post_checked.py runs the command only when the public-text check passes.

A fake gh on PATH stands in for the real one, so nothing here can post anything.
"""
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

TOOL = pathlib.Path(__file__).resolve().parent / "post_checked.py"
# Built at run time: the check also scans this file, so the term must not appear in it whole.
TERM = "-".join(["planted", "private", "term"])


class PostChecked(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        self.marker = self.dir / "posted"
        bin_dir = self.dir / "bin"
        bin_dir.mkdir()
        for name in ("gh", "notgh"):  # notgh would post too, if anything but gh were allowed
            fake = bin_dir / name
            fake.write_text(f"#!/bin/sh\ntouch {self.marker}\n")
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.env = dict(os.environ, PUBLIC_TEXT_DENYLIST=TERM, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
        self.body = self.text("Clean body.\n")

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *args, env=None):
        return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, env=env or self.env)

    def text(self, body, name="body.md"):
        path = self.dir / name
        path.write_text(body)
        return str(path)

    def refused(self, *command, files=None):
        result = self.run_tool(*(files or [self.body]), "--", *command)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("nothing was posted", result.stderr)
        self.assertFalse(self.marker.exists())
        return result

    def test_clean_text_is_posted(self):
        result = self.run_tool(self.body, "--", "gh", "issue", "create", "--title", "Clean", "--body-file", self.body)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.marker.exists())

    def test_a_failing_body_posts_nothing(self):
        bad = self.text(f"Mentions {TERM} here.\n", "bad.md")
        result = self.refused("gh", "issue", "create", "--title", "Clean", "--body-file", bad, files=[bad])
        self.assertIn("private term", result.stdout)

    def test_a_failing_title_posts_nothing(self):
        for flag in (["--title", f"about {TERM}"], ["-t", TERM], [f"--title={TERM}"]):
            with self.subTest(flag=flag):
                result = self.refused("gh", "pr", "create", *flag, "--body-file", self.body)
                self.assertIn("private term", result.stdout)
        result = self.refused("gh", "pr", "merge", "7", "--squash", "--subject", TERM, "--body-file", self.body)
        self.assertIn("private term", result.stdout)
        for flag in ([f"-t{TERM}"], [f"-t={TERM}"]):  # attached short values aren't allowed at all
            with self.subTest(attached=flag):
                self.refused("gh", "pr", "create", *flag, "--body-file", self.body)

    def test_a_check_that_errors_posts_nothing(self):
        undecodable = self.dir / "binary.md"
        undecodable.write_bytes(b"\xff\xfe\x00 not utf-8 \xc3\x28")
        result = self.run_tool(str(undecodable), "--", "gh", "issue", "create", "--body-file", str(undecodable))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("private term", result.stdout)
        self.assertFalse(self.marker.exists())

    def test_text_it_cannot_check_is_refused(self):
        other = self.text("Not passed to the check.\n", "other.md")
        for extra in (["--body", "inline"], ["-b", "inline"], ["--body=inline"], ["-binline"],
                      ["--body-file", other], ["-F", other], [f"--body-file={other}"],
                      ["-dtTitle"], ["-dt", "Title"], ["-db", "inline"], ["-dF", other], ["-fbinline"], [f"-ft{TERM}"],
                      ["--fill"], ["--fill-first"], ["--fill-verbose"], ["-f"], ["--web"], ["--draft=true"]):
            with self.subTest(extra=extra):
                self.refused("gh", "pr", "create", "--title", "Clean", *extra)
        for extra in (["--comment", "inline"], ["-c", "inline"]):
            with self.subTest(close=extra):
                self.refused("gh", "issue", "close", "3", *extra)

    def test_review_switches_are_allowed(self):
        for switch in ("--comment", "-c", "--approve", "-a", "--request-changes", "-r"):
            with self.subTest(switch=switch):
                self.marker.unlink(missing_ok=True)
                result = self.run_tool(self.body, "--", "gh", "pr", "review", "7", switch, "--body-file", self.body)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(self.marker.exists())
        for switch in ("--comment=inline", "--approve=yes"):  # a switch never carries text
            with self.subTest(attached=switch):
                self.marker.unlink(missing_ok=True)
                self.refused("gh", "pr", "review", "7", switch, "--body-file", self.body)

    def test_gh_api_takes_text_only_from_a_checked_input(self):
        other = self.text("Not passed to the check.\n", "other.md")
        for extra in (["-f", "body=inline"], ["-F", "body=inline"], ["--field", "body=inline"],
                      ["--raw-field=body=inline"], ["--input", other]):
            with self.subTest(extra=extra):
                self.refused("gh", "api", "repos/o/r/issues", *extra)
        result = self.run_tool(self.body, "--", "gh", "api", "repos/o/r/issues", "--input", self.body)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.marker.exists())

    def test_only_supported_gh_commands_run(self):
        for command in (["notgh", "issue", "create", "--body-file", self.body],
                        ["env", "gh", "api", "repos/o/r/issues", "-f", "body=inline"], ["sh", "-c", "gh issue create"],
                        ["gh", "release", "create", "v1", "--notes", "inline"], ["gh", "repo", "edit", "--description", "x"]):
            with self.subTest(command=command):
                self.refused(*command)

    def test_a_checked_body_file_is_allowed(self):
        for extra in (["--body-file", self.body], ["-F", self.body], [f"--body-file={self.body}"]):
            with self.subTest(extra=extra):
                self.marker.unlink(missing_ok=True)
                result = self.run_tool(self.body, "--", "gh", "issue", "comment", "3", *extra)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(self.marker.exists())

    def test_a_missing_file_or_command_posts_nothing(self):
        missing = self.run_tool(str(self.dir / "absent.md"), "--", "gh", "issue", "create", "--body-file", self.body)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("is not a file", missing.stderr)
        self.assertEqual(self.run_tool(self.body, "--").returncode, 2)
        self.assertEqual(self.run_tool(self.body, "gh", "issue", "create").returncode, 2)
        self.assertFalse(self.marker.exists())

    def test_gh_that_isnt_found_fails_cleanly(self):
        no_gh = self.dir / "no-gh"  # git, which the check needs, but no gh
        no_gh.mkdir()
        (no_gh / "git").symlink_to(shutil.which("git"))
        env = dict(self.env, PATH=str(no_gh))
        result = self.run_tool(self.body, "--", "gh", "issue", "create", "--body-file", self.body, env=env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("couldn't run", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
