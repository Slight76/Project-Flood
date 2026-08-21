[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$TargetPath,

    [ValidateSet('full', 'adapter')]
    [string]$Mode = 'full',

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$sourceRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\template'))

if (-not (Test-Path -LiteralPath $TargetPath -PathType Container)) {
    throw "Target directory does not exist: $TargetPath"
}

$targetRoot = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $TargetPath).Path)
$python = Get-Command python -ErrorAction SilentlyContinue
$pythonArgs = @()
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
    $pythonArgs = @('-3')
}
if (-not $python) {
    throw 'Python 3 is required.'
}

& $python.Source @pythonArgs -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'
if ($LASTEXITCODE -ne 0) {
    throw 'Project Flood requires Python 3.10 or newer.'
}

& $python.Source @pythonArgs -c 'import yaml'
if ($LASTEXITCODE -ne 0) {
    throw "PyYAML is required. Run: $($python.Source) $($pythonArgs -join ' ') -m pip install -r `"$(Join-Path $PSScriptRoot '..\requirements.txt')`""
}

$arguments = @(
    (Join-Path $PSScriptRoot 'flood.py'),
    'install',
    '--source', $sourceRoot,
    '--target', $targetRoot,
    '--mode', $Mode
)
if ($Force) {
    $arguments += '--force'
}

& $python.Source @pythonArgs @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Project Flood installation failed with exit code $LASTEXITCODE."
}

Write-Host 'Next: open the repository in VS Code, select Flood Squad Lead, and invoke flood-repository-onboarding.'
