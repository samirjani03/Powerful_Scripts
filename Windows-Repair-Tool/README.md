# Windows Repair Tool

A small PowerShell menu for running selected Windows maintenance and repair tasks.

The tool is designed to make common Windows commands easier to run and keep a transcript of what happened. It is an early version, so read the notes below before using it.

## Features

- Repairs the Windows image with DISM and then checks protected system files with SFC.
- Scans the Windows system drive with CHKDSK.
- Offers an optional network reset.
- Generates a basic system information report.
- Offers optional Windows component-store cleanup.
- Saves logs and reports in a predictable location.

## Requirements

- Windows 10 or Windows 11.
- Windows PowerShell 5.1 or later.
- An administrator account.
- An internet connection may be needed by DISM if Windows cannot find the repair files locally.
- No third-party PowerShell modules are required.

## How to run it

### 1. Save the script

Save the PowerShell script as:

```text
WindowsRepairTool.ps1
```

Make sure Windows hasn't saved it as `WindowsRepairTool.ps1.txt`.

### 2. Open PowerShell as Administrator

1. Open the Start menu.
2. Search for **Windows PowerShell**.
3. Right-click it and select **Run as administrator**.
4. Approve the User Account Control prompt.

The script needs administrator rights to run most of the repair commands.

### 3. Go to the script folder

For example, if you saved it in Downloads:

```powershell
Set-Location "$HOME\Downloads"
```

If it is in another folder, change the path to match your location.

### 4. Allow the script for this PowerShell session

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

This changes the execution policy only in the current PowerShell process. It does not permanently change the machine-wide policy. If your organization manages execution policies, follow its rules instead of trying to bypass them.

### 5. Start the tool

Run:

```powershell
.\WindowsRepairTool.ps1
```

Choose an option from the menu. Read each warning and confirmation prompt before continuing.

## Menu options

| Option | What it does | Before you run it |
| --- | --- | --- |
| `1` | Runs DISM `/RestoreHealth`, then `sfc /scannow`. | Repairs the Windows image and checks protected system files. It can take a while. |
| `2` | Runs `chkdsk` with `/scan` on the Windows system drive. | Performs an online filesystem scan. It is not a full hardware-health test. |
| `3` | Flushes DNS and resets Winsock and TCP/IP settings. | May disrupt networking or affect custom network settings. Use only when troubleshooting a network problem. A restart may be needed. |
| `4` | Saves the output of `systeminfo` to a text report. | Collects system details. Review the report before sharing it because it may contain information about your PC and environment. |
| `5` | Runs DISM component-store cleanup after confirmation. | This is maintenance, not a universal fix. |
| `0` | Exits the tool. | No action is run. |

## Where logs and reports are saved

The tool writes files to:

```text
C:\ProgramData\WindowsRepairTool\Logs
```

This uses the standard `ProgramData` directory on the Windows system drive. It creates a timestamped transcript log and timestamped system reports.

To open the folder, press `Win + R`, paste the path, and press Enter. You may need administrator permission to access some files.

## Safety notes

- **Read the menu and prompts carefully.** Do not run a repair just because it is available.
- **Network reset changes settings.** If you use a static IP address, custom DNS, VPN, proxy, virtual network adapter, or specialized networking software, record your settings first.
- **CHKDSK is not a hardware diagnostic.** If you suspect a failing drive, back up important data and use suitable drive-health diagnostics.
- **DISM and SFC can take time.** Do not close the terminal or power off the computer while a repair is running unless the system is unresponsive and you have no safer option.
- **Boot repair is intentionally excluded.** Commands such as `bootrec` are not general maintenance commands and should be used only in an appropriate recovery workflow.
- **Review logs before sharing them.** System reports and logs can reveal usernames, device details, installed software, and other environment information.
- **No repair is guaranteed.** A command completing successfully does not prove every Windows problem is fixed.

## Troubleshooting

### “Running scripts is disabled on this system”

Open PowerShell and follow the session-only execution-policy step above, unless a policy set by your organization prevents it.

### “Run PowerShell as Administrator”

Close the current terminal. Open Windows PowerShell using **Run as administrator**, navigate back to the script folder, and start the script again.

### DISM or SFC reports an error

Write down the exact error and exit code. Check the transcript log and the Windows servicing logs before repeating repairs. Microsoft's guidance is available here:

- System File Checker: https://support.microsoft.com/en-us/windows/experience/backup-recovery/using-system-file-checker-in-windows
- DISM PowerShell documentation: https://learn.microsoft.com/en-us/powershell/module/dism/repair-windowsimage

### The network still does not work

Restart Windows if requested, then test the connection. If the issue continues, diagnose the adapter, IP configuration, DNS, VPN, proxy, and router separately rather than repeatedly resetting the network stack.

## Limitations

This project is an early utility, not a complete diagnostic suite. The script has not been validated on every Windows build, and its handling of command-specific exit codes may need improvement. Always check the command output and logs. Do not treat the final menu message as proof that Windows is healthy.

## Contributing

Issues, bug reports, and improvements are welcome. Include the Windows version, the menu option used, the exact error text, and relevant log excerpts. Remove usernames, device identifiers, IP addresses, and other private information before posting logs publicly.

## License

No license has been selected yet. Until a license is added to the repository, others do not automatically have permission to redistribute or modify the project. If you want it to be open source, add a license file before publishing.
