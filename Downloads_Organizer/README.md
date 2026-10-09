# Downloads Organizer

A simple Windows tool that organizes files into folders by file type. It is designed for a cluttered Downloads folder, but it can organize **the folder where the `.bat` file is placed**.

## What it does

- Sorts files into folders such as `Images`, `PDF`, `Videos`, `Audio`, `Archives`, `Code`, and `Documents`.
- Scans subfolders too, so it can organize files inside folders while keeping each file in its current parent folder.
- Lets you choose which subfolders to ignore.
- Shows a preview of planned moves and asks you to type `YES` before moving anything.
- Avoids overwriting files with the same name by choosing a new name, such as `report (1).pdf`.
- Skips hidden/system files, common temporary or incomplete downloads, and the organizer script itself.
- Keeps a move history so you can undo the last organizer run.

## How to use it

1. **Put the `.bat` file in the folder you want to organize.** For example, put it directly inside your Downloads folder.
2. **Double-click the `.bat` file** to open the menu. It does not need to be run as administrator.
3. Choose **`1. Organize files`**.
4. If subfolders are listed, enter the numbers of the folders you want to **ignore**. For example:
   - `2,5,8` ignores folders 2, 5, and 8.
   - `2,5-8` ignores folder 2 and folders 5 through 8.
   - `N` ignores no selectable folders.
   - `A` ignores all selectable folders.

   Any folder you do not ignore may be organized. Some folders are automatically protected.
5. Review the preview carefully. It shows where each file is planned to go.
6. If the plan looks right, type **`YES`** when asked to move the files. Type anything else if you want to cancel.
7. When it finishes, check the result and the move count shown on screen.

## Important: where files go

Files are sorted **inside their current folder**, not all collected into one set of folders at the top level.

For example:

```text
Downloads/
├── report.pdf
├── photo.jpg
└── Course/
    ├── notes.txt
    └── video.mp4
```

After organizing, it may look like:

```text
Downloads/
├── PDF/
│   └── report.pdf
├── Images/
│   └── photo.jpg
└── Course/
    ├── Text/
    │   └── notes.txt
    └── Videos/
        └── video.mp4
```

## Undo the last run

1. Run the same `.bat` file again.
2. Choose **`2. Undo last run`**.
3. Review the undo preview.
4. Type **`YES`** to restore the moved files to their recorded original locations.

Undo will not overwrite a file if something already exists at its original location. Such files are skipped and left where they are. Undo is for the **last organizer run only**; run history is stored in the hidden `.downloads-organizer` folder inside the folder being organized.

## Folders the tool skips automatically

It does not enter common project/dependency folders such as `.git`, `.svn`, `.hg`, `node_modules`, `.venv`, `venv`, and `__pycache__`. It also avoids following junctions/symbolic links. The organizer's category folders and its own `.downloads-organizer` history folder are protected from recursive scanning.

Files with unknown extensions are placed in `Others`. Some files are skipped, including hidden/system files, common incomplete-download extensions, Office temporary files, and the organizer `.bat` itself.

## A few things to know

- **Preview first:** read the planned moves before confirming.
- **Undo is a safety net, not a backup.** Keep important files backed up.
- If you cancel before typing `YES`, no files are moved.
- The tool sorts by file extension; it does not inspect file contents to determine what a file really is.
- It organizes the folder containing the `.bat` file, so check its location before running it.
