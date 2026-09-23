# File Sorter

A small Python command-line tool that tidies a messy folder (for example `Downloads`) by moving its
files into category sub-folders such as `Images`, `Documents` or `Video`.

It is **safe by default**: it shows the plan first, never touches folders or hidden files, and can undo
everything it moved.

## Features

- Sorts the files of **the folder you pass on the command line**, and only that folder (not its sub-folders).
- **Dry run by default**: prints what would move where. Nothing changes until you add `--apply`.
- **Never moves folders** (so projects and `.git` folders stay where they are), hidden/system files, or the script itself.
- Case-insensitive extensions (`PHOTO.JPG` and `photo.jpg` both go to `Images`).
- Categories: `Images`, `Video`, `Audio`, `Documents`, `Spreadsheets`, `Archives`, `Code`, `Apps` and `Other`.
- **No overwriting**: if `Images/photo.jpg` already exists, the new file becomes `Images/photo (1).jpg`.
- **Undo log**: every move is saved to `.file-sorter-undo.json` inside the sorted folder, and `--undo` puts the files back.
- Works on Windows, macOS and Linux (uses `pathlib`). Standard library only.

## How to run

Requires Python 3.8+.

```bash
git clone https://github.com/naniiic137/File-Sorter.git
cd File-Sorter

python main.py "C:/Users/<you>/Downloads"           # 1. dry run: only shows the plan
python main.py "C:/Users/<you>/Downloads" --apply   # 2. really move the files
python main.py "C:/Users/<you>/Downloads" --undo    # put everything back
```

### Example output

Test folder with a few dummy files, a project folder, a hidden `.env` file and an existing `Images/holiday.JPG`:

```text
$ python main.py demo
backup.zip  ->  Archives/backup.zip
budget.xlsx  ->  Spreadsheets/budget.xlsx
clip.mp4  ->  Video/clip.mp4
CV.pdf  ->  Documents/CV.pdf
holiday.JPG  ->  Images/holiday (1).JPG
mystery.xyz  ->  Other/mystery.xyz
notes.txt  ->  Documents/notes.txt
script.py  ->  Code/script.py
setup.exe  ->  Apps/setup.exe
song.mp3  ->  Audio/song.mp3

Dry run: 10 file(s) would be moved. Add --apply to do it.

$ python main.py demo --apply
...
Moved 10 file(s). Undo log: ...\demo\.file-sorter-undo.json
To undo: python main.py "demo" --undo

$ python main.py demo --undo
restored  Audio/song.mp3  ->  song.mp3
...
Restored 10 file(s), skipped 0.
```

`my-project/` and `.env` were left alone.

### Changing the categories

The mapping is a plain dictionary at the top of `main.py` (`CATEGORIES`). Add an extension to a list,
or add a new category, and the sorter picks it up.

## Running the tests

The tests only create and use their own temporary folders.

```bash
python -m unittest -v
```

## Project structure

```text
main.py        # categorisation rules, planning, moving, undo and the command-line interface
test_main.py   # unit tests (unittest)
```

## Limitations

- Sorting is by file extension only; the file contents are not inspected.
- Only the top level of the folder is sorted; files inside sub-folders are not touched.
- `--undo` skips a file if something new now has its original name, and keeps it in the log so you can sort it out by hand.
- Undo removes a category folder only when it is empty afterwards.

## License

License: not chosen yet.
