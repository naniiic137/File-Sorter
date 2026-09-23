"""Unit tests. Only temporary folders created by the tests themselves are touched."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import (OTHER, UNDO_LOG_NAME, apply_moves, category_for,  # noqa: E402
                  plan_moves, undo, unique_destination)


class CategoryTests(unittest.TestCase):
    def test_known_extensions(self):
        self.assertEqual(category_for("holiday.jpg"), "Images")
        self.assertEqual(category_for("clip.mp4"), "Video")
        self.assertEqual(category_for("song.mp3"), "Audio")
        self.assertEqual(category_for("cv.pdf"), "Documents")
        self.assertEqual(category_for("budget.xlsx"), "Spreadsheets")
        self.assertEqual(category_for("backup.zip"), "Archives")
        self.assertEqual(category_for("script.py"), "Code")
        self.assertEqual(category_for("setup.exe"), "Apps")

    def test_case_insensitive(self):
        self.assertEqual(category_for("PHOTO.JPG"), "Images")
        self.assertEqual(category_for("Report.PdF"), "Documents")

    def test_unknown_or_missing_extension(self):
        self.assertEqual(category_for("data.xyz"), OTHER)
        self.assertEqual(category_for("Makefile"), OTHER)

    def test_only_last_extension_counts(self):
        self.assertEqual(category_for("archive.tar.gz"), "Archives")
        self.assertEqual(category_for("notes.txt.exe"), "Apps")


class FolderTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for name in ["a.jpg", "b.PNG", "song.mp3", "notes.txt", "weird.xyz", ".hidden.txt"]:
            (self.root / name).write_text(name)
        (self.root / "project").mkdir()
        (self.root / "project" / "inner.py").write_text("print('hi')")

    def tearDown(self):
        self._tmp.cleanup()

    def test_plan_skips_folders_and_hidden_files(self):
        planned = {src.name: dst.relative_to(self.root.resolve()).as_posix()
                   for src, dst in plan_moves(self.root)}
        self.assertEqual(planned, {
            "a.jpg": "Images/a.jpg",
            "b.PNG": "Images/b.PNG",
            "song.mp3": "Audio/song.mp3",
            "notes.txt": "Documents/notes.txt",
            "weird.xyz": "Other/weird.xyz",
        })

    def test_plan_does_not_touch_disk(self):
        before = sorted(p.name for p in self.root.iterdir())
        plan_moves(self.root)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), before)

    def test_plan_skips_the_script_itself(self):
        script = self.root / "main.py"
        script.write_text("# sorter")
        names = [src.name for src, _ in plan_moves(self.root, script_path=script)]
        self.assertNotIn("main.py", names)

    def test_collision_gets_a_new_name(self):
        (self.root / "Images").mkdir()
        (self.root / "Images" / "a.jpg").write_text("already here")
        dest = unique_destination(self.root / "Images" / "a.jpg")
        self.assertEqual(dest.name, "a (1).jpg")

    def test_apply_then_undo_restores_everything(self):
        before = {p.name: p.read_text() for p in self.root.iterdir() if p.is_file()}
        apply_moves(self.root, plan_moves(self.root))
        self.assertTrue((self.root / "Images" / "a.jpg").exists())
        self.assertTrue((self.root / "project" / "inner.py").exists())
        self.assertTrue((self.root / UNDO_LOG_NAME).exists())

        restored, skipped = undo(self.root)
        self.assertEqual((len(restored), len(skipped)), (5, 0))
        after = {p.name: p.read_text() for p in self.root.iterdir() if p.is_file()}
        self.assertEqual(after, before)
        self.assertFalse((self.root / "Images").exists())
        self.assertTrue((self.root / "project").is_dir())


if __name__ == "__main__":
    unittest.main()
