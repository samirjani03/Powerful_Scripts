@echo off
setlocal

:: ============================================================
:: DOWNLOADS ORGANIZER - ULTIMATE
::
:: Features:
::   - Recursive organization
::   - Folder-by-folder IGNORE selection
::   - Safe preview / dry run
::   - Duplicate protection
::   - Transaction log for every successful move
::   - Undo LAST completed organizer run
::   - Safe handling of undo conflicts
::   - Automatic protection for common project folders
::   - No external software required
::
:: Put this BAT file in the folder you want to organize.
:: ============================================================

set "ORGANIZER_SCRIPT=%~f0"
set "ORGANIZER_ROOT=%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
"$content = Get-Content -LiteralPath $env:ORGANIZER_SCRIPT -Raw; ^
$parts = $content -split '(?m)^### POWERSHELL ENGINE ###\r?\n', 2; ^
if ($parts.Count -lt 2) { Write-Host 'ERROR: PowerShell engine section not found.' -ForegroundColor Red; exit 1 }; ^
& ([scriptblock]::Create($parts[1]))"

set "EXITCODE=%ERRORLEVEL%"
endlocal & exit /b %EXITCODE%


### POWERSHELL ENGINE ###

$ErrorActionPreference = "Stop"

# ============================================================
# ROOT / INTERNAL PATHS
# ============================================================

$Root = [Environment]::GetEnvironmentVariable("ORGANIZER_ROOT")
$ScriptPath = [Environment]::GetEnvironmentVariable("ORGANIZER_SCRIPT")

if ([string]::IsNullOrWhiteSpace($Root)) {
    Write-Host ""
    Write-Host "ERROR: Could not determine organizer folder." -ForegroundColor Red
    exit 1
}

try {
    $Root = (Get-Item -LiteralPath $Root -Force).FullName
}
catch {
    Write-Host ""
    Write-Host "ERROR: Could not access organizer folder." -ForegroundColor Red
    exit 1
}

if (-not $Root.EndsWith("\")) {
    $Root += "\"
}

$ScriptName = Split-Path -Leaf $ScriptPath

$OrganizerDataDir = Join-Path $Root ".downloads-organizer"
$HistoryDir = Join-Path $OrganizerDataDir "history"
$LastRunPointer = Join-Path $OrganizerDataDir "last-run.txt"

# Create internal data directory and keep it hidden.
if (-not (Test-Path -LiteralPath $OrganizerDataDir)) {
    New-Item -ItemType Directory -Path $OrganizerDataDir -Force | Out-Null
}

if (-not (Test-Path -LiteralPath $HistoryDir)) {
    New-Item -ItemType Directory -Path $HistoryDir -Force | Out-Null
}

try {
    $DataFolder = Get-Item -LiteralPath $OrganizerDataDir -Force
    $DataFolder.Attributes = $DataFolder.Attributes -bor [System.IO.FileAttributes]::Hidden
}
catch {
    # Non-fatal. The organizer still works if hiding fails.
}


# ============================================================
# CATEGORY DEFINITIONS
# ============================================================

$CategoryNames = @(
    "Images",
    "Word",
    "PDF",
    "Spreadsheets",
    "Presentations",
    "Documents",
    "Text",
    "Ebooks",
    "Videos",
    "Audio",
    "Subtitles",
    "Archives",
    "Code",
    "Web",
    "Data",
    "Config",
    "Applications",
    "DiskImages",
    "Fonts",
    "Design",
    "3D",
    "Databases",
    "Security",
    "Shortcuts",
    "Torrents",
    "Others"
)


# ============================================================
# AUTOMATICALLY PROTECTED FOLDERS
#
# These folders are never entered recursively.
# This protects common project/repository folders and prevents
# the organizer from processing its own output folders.
# ============================================================

$AutoProtectedFolderNames = @(
    # Organizer output categories
    "Images",
    "Word",
    "PDF",
    "Spreadsheets",
    "Presentations",
    "Documents",
    "Text",
    "Ebooks",
    "Videos",
    "Audio",
    "Subtitles",
    "Archives",
    "Code",
    "Web",
    "Data",
    "Config",
    "Applications",
    "DiskImages",
    "Fonts",
    "Design",
    "3D",
    "Databases",
    "Security",
    "Shortcuts",
    "Torrents",
    "Others",

    # Organizer's own internal folder
    ".downloads-organizer",

    # Common source-control / dependency / build folders
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv"
)


# ============================================================
# FILES WE NEVER TOUCH
# ============================================================

$ProtectedFileNames = @(
    $ScriptName,
    "desktop.ini",
    "Thumbs.db",
    ".DS_Store"
)

$TemporaryExtensions = @(
    ".crdownload",
    ".part",
    ".download",
    ".opdownload",
    ".partial",
    ".tmp"
)


# ============================================================
# HELPER: RELATIVE PATH
# ============================================================

function Get-RelativePath {
    param(
        [string]$FullPath
    )

    if ($FullPath.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $FullPath.Substring($Root.Length).TrimStart("\")
    }

    return $FullPath
}


# ============================================================
# HELPER: AUTO-PROTECTED FOLDER
# ============================================================

function Test-AutoProtectedFolder {
    param(
        [System.IO.DirectoryInfo]$Folder
    )

    if ($AutoProtectedFolderNames -contains $Folder.Name) {
        return $true
    }

    # Never recurse through junctions / symlinks / reparse points.
    if (($Folder.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        return $true
    }

    return $false
}


# ============================================================
# RECURSIVE FOLDER SCANNER
# ============================================================

function Get-FolderTree {
    param(
        [string]$Path
    )

    $Results = New-Object System.Collections.Generic.List[object]

    try {
        $Children = Get-ChildItem `
            -LiteralPath $Path `
            -Directory `
            -Force `
            -ErrorAction Stop
    }
    catch {
        return @()
    }

    foreach ($Folder in $Children) {

        $null = $Results.Add($Folder)

        # Do not enter junctions / symlinks.
        if (($Folder.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            continue
        }

        # Do not recurse into automatic protected folders.
        if ($AutoProtectedFolderNames -contains $Folder.Name) {
            continue
        }

        $Nested = @(Get-FolderTree -Path $Folder.FullName)

        foreach ($Item in $Nested) {
            $null = $Results.Add($Item)
        }
    }

    return $Results.ToArray()
}


# ============================================================
# FILE CLASSIFICATION
# ============================================================

function Get-Category {
    param(
        [System.IO.FileInfo]$File
    )

    $Extension = $File.Extension.ToLowerInvariant()
    $Name = $File.Name.ToLowerInvariant()


    # IMAGES
    if ($Extension -in @(
        ".jpg",".jpeg",".jpe",".jfif",".pjpeg",".pjp",
        ".png",".gif",".bmp",".webp",".svg",
        ".heic",".heif",".tif",".tiff",
        ".ico",".avif",".raw",
        ".cr2",".cr3",".nef",".arw",".dng"
    )) {
        return "Images"
    }


    # WORD
    if ($Extension -in @(
        ".doc",".docx",".docm",
        ".dot",".dotx",".dotm"
    )) {
        return "Word"
    }


    # PDF
    if ($Extension -eq ".pdf") {
        return "PDF"
    }


    # SPREADSHEETS
    if ($Extension -in @(
        ".xls",".xlsx",".xlsm",".xlsb",
        ".xlt",".xltx",
        ".csv",".tsv",".ods"
    )) {
        return "Spreadsheets"
    }


    # PRESENTATIONS
    if ($Extension -in @(
        ".ppt",".pptx",".pptm",
        ".pps",".ppsx",
        ".pot",".potx",".odp"
    )) {
        return "Presentations"
    }


    # OTHER DOCUMENTS
    if ($Extension -in @(
        ".odt",".ott",
        ".wps",".pages"
    )) {
        return "Documents"
    }


    # TEXT / NOTES
    if ($Extension -in @(
        ".txt",".rtf",".md",".markdown",
        ".log",".nfo",".rst"
    )) {
        return "Text"
    }


    # EBOOKS
    if ($Extension -in @(
        ".epub",".mobi",".azw",".azw3"
    )) {
        return "Ebooks"
    }


    # VIDEOS
    if ($Extension -in @(
        ".mp4",".mkv",".avi",".mov",
        ".wmv",".flv",".webm",
        ".m4v",".3gp",
        ".mpg",".mpeg",
        ".ts",".m2ts",".m2v"
    )) {
        return "Videos"
    }


    # AUDIO
    if ($Extension -in @(
        ".mp3",".wav",".flac",".aac",
        ".m4a",".ogg",".opus",
        ".wma",".aiff",".aif",".amr"
    )) {
        return "Audio"
    }


    # SUBTITLES
    if ($Extension -in @(
        ".srt",".ass",".ssa",".vtt",".sub"
    )) {
        return "Subtitles"
    }


    # ARCHIVES
    if ($Extension -in @(
        ".zip",".rar",".7z",
        ".tar",".gz",".bz2",".xz",
        ".tgz",".tbz",".cab",
        ".zst"
    )) {
        return "Archives"
    }


    # PROGRAMMING / CODE
    if ($Extension -in @(
        ".py",".pyw",
        ".js",".jsx",
        ".ts",".tsx",
        ".java",
        ".c",".h",
        ".cpp",".cc",".hpp",
        ".cs",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".kt",".kts",
        ".dart",
        ".lua",
        ".r",
        ".scala",
        ".groovy",
        ".asm",".s",
        ".sql",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".ps1",
        ".psm1",
        ".bat",
        ".cmd",
        ".vbs",
        ".vim"
    )) {
        return "Code"
    }


    # WEB
    if ($Extension -in @(
        ".html",".htm",
        ".css",".scss",".sass",".less"
    )) {
        return "Web"
    }


    # DATA
    if ($Extension -in @(
        ".json",".jsonl",
        ".xml",
        ".yaml",".yml",
        ".parquet",
        ".avro"
    )) {
        return "Data"
    }


    # CONFIG
    if ($Extension -in @(
        ".ini",".cfg",".conf",
        ".config",".properties",
        ".toml"
    )) {
        return "Config"
    }

    if ($Name -eq ".env" -or $Name.StartsWith(".env.")) {
        return "Config"
    }


    # APPLICATIONS / INSTALLERS
    if ($Extension -in @(
        ".exe",".msi",".msix",".appx",
        ".apk",".deb",".rpm",
        ".dmg",".pkg",".run"
    )) {
        return "Applications"
    }


    # DISK / VIRTUAL MACHINE IMAGES
    if ($Extension -in @(
        ".iso",".img",
        ".vhd",".vhdx",
        ".vdi",".vmdk",
        ".qcow",".qcow2",
        ".ova",".ovf",
        ".bin",".cue"
    )) {
        return "DiskImages"
    }


    # FONTS
    if ($Extension -in @(
        ".ttf",".otf",
        ".woff",".woff2"
    )) {
        return "Fonts"
    }


    # DESIGN
    if ($Extension -in @(
        ".psd",".psb",
        ".ai",".eps",
        ".indd",
        ".xcf",
        ".sketch",
        ".fig"
    )) {
        return "Design"
    }


    # 3D
    if ($Extension -in @(
        ".obj",".fbx",".stl",
        ".blend",
        ".glb",".gltf",
        ".3ds",".dae",
        ".step",".stp",
        ".iges",".igs"
    )) {
        return "3D"
    }


    # DATABASE
    if ($Extension -in @(
        ".db",".sqlite",".sqlite3",
        ".mdb",".accdb"
    )) {
        return "Databases"
    }


    # SECURITY / CERTIFICATES
    if ($Extension -in @(
        ".pem",".crt",".cer",
        ".csr",".der",
        ".p12",".pfx",
        ".pub",".key",
        ".ovpn"
    )) {
        return "Security"
    }


    # SHORTCUTS / LINKS
    if ($Extension -in @(
        ".lnk",".url"
    )) {
        return "Shortcuts"
    }


    # TORRENTS
    if ($Extension -eq ".torrent") {
        return "Torrents"
    }


    # UNKNOWN
    return "Others"
}


# ============================================================
# SKIP FILE?
# ============================================================

function Test-SkipFile {
    param(
        [System.IO.FileInfo]$File
    )

    if ($File.Name -ieq $ScriptName) {
        return $true
    }

    if ($ProtectedFileNames -contains $File.Name) {
        return $true
    }

    # Hidden/system files remain untouched.
    if (($File.Attributes -band [System.IO.FileAttributes]::Hidden) -ne 0) {
        return $true
    }

    if (($File.Attributes -band [System.IO.FileAttributes]::System) -ne 0) {
        return $true
    }

    # Microsoft Office temporary files.
    if ($File.Name.StartsWith("~$")) {
        return $true
    }

    # Browser / incomplete download files.
    if ($TemporaryExtensions -contains $File.Extension.ToLowerInvariant()) {
        return $true
    }

    return $false
}


# ============================================================
# DUPLICATE-SAFE DESTINATION
# ============================================================

function Get-UniqueDestination {
    param(
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Destination)) {
        return $Destination
    }

    $Directory = Split-Path -Parent $Destination
    $FileName = Split-Path -Leaf $Destination

    $Base = [System.IO.Path]::GetFileNameWithoutExtension($FileName)
    $Extension = [System.IO.Path]::GetExtension($FileName)

    $Counter = 1

    do {
        $Candidate = Join-Path `
            $Directory `
            ("{0} ({1}){2}" -f $Base, $Counter, $Extension)

        $Counter++
    }
    while (Test-Path -LiteralPath $Candidate)

    return $Candidate
}


# ============================================================
# IGNORE PATH CHECK
# ============================================================

function Test-IsIgnoredPath {
    param(
        [string]$Path,
        [string[]]$IgnoredPaths
    )

    foreach ($Ignored in $IgnoredPaths) {

        $NormalizedIgnored = $Ignored.TrimEnd("\")

        if ($Path.Equals(
            $NormalizedIgnored,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            return $true
        }

        if ($Path.StartsWith(
            $NormalizedIgnored + "\",
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            return $true
        }
    }

    return $false
}


# ============================================================
# SELECTION PARSER
#
# Examples:
#   2,5,8
#   2,5-8,14
#   N
#   A
# ============================================================

function Parse-FolderSelection {
    param(
        [string]$InputText,
        [int]$Maximum
    )

    $Selected = New-Object System.Collections.Generic.HashSet[int]

    if ([string]::IsNullOrWhiteSpace($InputText)) {
        return $Selected
    }

    $InputText = $InputText.Trim()

    if ($InputText -match "^(N|NONE)$") {
        return $Selected
    }

    if ($InputText -match "^(A|ALL)$") {

        for ($i = 1; $i -le $Maximum; $i++) {
            $null = $Selected.Add($i)
        }

        return $Selected
    }

    foreach ($Part in ($InputText -split ",")) {

        $Token = $Part.Trim()

        if ([string]::IsNullOrWhiteSpace($Token)) {
            continue
        }

        if ($Token -match "^(\d+)\s*-\s*(\d+)$") {

            $Start = [int]$Matches[1]
            $End = [int]$Matches[2]

            if ($Start -gt $End) {
                $Temp = $Start
                $Start = $End
                $End = $Temp
            }

            for ($i = $Start; $i -le $End; $i++) {

                if ($i -ge 1 -and $i -le $Maximum) {
                    $null = $Selected.Add($i)
                }
            }

            continue
        }

        if ($Token -match "^\d+$") {

            $Number = [int]$Token

            if ($Number -ge 1 -and $Number -le $Maximum) {
                $null = $Selected.Add($Number)
            }

            continue
        }

        Write-Host "Ignoring invalid selection: $Token" -ForegroundColor Yellow
    }

    return $Selected
}


# ============================================================
# INPUT: YES / NO
# ============================================================

function Confirm-Yes {
    param(
        [string]$Prompt
    )

    while ($true) {

        $Answer = Read-Host $Prompt

        if ($Answer -ieq "YES" -or $Answer -ieq "Y") {
            return $true
        }

        if ($Answer -ieq "NO" -or $Answer -ieq "N") {
            return $false
        }

        Write-Host "Please type YES or NO." -ForegroundColor Yellow
    }
}


# ============================================================
# CREATE NEW RUN LOG
# ============================================================

function New-RunLog {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
    $FileName = "run_$Timestamp.jsonl"

    return (Join-Path $HistoryDir $FileName)
}


# ============================================================
# APPEND SUCCESSFUL MOVE TO RUN LOG
#
# JSON Lines is used so each move is committed immediately.
# If 400 files move and file 401 fails, the first 400 are still
# undoable.
# ============================================================

function Add-MoveToLog {
    param(
        [string]$LogPath,
        [string]$Source,
        [string]$Destination
    )

    $Record = [PSCustomObject]@{
        Time = (Get-Date).ToString("o")
        Source = $Source
        Destination = $Destination
    }

    $Record |
        ConvertTo-Json -Compress |
        Add-Content -LiteralPath $LogPath -Encoding UTF8
}


# ============================================================
# LOAD LAST RUN
# ============================================================

function Get-LastRunLog {
    if (-not (Test-Path -LiteralPath $LastRunPointer)) {
        return $null
    }

    try {
        $Path = (Get-Content -LiteralPath $LastRunPointer -Raw).Trim()

        if ([string]::IsNullOrWhiteSpace($Path)) {
            return $null
        }

        if (-not (Test-Path -LiteralPath $Path)) {
            return $null
        }

        return $Path
    }
    catch {
        return $null
    }
}


# ============================================================
# UNDO LAST RUN
# ============================================================

function Undo-LastRun {

    Clear-Host

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                    UNDO LAST RUN" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    $LogPath = Get-LastRunLog

    if ($null -eq $LogPath) {

        Write-Host "No completed organizer run is available to undo." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to return"
        return
    }

    try {
        $Lines = @(
            Get-Content -LiteralPath $LogPath -ErrorAction Stop |
            Where-Object {
                -not [string]::IsNullOrWhiteSpace($_)
            }
        )
    }
    catch {

        Write-Host "Could not read the last-run history." -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to return"
        return
    }

    if ($Lines.Count -eq 0) {

        Write-Host "The last-run history is empty." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to return"
        return
    }

    $Records = New-Object System.Collections.Generic.List[object]

    foreach ($Line in $Lines) {

        try {
            $Record = $Line | ConvertFrom-Json
            $null = $Records.Add($Record)
        }
        catch {
            Write-Host "Warning: one history record could not be read." -ForegroundColor Yellow
        }
    }

    if ($Records.Count -eq 0) {

        Write-Host "No valid move records were found." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to return"
        return
    }


    # Process in reverse order.
    [array]::Reverse($Records.ToArray())

    Write-Host "History file:" -ForegroundColor DarkGray
    Write-Host "  $LogPath"
    Write-Host ""
    Write-Host "Files recorded as moved: $($Lines.Count)"
    Write-Host ""

    Write-Host "UNDO preview:" -ForegroundColor Yellow
    Write-Host ""

    $Undoable = 0
    $AlreadyMissing = 0
    $OriginalConflicts = 0

    foreach ($Record in $Records) {

        $Destination = [string]$Record.Destination
        $Source = [string]$Record.Source

        if (-not (Test-Path -LiteralPath $Destination)) {

            Write-Host "[MISSING] " -NoNewline -ForegroundColor Red
            Write-Host (Get-RelativePath $Destination)

            $AlreadyMissing++
            continue
        }

        if (Test-Path -LiteralPath $Source) {

            $OriginalConflicts++

            Write-Host "[CONFLICT]" -NoNewline -ForegroundColor Yellow
            Write-Host " original path already exists:"
            Write-Host "           $Source"
            continue
        }

        $Undoable++

        Write-Host "[RESTORE] " -NoNewline -ForegroundColor Green
        Write-Host (Get-RelativePath $Destination)

        Write-Host "          -> " -NoNewline
        Write-Host (Get-RelativePath $Source)
    }

    Write-Host ""
    Write-Host "Undoable files      : $Undoable" -ForegroundColor Green
    Write-Host "Missing at destination: $AlreadyMissing" -ForegroundColor Red
    Write-Host "Original path conflicts: $OriginalConflicts" -ForegroundColor Yellow
    Write-Host ""

    if ($Undoable -eq 0) {

        Write-Host "There are no files that can be safely restored automatically." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to return"
        return
    }


    Write-Host "Safety rule:" -ForegroundColor Cyan
    Write-Host "  Undo will NEVER overwrite an existing file."
    Write-Host "  If the original path exists, that record is skipped."
    Write-Host ""

    if (-not (Confirm-Yes "Type YES to undo the last run")) {

        Write-Host ""
        Write-Host "Undo cancelled. No files were moved back." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to return"
        return
    }


    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                    RESTORING FILES" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    $Restored = 0
    $Skipped = 0

    # Reverse of the original move order.
    [array]::Reverse($Records.ToArray())

    foreach ($Record in $Records) {

        $Destination = [string]$Record.Destination
        $Source = [string]$Record.Source

        try {

            if (-not (Test-Path -LiteralPath $Destination)) {

                Write-Host "[SKIPPED] Destination no longer exists:" -ForegroundColor Yellow
                Write-Host "         $(Get-RelativePath $Destination)"
                $Skipped++
                continue
            }

            if (Test-Path -LiteralPath $Source) {

                Write-Host "[CONFLICT] Original path already exists:" -ForegroundColor Yellow
                Write-Host "           $(Get-RelativePath $Source)"
                Write-Host "           File left where it currently is."
                $Skipped++
                continue
            }


            # Re-create the original parent directory if necessary.
            $SourceDirectory = Split-Path -Parent $Source

            if (-not (Test-Path -LiteralPath $SourceDirectory)) {

                New-Item `
                    -ItemType Directory `
                    -Path $SourceDirectory `
                    -Force `
                    -ErrorAction Stop | Out-Null
            }


            Move-Item `
                -LiteralPath $Destination `
                -Destination $Source `
                -ErrorAction Stop


            Write-Host "[RESTORED] " -NoNewline -ForegroundColor Green
            Write-Host (Get-RelativePath $Destination)

            Write-Host "           -> " -NoNewline
            Write-Host (Get-RelativePath $Source)

            $Restored++
        }
        catch {

            Write-Host ""
            Write-Host "[FAILED] Could not restore:" -ForegroundColor Red
            Write-Host "         $(Get-RelativePath $Destination)"
            Write-Host "         $($_.Exception.Message)" -ForegroundColor Red
            Write-Host ""

            $Skipped++
        }
    }


    # Mark the run as undone by removing the active pointer.
    # The original JSONL history remains in the history directory.
    try {
        if (Test-Path -LiteralPath $LastRunPointer) {
            Remove-Item -LiteralPath $LastRunPointer -Force
        }
    }
    catch {
        Write-Host "Warning: could not clear the last-run pointer." -ForegroundColor Yellow
    }


    # Clean only EMPTY organizer category folders.
    # Never recursively delete anything.
    foreach ($Category in $CategoryNames) {

        $Candidate = Join-Path $Root $Category

        if (Test-Path -LiteralPath $Candidate -PathType Container) {

            try {
                $Children = @(Get-ChildItem -LiteralPath $Candidate -Force -ErrorAction Stop)

                if ($Children.Count -eq 0) {
                    Remove-Item -LiteralPath $Candidate -Force -ErrorAction SilentlyContinue
                }
            }
            catch {
                # Non-fatal.
            }
        }
    }


    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "                       UNDO COMPLETE" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Restored successfully : $Restored" -ForegroundColor Green
    Write-Host "Skipped / failed      : $Skipped" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The original run history is still preserved." -ForegroundColor DarkGray
    Write-Host ""

    Read-Host "Press Enter to return"
}


# ============================================================
# ORGANIZE
# ============================================================

function Start-Organization {

    Clear-Host

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "              DOWNLOADS ORGANIZER - ORGANIZE" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Root folder:" -ForegroundColor DarkGray
    Write-Host "  $Root"
    Write-Host ""

    Write-Host "This run will:" -ForegroundColor Yellow
    Write-Host "  1. Scan recursively"
    Write-Host "  2. Let you choose folders to IGNORE"
    Write-Host "  3. Organize only the direct files of each allowed folder"
    Write-Host "  4. Keep files inside their current parent folder"
    Write-Host "  5. Preview every planned move"
    Write-Host "  6. Ask for final confirmation"
    Write-Host "  7. Log every successful move for UNDO"
    Write-Host ""


    # ========================================================
    # FOLDER SCAN
    # ========================================================

    Write-Host "Scanning folders..." -ForegroundColor Yellow
    Write-Host ""

    $Folders = @(Get-FolderTree -Path $Root)
    $Folders = @($Folders | Sort-Object FullName)


    # ========================================================
    # FOLDER SELECTION
    # ========================================================

    $IgnoredPaths = @()

    if ($Folders.Count -eq 0) {

        Write-Host "No subfolders found." -ForegroundColor DarkGray
        Write-Host ""

    } else {

        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "                    FOLDER SELECTION" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host ""

        Write-Host "Choose folders to IGNORE." -ForegroundColor Yellow
        Write-Host "Everything you do NOT select will be organized." -ForegroundColor Green
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  2,5,8        -> individual folders"
        Write-Host "  2,5-8,14     -> numbers + ranges"
        Write-Host "  N             -> ignore nothing"
        Write-Host "  A             -> ignore all selectable folders"
        Write-Host ""

        $FolderMap = @{}
        $Index = 0

        foreach ($Folder in $Folders) {

            $Index++
            $FolderMap[$Index] = $Folder.FullName

            $Relative = Get-RelativePath $Folder.FullName

            if (Test-AutoProtectedFolder -Folder $Folder) {

                Write-Host (
                    "{0,4}. [AUTO-PROTECTED] {1}" -f $Index, $Relative
                ) -ForegroundColor DarkGray

            } else {

                Write-Host (
                    "{0,4}. {1}" -f $Index, $Relative
                ) -ForegroundColor White
            }
        }

        Write-Host ""

        $Selection = Read-Host "Folders to IGNORE"

        $SelectedNumbers = Parse-FolderSelection `
            -InputText $Selection `
            -Maximum $Folders.Count


        # Build ignored paths from user's selections.
        $TempIgnored = New-Object System.Collections.Generic.List[string]

        foreach ($Number in $SelectedNumbers) {

            if (-not $FolderMap.ContainsKey($Number)) {
                continue
            }

            $Path = $FolderMap[$Number]

            $FolderObject = $Folders |
                Where-Object { $_.FullName -eq $Path } |
                Select-Object -First 1

            # User cannot override automatic protections.
            if ($FolderObject -and (Test-AutoProtectedFolder $FolderObject)) {
                continue
            }

            $null = $TempIgnored.Add($Path)
        }


        # If a parent is ignored, its children are automatically covered.
        $TempIgnored = @($TempIgnored | Sort-Object Length)

        $FinalIgnored = New-Object System.Collections.Generic.List[string]

        foreach ($Path in $TempIgnored) {

            if (-not (Test-IsIgnoredPath `
                -Path $Path `
                -IgnoredPaths @($FinalIgnored))) {

                $null = $FinalIgnored.Add($Path)
            }
        }

        $IgnoredPaths = @($FinalIgnored)


        # ====================================================
        # SHOW FOLDER DECISION
        # ====================================================

        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "                     FOLDER DECISION" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host ""

        Write-Host "IGNORE:" -ForegroundColor Yellow

        if ($IgnoredPaths.Count -eq 0) {

            Write-Host "  None" -ForegroundColor DarkGray

        } else {

            foreach ($Path in $IgnoredPaths) {
                Write-Host (
                    "  [IGNORE] $(Get-RelativePath $Path)"
                ) -ForegroundColor Yellow
            }
        }

        Write-Host ""
    }


    # ========================================================
    # BUILD PROCESSING LIST
    # ========================================================

    # Root itself is always processed.
    $FoldersToProcess = New-Object System.Collections.Generic.List[string]
    $null = $FoldersToProcess.Add($Root.TrimEnd("\"))


    foreach ($Folder in $Folders | Sort-Object FullName.Length, FullName) {

        if (Test-AutoProtectedFolder $Folder) {
            continue
        }

        if (Test-IsIgnoredPath `
            -Path $Folder.FullName `
            -IgnoredPaths $IgnoredPaths) {

            continue
        }

        $null = $FoldersToProcess.Add($Folder.FullName)
    }


    # ========================================================
    # BUILD FILE PLAN
    #
    # Every file stays within its current parent folder.
    #
    # internship/report.pdf
    #       ->
    # internship/PDF/report.pdf
    #
    # NOT:
    # Downloads/PDF/report.pdf
    # ========================================================

    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                    BUILDING PREVIEW" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    $Plan = New-Object System.Collections.Generic.List[object]

    foreach ($CurrentFolder in $FoldersToProcess) {

        try {

            $Files = @(
                Get-ChildItem `
                    -LiteralPath $CurrentFolder `
                    -File `
                    -Force `
                    -ErrorAction Stop
            )
        }
        catch {
            Write-Host "Warning: could not read folder:" -ForegroundColor Yellow
            Write-Host "  $(Get-RelativePath $CurrentFolder)"
            continue
        }


        foreach ($File in $Files) {

            if (Test-SkipFile $File) {
                continue
            }

            $Category = Get-Category $File

            $DestinationDirectory = Join-Path `
                $CurrentFolder `
                $Category

            $Destination = Join-Path `
                $DestinationDirectory `
                $File.Name

            $Destination = Get-UniqueDestination $Destination


            $null = $Plan.Add(
                [PSCustomObject]@{
                    Source = $File.FullName
                    Destination = $Destination
                    SourceRelative = Get-RelativePath $File.FullName
                    DestinationRelative = Get-RelativePath $Destination
                    Category = $Category
                }
            )
        }
    }


    # ========================================================
    # NOTHING TO DO
    # ========================================================

    if ($Plan.Count -eq 0) {

        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "                    NOTHING TO ORGANIZE" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "No files need to be moved."
        Write-Host ""
        Read-Host "Press Enter to return"
        return
    }


    # ========================================================
    # FILE PREVIEW
    # ========================================================

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                     FILE PREVIEW" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    foreach ($Item in $Plan) {

        Write-Host "[PLAN] $($Item.SourceRelative)"
        Write-Host "       -> $($Item.DestinationRelative)" -ForegroundColor Green
    }


    # ========================================================
    # SUMMARY
    # ========================================================

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                        SUMMARY" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    $Summary = @{}

    foreach ($Item in $Plan) {

        if (-not $Summary.ContainsKey($Item.Category)) {
            $Summary[$Item.Category] = 0
        }

        $Summary[$Item.Category]++
    }

    foreach ($Entry in ($Summary.GetEnumerator() | Sort-Object Name)) {

        Write-Host (
            "{0,-18} {1,5} file(s)" -f $Entry.Key, $Entry.Value
        )
    }

    Write-Host ""
    Write-Host (
        "TOTAL FILES TO MOVE : {0}" -f $Plan.Count
    ) -ForegroundColor Yellow

    Write-Host ""


    # ========================================================
    # CONFIRM
    # ========================================================

    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "                     FINAL CONFIRMATION" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""

    Write-Host "Nothing has been moved yet." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Undo history will be created automatically after movement."
    Write-Host ""

    if (-not (Confirm-Yes "Type YES to actually move these files")) {

        Write-Host ""
        Write-Host "Operation cancelled. No files were moved." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to return"
        return
    }


    # ========================================================
    # START TRANSACTION LOG
    # ========================================================

    $RunLog = New-RunLog

    # Create the file before moving anything.
    New-Item -ItemType File -Path $RunLog -Force | Out-Null

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                     MOVING FILES" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    $Moved = 0
    $Failed = 0


    # ========================================================
    # MOVE FILES
    #
    # Every SUCCESSFUL move is immediately appended to history.
    # ========================================================

    foreach ($Item in $Plan) {

        try {

            if (-not (Test-Path -LiteralPath $Item.Source)) {

                Write-Host "[FAILED] Source no longer exists:" -ForegroundColor Red
                Write-Host "         $($Item.SourceRelative)"
                $Failed++
                continue
            }


            $DestinationDirectory = Split-Path -Parent $Item.Destination


            if (-not (Test-Path -LiteralPath $DestinationDirectory)) {

                New-Item `
                    -ItemType Directory `
                    -Path $DestinationDirectory `
                    -Force `
                    -ErrorAction Stop | Out-Null
            }


            # Re-check destination in case something changed after preview.
            $FinalDestination = Get-UniqueDestination $Item.Destination


            Move-Item `
                -LiteralPath $Item.Source `
                -Destination $FinalDestination `
                -ErrorAction Stop


            # IMPORTANT:
            # Log only after the move actually succeeded.
            Add-MoveToLog `
                -LogPath $RunLog `
                -Source $Item.Source `
                -Destination $FinalDestination


            if ($FinalDestination -ne $Item.Destination) {

                Write-Host "[DUPLICATE] $($Item.SourceRelative)" `
                    -ForegroundColor Yellow

                Write-Host (
                    "            -> $(Get-RelativePath $FinalDestination)"
                ) -ForegroundColor Green

            } else {

                Write-Host "[MOVED]  $($Item.SourceRelative)"

                Write-Host (
                    "         -> $(Get-RelativePath $FinalDestination)"
                ) -ForegroundColor Green
            }

            $Moved++
        }
        catch {

            Write-Host ""
            Write-Host "[FAILED] $($Item.SourceRelative)" -ForegroundColor Red
            Write-Host "         $($_.Exception.Message)" -ForegroundColor Red
            Write-Host ""

            $Failed++
        }
    }


    # ========================================================
    # REGISTER LAST COMPLETED RUN
    #
    # Even a partially successful run is undoable.
    # ========================================================

    if ($Moved -gt 0) {

        Set-Content `
            -LiteralPath $LastRunPointer `
            -Value $RunLog `
            -Encoding UTF8

    } else {

        try {
            Remove-Item -LiteralPath $RunLog -Force -ErrorAction SilentlyContinue
        }
        catch {
            # Non-fatal.
        }

        try {
            Remove-Item -LiteralPath $LastRunPointer -Force -ErrorAction SilentlyContinue
        }
        catch {
            # Non-fatal.
        }
    }


    # ========================================================
    # FINAL RESULT
    # ========================================================

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "                   ORGANIZATION COMPLETE" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Successfully moved : $Moved" -ForegroundColor Green
    Write-Host "Failed              : $Failed" -ForegroundColor Red
    Write-Host ""

    if ($Moved -gt 0) {

        Write-Host "UNDO AVAILABLE:" -ForegroundColor Cyan
        Write-Host "  Run this organizer again and choose:"
        Write-Host "  2. Undo last run"
        Write-Host ""
        Write-Host "History saved to:" -ForegroundColor DarkGray
        Write-Host "  $RunLog"
    }

    Write-Host ""
    Read-Host "Press Enter to return"
}


# ============================================================
# MAIN MENU
# ============================================================

while ($true) {

    Clear-Host

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "              DOWNLOADS ORGANIZER - ULTIMATE" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Root:"
    Write-Host "  $Root"
    Write-Host ""

    $LastRun = Get-LastRunLog
    $HasUndo = ($null -ne $LastRun)

    if ($HasUndo) {

        try {
            $LastCount = @(
                Get-Content -LiteralPath $LastRun -ErrorAction Stop |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
            ).Count
        }
        catch {
            $LastCount = 0
        }

        Write-Host "Last organizer run:" -ForegroundColor Yellow
        Write-Host "  $LastCount successful move(s) available for UNDO."
        Write-Host ""
    } else {
        Write-Host "No completed organizer run is currently available for UNDO."
        Write-Host ""
    }

    Write-Host "1. Organize files"
    Write-Host "2. Undo last run"
    Write-Host "3. Exit"
    Write-Host ""

    $Choice = Read-Host "Choose"

    switch ($Choice) {

        "1" {
            Start-Organization
        }

        "2" {
            Undo-LastRun
        }

        "3" {
            Clear-Host
            exit 0
        }

        default {
            Write-Host ""
            Write-Host "Invalid choice. Use 1, 2 or 3." -ForegroundColor Yellow
            Start-Sleep -Seconds 1
        }
    }
}
