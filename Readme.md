# Powerful Scripts

A collection of small scripts and security tools for **productivity,** **automation, cybersecurity, OSINT and experiments**.

> Use security tools only on systems and targets you own or have permission to test.

## Contents

| Project                                                                       | What it does                                | Main tech           |
| ----------------------------------------------------------------------------- | ------------------------------------------- | ------------------- |
| [IP Tracker](./IP%20Tracker/)                                                 | IP information / tracking utility           | Python              |
| [Keylogger](./Keylogger/)                                                     | Keylogging project for security learning    | Python              |
| [Local-CLI.ps1](./Local-CLI.ps1)                                              | Local Ollama-powered PowerShell CLI agent   | PowerShell + Ollama |
| [SQLinjection.py](./SQLinjection.py)                                          | SQL injection testing/scanning tool         | Python              |
| [locker.bat](./locker.bat)                                                    | Simple folder hide/unhide demo              | Windows Batch       |
| [pdfprotector.py](./pdfprotector.py)                                          | Password-protects PDF, Word and Excel files | Python              |
| [Downloads Organizer](./Downloads-Organizer/Downloads_Organizer_ULTIMATE.bat) | Smart recursive file organizer with undo    | Batch + PowerShell  |

---

## Downloads Organizer

**File:** `Downloads_Organizer_ULTIMATE.bat`

A Windows file organizer for messy folders.

### Features

* Organizes files by type
* Recursively handles subfolders
* Lets you choose folders to **IGNORE**
* Keeps project folders untouched
* Shows a preview before moving
* Handles duplicate filenames
* Saves move history
* Can **undo the last run**
* No extra software required

### Use

1. Put the `.bat` inside the folder you want to organize.
2. Run it.
3. Choose **Organize files**.
4. Select folders to ignore.
5. Check the preview.
6. Type `YES`.

To undo:

```text
2. Undo last run
```

### Example

```text
Downloads/
├── resume.docx
├── photo.jpg
└── internship/
    └── web-project/
        ├── index.html
        ├── style.css
        ├── app.js
        └── logo.png
```

Ignore `internship\myproject`:

```text
Downloads/
├── Word/
│   └── resume.docx
├── Images/
│   └── photo.jpg
└── internship/
    ├── PDF/
    │   └── report.pdf
    └── web-project/
        ├── index.html
        ├── style.css
        ├── app.js
        └── logo.png
```

`myproject` stays untouched.

---

## Local-CLI

**File:** `Local-CLI.ps1`

A local CLI agent using Ollama to generate PowerShell commands inside a fixed workspace.

Uses:

* Ollama
* `qwen2.5-coder:latest`
* `C:\AgentWorkspace`

It also checks generated commands before execution.

---

## SQL Injection Scanner

**File:** `SQLinjection.py`

A Python SQLi testing tool supporting:

* GET / POST
* Custom payloads
* Headers / cookies
* Proxy
* Threads
* Delays / retries
* TXT / JSON / CSV output

Install:

```bash
pip install requests urllib3 colorama
```

Use only against authorized targets.

---

## PDF Protector

**File:** `pdfprotector.py`

Password-protects:

* PDF
* `.docx`
* `.xlsx`

Install:

```bash
pip install pypdf rich pywin32
```

Word/Excel protection uses Microsoft Office on Windows.

---

## Folder Locker

**File:** `locker.bat`

A simple Windows Batch demo that hides/unhides a folder.

This is **not real encryption or strong security**. It's mainly a Batch scripting experiment.

---

## IP Tracker

**Folder:** `IP Tracker/`

An IP-related information / tracking project.

Open the folder for its own code and usage.

---

## Keylogger

**Folder:** `Keylogger/`

A keylogging project for understanding keyboard capture.

Use only on systems you own or are authorized to monitor.

---

More scripts will be added as the collection grows.
