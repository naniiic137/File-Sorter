"""File Sorter: tidy a folder by moving its files into category sub-folders.

Safe by default:
  * it only touches the folder you name on the command line,
  * it never moves folders, hidden/system files or this script,
  * without --apply it only prints what it *would* do (dry run),
  * every real move is written to an undo log so --undo can put files back.

Usage examples:
    python main.py "C:/Users/me/Downloads"            # dry run: show the plan
    python main.py "C:/Users/me/Downloads" --apply    # really move the files
    python main.py "C:/Users/me/Downloads" --undo     # put them back
"""

import argparse
import json
import shutil
import stat
import sys
from pathlib import Path

UNDO_LOG_NAME = ".file-sorter-undo.json"

CATEGORIES = {
    "Images": ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "tif", "tiff", "heic"],
    "Video": ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v"],
    "Audio": ["mp3", "wav", "m4a", "flac", "aac", "ogg", "wma"],
    "Documents": ["pdf", "doc", "docx", "odt", "rtf", "txt", "md", "ppt", "pptx", "odp", "epub"],
    "Spreadsheets": ["xls", "xlsx", "ods", "csv", "tsv"],
    "Archives": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso"],
    "Code": ["py", "js", "ts", "html", "css", "json", "xml", "yml", "yaml", "java", "c", "cpp",
             "h", "cs", "php", "sql", "sh", "bat", "ps1", "ipynb", "pas", "lpr"],
    "Apps": ["exe", "msi", "apk", "jar", "appimage", "deb", "dmg"],
}
OTHER = "Other"

# extension (lower case, without the dot) -> category name
EXTENSION_TO_CATEGORY = {
    ext: category for category, extensions in CATEGORIES.items() for ext in extensions
}


def category_for(filename):
    """Return the category folder name for a file name (case-insensitive)."""
    suffix = Path(filename).suffix.lower().lstrip(".")
    return EXTENSION_TO_CATEGORY.get(suffix, OTHER)


def is_hidden(path):
    """True for dot-files, Office lock files and Windows hidden/system files."""
    if path.name.startswith((".", "~$")):
        return True
    attributes = getattr(path.stat(), "st_file_attributes", 0)  # 0 outside Windows
    return bool(attributes & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM))


def unique_destination(destination, taken=()):
    """Return a path that does not exist yet: 'a.txt', 'a (1).txt', 'a (2).txt', ..."""
    candidate = destination
    counter = 1
    while candidate.exists() or candidate in taken:
        candidate = destination.with_name(f"{destination.stem} ({counter}){destination.suffix}")
        counter += 1
    return candidate


def plan_moves(target, script_path=None):
    """Work out which files to move where. Nothing is changed on disk.

    Returns a list of (source, destination) Path pairs.
    """
    target = Path(target).resolve()
    script_path = Path(script_path).resolve() if script_path else None
    moves = []
    taken = set()
    for entry in sorted(target.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_symlink() or not entry.is_file():
            continue                      # never move folders or links
        if is_hidden(entry) or entry.name == UNDO_LOG_NAME:
            continue
        if script_path is not None and entry.resolve() == script_path:
            continue                      # never move this script
        destination = unique_destination(target / category_for(entry.name) / entry.name, taken)
        taken.add(destination)
        moves.append((entry, destination))
    return moves


def apply_moves(target, moves):
    """Move the files and append the moves to the undo log in `target`."""
    target = Path(target).resolve()
    log_path = target / UNDO_LOG_NAME
    log = load_log(log_path)
    for source, destination in moves:
        destination.parent.mkdir(exist_ok=True)
        destination = unique_destination(destination)   # in case something changed meanwhile
        shutil.move(str(source), str(destination))
        log.append({"from": source.relative_to(target).as_posix(),
                    "to": destination.relative_to(target).as_posix()})
        save_log(log_path, log)            # save after every move, so a crash loses nothing
    return log_path


def undo(target):
    """Move files back to where they were, using the undo log.

    Returns two lists of log entries: (restored, skipped).
    """
    target = Path(target).resolve()
    log_path = target / UNDO_LOG_NAME
    log = load_log(log_path)
    restored, skipped = [], []
    for move in reversed(log):
        current = target / move["to"]
        original = target / move["from"]
        if current.exists() and not original.exists():
            shutil.move(str(current), str(original))
            restored.append(move)
            try:
                current.parent.rmdir()     # remove the category folder if now empty
            except OSError:
                pass
        else:
            skipped.insert(0, move)
    if skipped:
        save_log(log_path, skipped)
    elif log_path.exists():
        log_path.unlink()
    return restored, skipped


def load_log(log_path):
    if not log_path.exists():
        return []
    with open(log_path, encoding="utf-8") as f:
        return json.load(f)


def save_log(log_path, log):
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sort the files of a folder into category sub-folders "
                    "(dry run unless --apply is given).")
    parser.add_argument("folder", help="the folder to sort, e.g. your Downloads folder")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="really move the files")
    group.add_argument("--undo", action="store_true",
                       help="move files back using the undo log")
    args = parser.parse_args(argv)

    target = Path(args.folder).expanduser()
    if not target.is_dir():
        parser.error(f"not a folder: {target}")

    if args.undo:
        if not (target / UNDO_LOG_NAME).exists():
            print("Nothing to undo (no undo log in this folder).")
            return 0
        restored, skipped = undo(target)
        for move in restored:
            print(f"restored  {move['to']}  ->  {move['from']}")
        for move in skipped:
            print(f"skipped   {move['to']} (missing, or {move['from']} already exists)")
        print(f"\nRestored {len(restored)} file(s), skipped {len(skipped)}.")
        return 0

    moves = plan_moves(target, script_path=Path(__file__))
    if not moves:
        print("Nothing to sort: no loose files found (folders and hidden files are ignored).")
        return 0

    base = target.resolve()
    for source, destination in moves:
        print(f"{source.name}  ->  {destination.relative_to(base).as_posix()}")

    if args.apply:
        log_path = apply_moves(target, moves)
        print(f"\nMoved {len(moves)} file(s). Undo log: {log_path}")
        print(f"To undo: python main.py \"{args.folder}\" --undo")
    else:
        print(f"\nDry run: {len(moves)} file(s) would be moved. Add --apply to do it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
