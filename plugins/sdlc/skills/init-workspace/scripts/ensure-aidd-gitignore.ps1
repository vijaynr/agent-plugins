[CmdletBinding()]
param(
    [string]$Root = '.'
)

$ErrorActionPreference = 'Stop'

$gitignore = Join-Path $Root '.gitignore'
$parent = Split-Path -Parent $gitignore
if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $gitignore -PathType Leaf)) {
    New-Item -ItemType File -Path $gitignore -Force | Out-Null
}

$aiddLines = @(
    '# AIDD',
    '/.features/*',
    '!/.features/*/',
    '/.features/*/*',
    '!/.features/*/SPEC.md',
    '!/.features/*/DESIGN.md',
    '!/.features/*/tasks/',
    '!/.features/*/tasks/PLAN.md',
    '!/.features/*/tasks/TODO.md'
)

$content = @(Get-Content -LiteralPath $gitignore -ErrorAction SilentlyContinue)
$changed = $false
foreach ($line in $aiddLines) {
    if ($content -notcontains $line) {
        Add-Content -LiteralPath $gitignore -Value $line
        $content += $line
        $changed = $true
    }
}

[ordered]@{
    ok = $true
    changed = $changed
    gitignore = $gitignore
} | ConvertTo-Json -Depth 3
