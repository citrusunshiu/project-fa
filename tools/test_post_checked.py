# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Shows that post_checked.py runs the command only when the public-text check passes."""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

TOOL = pathlib.Path(__file__).resolve().parent / "post_checked.py"
# Built at run time: the check also scans this file, so the term must not appear in it whole.
TERM = "-".join(["planted", "private", "term"])


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True,
                          env=dict(os.environ, PUBLIC_TEXT_DENYLIST=TERM))


class PostChecked(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        self.marker = self.dir / "posted"
        self.post = [sys.executable, "-c", f"open({str(self.marker)!r}, 'w').close()"]

    def tearDown(self):
        self.tmp.cleanup()

    def text(self, body: str) -> str:
        path = self.dir / "body.md"
        path.write_text(body)
        return str(path)

    def test_clean_text_is_posted(self):
        result = run(self.text("A plain description.\n"), "--", *self.post)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.marker.exists())

    def test_a_failing_body_posts_nothing(self):
        result = run(self.text(f"Mentions {TERM} here.\n"), "--", *self.post)
        self.assertEqual(result.returncode, 1)
        self.assertIn("private term", result.stdout)
        self.assertIn("nothing was posted", result.stderr)
        self.assertFalse(self.marker.exists())

    def test_a_failing_title_posts_nothing_in_any_form(self):
        for flag in (["--title", f"about {TERM}"], ["-t", TERM], [f"--title={TERM}"], [f"-t{TERM}"], [f"-t={TERM}"]):
            with self.subTest(flag=flag):
                result = run(self.text("Clean body.\n"), "--", *self.post, *flag)
                self.assertEqual(result.returncode, 1)
                self.assertIn("private term", result.stdout)
                self.assertFalse(self.marker.exists())

    def test_a_check_that_errors_posts_nothing(self):
        undecodable = self.dir / "binary.md"
        undecodable.write_bytes(b"\xff\xfe\x00 not utf-8 \xc3\x28")
        result = run(str(undecodable), "--", *self.post)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("private term", result.stdout)
        self.assertFalse(self.marker.exists())

    def test_text_it_cannot_check_is_refused(self):
        body = self.text("Clean body.\n")
        other = self.dir / "other.md"
        other.write_text("Not passed to the check.\n")
        cases = [["--body", "inline"], ["-b", "inline"], ["--body=inline"], ["-binline"],
                 ["--body-file", str(other)], ["-F", str(other)], [f"--body-file={other}"]]
        for extra in cases:
            with self.subTest(extra=extra):
                result = run(body, "--", *self.post, *extra)
                self.assertEqual(result.returncode, 1)
                self.assertIn("nothing was posted", result.stderr)
                self.assertFalse(self.marker.exists())
        for extra in (["-f", "body=inline"], ["-F", "body=inline"], ["--field", "body=inline"], ["--raw-field=body=inline"],
                      ["--input", str(other)]):
            with self.subTest(api=extra):
                result = run(body, "--", "gh", "api", "repos/o/r/issues", *extra)
                self.assertEqual(result.returncode, 1)
                self.assertIn("nothing was posted", result.stderr)

    def test_a_checked_body_file_is_allowed(self):
        body = self.text("Clean body.\n")
        for extra in (["--body-file", body], ["-F", body], [f"--body-file={body}"]):
            with self.subTest(extra=extra):
                self.marker.unlink(missing_ok=True)
                result = run(body, "--", *self.post, *extra)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(self.marker.exists())

    def test_a_missing_file_or_command_posts_nothing(self):
        missing = run(str(self.dir / "absent.md"), "--", *self.post)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("is not a file", missing.stderr)
        self.assertEqual(run(self.text("Clean.\n"), "--").returncode, 2)
        self.assertEqual(run(self.text("Clean.\n"), *self.post).returncode, 2)
        self.assertFalse(self.marker.exists())

    def test_a_command_that_isnt_found_fails_cleanly(self):
        result = run(self.text("Clean.\n"), "--", "no-such-command-for-post-checked")
        self.assertEqual(result.returncode, 1)
        self.assertIn("couldn't run", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

if __name__ == "__main__":
    unittest.main()
