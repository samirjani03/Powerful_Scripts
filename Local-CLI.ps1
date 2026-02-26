# param([string]$Query)

# if (-not $Query) {
#     Write-Host "Usage: powershell -File Local-CLI.ps1 'your query'"
#     exit 1
# }

# $model = "qwen2.5-coder:latest"
# $ollamaUrl = "http://localhost:11434/api/generate"

# $currentDir = Get-Location

# $prompt = @"
# You are Local-CLI. Respond ONLY in this format:

# COMMAND: <PowerShell command>

# Rules:
# - No markdown
# - No backticks
# - No explanation
# - Only one COMMAND line

# Current Directory: $currentDir
# User Query: $Query
# "@

# $body = @{
#     model = $model
#     prompt = $prompt
#     stream = $false
# } | ConvertTo-Json -Depth 3

# try {
#     $response = Invoke-RestMethod -Uri $ollamaUrl -Method Post -Body $body -ContentType "application/json"
# }
# catch {
#     Write-Host "Ollama not running?"
#     exit 1
# }

# $raw = $response.response

# # Clean response
# $cleanCmd = $raw -replace "^COMMAND:\s*", ""
# $cleanCmd = $cleanCmd.Trim()

# if ([string]::IsNullOrWhiteSpace($cleanCmd)) {
#     Write-Host "Invalid model response:"
#     Write-Host $raw
#     exit 1
# }

# Write-Host "Executing: $cleanCmd"

# try {
#     Invoke-Expression $cleanCmd
#     Write-Host "Done."
# }
# catch {
#     Write-Host "Execution failed:"
#     Write-Host $_
# }

param([string]$Query)

if (-not $Query) {
    Write-Host "Usage: powershell -File Local-CLI.ps1 'your query'"
    exit 1
}

# ===== CONFIG =====
$model = "qwen2.5-coder:latest"
$ollamaUrl = "http://localhost:11434/api/generate"
$workspace = "C:\AgentWorkspace"

# Ensure workspace exists
if (!(Test-Path $workspace)) {
    New-Item -ItemType Directory -Path $workspace | Out-Null
}

Set-Location $workspace

# ===== PROMPT =====
$prompt = @"
You are a Windows PowerShell CLI agent.

STRICT RULES:
- Respond ONLY in this format:
COMMAND: <PowerShell command>
- Use PowerShell syntax ONLY.
- Use ';' to separate multiple commands.
- DO NOT use &&.
- DO NOT use cmd syntax.
- No explanations.

Example valid response:
COMMAND: New-Item -ItemType Directory "demo" -Force; New-Item "demo\demo1.txt" -ItemType File

Current directory: $workspace
User request: $Query
"@

$body = @{
    model = $model
    prompt = $prompt
    stream = $false
} | ConvertTo-Json -Depth 3

try {
    $response = Invoke-RestMethod -Uri $ollamaUrl -Method Post -Body $body -ContentType "application/json"
}
catch {
    Write-Host "Ollama not running?"
    exit 1
}

$raw = $response.response
$cleanCmd = $raw -replace "^COMMAND:\s*", ""
$cleanCmd = $cleanCmd.Trim()

if ([string]::IsNullOrWhiteSpace($cleanCmd)) {
    Write-Host "Invalid model response:"
    Write-Host $raw
    exit 1
}

# ===== SECURITY LAYER =====

# Block dangerous tokens
$blockedPatterns = @("&&", "C:\Windows", "C:\Users", "C:\Program Files", "Remove-Item C:\", "format", "shutdown")

foreach ($pattern in $blockedPatterns) {
    if ($cleanCmd -match [regex]::Escape($pattern)) {
        Write-Host "Blocked dangerous command."
        exit 1
    }
}

# Whitelist command names
$allowed = @(
    "New-Item",
    "Remove-Item",
    "Add-Content",
    "Get-ChildItem",
    "Set-Location",
    "Rename-Item"
)

# Split multiple commands
$commands = $cleanCmd -split ";"

foreach ($cmd in $commands) {

    $cmd = $cmd.Trim()
    if ($cmd -eq "") { continue }

    $cmdName = $cmd.Split(" ")[0]

    if ($allowed -notcontains $cmdName) {
        Write-Host "Command not allowed: $cmdName"
        exit 1
    }
}

Write-Host "Executing inside workspace: $workspace"
Write-Host "Command(s): $cleanCmd"

try {
    Invoke-Expression $cleanCmd
    Write-Host "Done."
}
catch {
    Write-Host "Execution failed:"
    Write-Host $_
}