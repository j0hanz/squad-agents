# Human-in-the-loop reproduction loop (PowerShell version).
# Copy this file, edit the steps below, and run it.
# The agent runs the script; the user follows prompts in their terminal.
#
# Usage:
#   pwsh -File hitl-loop.template.ps1
#
# Two helpers:
#   Step "instruction"         -> show instruction, wait for Enter
#   Capture [ref]var "question" -> show question, read response into var
#
# At the end, captured values are printed as KEY=VALUE for the agent to parse.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Step([string]$Instruction) {
    Write-Host ""
    Write-Host ">>> $Instruction"
    Read-Host "    [Enter when done]" | Out-Null
}

function Capture([ref]$Var, [string]$Question) {
    Write-Host ""
    Write-Host ">>> $Question"
    $Var.Value = Read-Host "    > "
}

# --- edit below ---------------------------------------------------------

Step "Open the app at http://localhost:3000 and sign in."

$ERRORED = ""
Capture ([ref]$ERRORED) "Click the 'Export' button. Did it throw an error? (y/n)"

$ERROR_MSG = ""
Capture ([ref]$ERROR_MSG) "Paste the error message (or 'none'):"

# --- edit above ---------------------------------------------------------

Write-Host ""
Write-Host "--- Captured ---"
Write-Host "ERRORED=$ERRORED"
Write-Host "ERROR_MSG=$ERROR_MSG"
