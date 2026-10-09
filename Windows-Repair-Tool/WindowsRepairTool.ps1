
# WindowsRepairTool.ps1
# Windows 10/11 | Windows PowerShell 5.1+
# No third-party dependencies.

$ErrorActionPreference = 'Stop'
$LogDir = Join-Path $env:ProgramData 'WindowsRepairTool\Logs'
$LogFile = Join-Path $LogDir (
    'Repair-{0}.log' -f (Get-Date -Format 'yyyyMMdd-HHmmss')
)
$script:Failures = [System.Collections.Generic.List[string]]::new()

# Require administrator privileges.
$Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = [Security.Principal.WindowsPrincipal]::new($Identity)

if (-not $Principal.IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)) {
    Write-Host 'Run PowerShell as Administrator, then start this script again.'
    exit 1
}

try {
    New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
    Start-Transcript -Path $LogFile -ErrorAction Stop | Out-Null
}
catch {
    Write-Error "Could not start logging: $($_.Exception.Message)"
    exit 1
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,

        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    Write-Host "`n> $FilePath $($Arguments -join ' ')" -ForegroundColor Cyan

    try {
        & $FilePath @Arguments
        $Code = $LASTEXITCODE

        if ($Code -ne 0) {
            $script:Failures.Add(
                "$FilePath returned exit code $Code"
            )
            Write-Warning "Command failed with exit code $Code."
            return $false
        }

        Write-Host 'Command completed successfully.' -ForegroundColor Green
        return $true
    }
    catch {
        $script:Failures.Add(
            "$FilePath : $($_.Exception.Message)"
        )
        Write-Warning $_.Exception.Message
        return $false
    }
}

function Invoke-WindowsRepair {
    Write-Host "`nRepairing the Windows image first..."
    $Dism = Invoke-NativeCommand 'DISM.exe' @(
        '/Online', '/Cleanup-Image', '/RestoreHealth'
    )

    Write-Host "`nChecking and repairing protected system files..."
    $Sfc = Invoke-NativeCommand 'sfc.exe' @('/scannow')

    if ($Dism -and $Sfc) {
        Write-Host 'Both commands reported successful completion.'
    }
    else {
        Write-Warning 'One or more repair commands reported a failure.'
    }
}

function Invoke-DiskCheck {
    # Online scan. This does not request an offline /f repair.
    Invoke-NativeCommand 'chkdsk.exe' @(
        $env:SystemDrive, '/scan'
    ) | Out-Null
}

function Invoke-NetworkRepair {
    Write-Warning 'This resets Winsock and TCP/IP settings.'
    Write-Warning 'Custom network configuration may need attention.'

    $Answer = Read-Host 'Continue? Type YES to confirm'
    if ($Answer -cne 'YES') {
        Write-Host 'Network repair cancelled.'
        return
    }

    Invoke-NativeCommand 'ipconfig.exe' @('/flushdns') | Out-Null
    Invoke-NativeCommand 'netsh.exe' @(
        'winsock', 'reset'
    ) | Out-Null
    Invoke-NativeCommand 'netsh.exe' @(
        'int', 'ip', 'reset'
    ) | Out-Null

    Write-Host 'Restart Windows if required by the reset operations.'
}

function New-SystemReport {
    $Report = Join-Path $LogDir (
        'SystemReport-{0}.txt' -f (Get-Date -Format 'yyyyMMdd-HHmmss')
    )

    try {
        systeminfo.exe | Out-File -FilePath $Report -Encoding utf8
        Write-Host "Report saved to: $Report"
    }
    catch {
        $script:Failures.Add("System report: $($_.Exception.Message)")
        Write-Warning $_.Exception.Message
    }
}

try {
    do {
        Write-Host "`n===== Windows Repair Tool ====="
        Write-Host '1. Repair Windows image and system files'
        Write-Host '2. Scan the Windows drive'
        Write-Host '3. Repair network configuration'
        Write-Host '4. Generate system report'
        Write-Host '5. Clean up Windows component store'
        Write-Host '0. Exit'

        $Choice = Read-Host 'Choose an action'

        switch ($Choice) {
            '1' { Invoke-WindowsRepair }
            '2' { Invoke-DiskCheck }
            '3' { Invoke-NetworkRepair }
            '4' { New-SystemReport }
            '5' {
                $Answer = Read-Host 'Run component cleanup? Type YES'
                if ($Answer -ceq 'YES') {
                    Invoke-NativeCommand 'DISM.exe' @(
                        '/Online', '/Cleanup-Image',
                        '/StartComponentCleanup'
                    ) | Out-Null
                }
            }
            '0' { break }
            default { Write-Host 'Invalid choice.' }
        }
    } while ($Choice -ne '0')
}
finally {
    if ($script:Failures.Count -gt 0) {
        Write-Host "`nCommands requiring attention:"
        $script:Failures | ForEach-Object { Write-Host "- $_" }
    }
    else {
        Write-Host "`nNo nonzero exit codes were recorded."
    }

    Write-Host "Log: $LogFile"
    Stop-Transcript | Out-Null
}