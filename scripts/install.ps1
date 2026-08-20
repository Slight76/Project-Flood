[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$TargetPath,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$sourceRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\template'))

if (-not (Test-Path -LiteralPath $TargetPath -PathType Container)) {
    throw "Target directory does not exist: $TargetPath"
}

$targetRoot = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $TargetPath).Path)
$sourceFiles = Get-ChildItem -LiteralPath $sourceRoot -File -Recurse -Force
$entries = foreach ($sourceFile in $sourceFiles) {
    $relativePath = $sourceFile.FullName.Substring($sourceRoot.Length).TrimStart(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    [pscustomobject]@{
        Source = $sourceFile.FullName
        Relative = $relativePath
        Destination = Join-Path $targetRoot $relativePath
    }
}

$conflicts = @($entries | Where-Object { Test-Path -LiteralPath $_.Destination })
if ($conflicts.Count -gt 0 -and -not $Force) {
    $lines = ($conflicts.Relative | ForEach-Object { "  $_" }) -join [Environment]::NewLine
    throw "No files were copied because these destinations already exist:`n$lines`nMerge them manually, or rerun with -Force to back them up and replace them."
}

$backupRoot = $null
if ($conflicts.Count -gt 0) {
    $timestamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
    $backupRoot = Join-Path $targetRoot ".project-flood-backup\$timestamp"

    foreach ($entry in $conflicts) {
        $backupDestination = Join-Path $backupRoot $entry.Relative
        $backupDirectory = Split-Path -Parent $backupDestination
        New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
        Copy-Item -LiteralPath $entry.Destination -Destination $backupDestination
    }
}

foreach ($entry in $entries) {
    $destinationDirectory = Split-Path -Parent $entry.Destination
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    Copy-Item -LiteralPath $entry.Source -Destination $entry.Destination -Force
}

$scratchPath = Join-Path $targetRoot '.agent-team\scratch'
New-Item -ItemType Directory -Path $scratchPath -Force | Out-Null

Write-Host "Project Flood installed into $targetRoot"
if ($backupRoot) {
    Write-Host "Replaced files were backed up to $backupRoot"
}
Write-Host 'Next: open the repository in VS Code, select Squad Lead, and run /onboard-repository.'
