[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Feature,

    [string]$Branch = '',
    [string]$Base = '',
    [string]$WorktreePath = '',
    [string]$RepoRoot = '',
    [string]$Remote = 'origin',

    [Alias('n')]
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function ConvertTo-Slug {
    param([string]$Value)
    $slug = $Value.ToLowerInvariant() -replace '[^a-z0-9._-]+', '-'
    $slug = $slug.Trim('-')
    if ([string]::IsNullOrWhiteSpace($slug)) { return 'feature' }
    return $slug
}

function Normalize-Slashes {
    param([string]$Value)
    $v = $Value -replace '\\', '/'
    $v = $v -replace '/+', '/'
    return $v.TrimEnd('/')
}

function Invoke-Git {
    $gitArgs = $args
    $stdout = New-Object System.Collections.Generic.List[string]
    $stderr = New-Object System.Collections.Generic.List[string]
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & git @gitArgs 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) { $stderr.Add("$_") } else { $stdout.Add("$_") }
        }
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previous
    }
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = ($stdout -join "`n").Trim()
        Error = ($stderr -join "`n").Trim()
    }
}

function Assert-GitSuccess($Result, [string]$Command) {
    if ($Result.ExitCode -ne 0) {
        $text = (@($Result.Error, $Result.Output) | Where-Object { $_ }) -join "`n"
        $detail = if ($text) { ": $text" } else { '' }
        throw "$Command failed with exit code $($Result.ExitCode)$detail"
    }
}

$ok = $true
$errorMessage = ''
$resolvedRepoRoot = ''
$resolvedWorktreePath = ''
$branchCreated = $false
$worktreeCreated = $false
$worktreeExisted = $false

try {
    # 1. Resolve repository root
    if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
        $rootResult = Invoke-Git rev-parse --show-toplevel
        if ($rootResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($rootResult.Output)) {
            throw 'not inside a git repository'
        }
        $resolvedRepoRoot = (Resolve-Path -LiteralPath $rootResult.Output).Path
    }
    else {
        if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
            throw "repository root does not exist: $RepoRoot"
        }
        $resolvedRepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
    }

    Set-Location $resolvedRepoRoot

    # 2. Derive feature slug and target branch name
    $featureSlug = ConvertTo-Slug $Feature
    if ([string]::IsNullOrWhiteSpace($Branch)) {
        $Branch = $featureSlug
    }

    # 3. Determine base ref
    if ([string]::IsNullOrWhiteSpace($Base)) {
        $currentBranch = (Invoke-Git branch --show-current).Output
        if ([string]::IsNullOrWhiteSpace($currentBranch)) {
            $Base = 'HEAD'
        }
        else {
            $Base = $currentBranch
        }
    }

    # 4. Resolve worktree destination path
    # Default: ../<repo-name>.worktrees/<feature-slug>
    $repoName = Split-Path -Leaf $resolvedRepoRoot
    $parentDir = Split-Path -Parent $resolvedRepoRoot

    if ([string]::IsNullOrWhiteSpace($WorktreePath)) {
        $worktreeParentDir = Join-Path $parentDir "$repoName.worktrees"
        $resolvedWorktreePath = Join-Path $worktreeParentDir $featureSlug
    }
    else {
        if ([System.IO.Path]::IsPathRooted($WorktreePath)) {
            $resolvedWorktreePath = [System.IO.Path]::GetFullPath($WorktreePath)
        }
        else {
            $resolvedWorktreePath = [System.IO.Path]::GetFullPath((Join-Path $resolvedRepoRoot $WorktreePath))
        }
    }

    $normWorktreePath = Normalize-Slashes $resolvedWorktreePath

    # 5. Check if worktree is already registered in git
    $worktreeListResult = Invoke-Git worktree list --porcelain
    Assert-GitSuccess $worktreeListResult 'git worktree list'
    $existingWorktrees = New-Object System.Collections.Generic.List[string]
    $lines = $worktreeListResult.Output -split "`n"
    foreach ($line in $lines) {
        if ($line -match '^worktree\s+(.+)$') {
            $wt = $Matches[1].Trim()
            try {
                $existingWorktrees.Add((Normalize-Slashes ([System.IO.Path]::GetFullPath($wt))))
            }
            catch {
                $existingWorktrees.Add((Normalize-Slashes $wt))
            }
        }
    }

    $registeredPath = $null
    foreach ($existingWorktree in $existingWorktrees) {
        if ($existingWorktree -ieq $normWorktreePath) {
            $registeredPath = $existingWorktree
            break
        }
    }

    if ($null -ne $registeredPath) {
        $worktreeExisted = $true
        $existingBranch = (Invoke-Git -C $registeredPath branch --show-current).Output
        if ($existingBranch -cne $Branch) {
            throw "worktree path is already registered on branch '$existingBranch', not requested branch '$Branch': $resolvedWorktreePath"
        }
    }
    elseif (Test-Path -LiteralPath $resolvedWorktreePath) {
        throw "target directory exists but is not registered as a git worktree: $resolvedWorktreePath"
    }

    # 6. Validate the base and create a worktree when requested
    $branchExists = (Invoke-Git show-ref --verify --quiet "refs/heads/$Branch").ExitCode -eq 0

    if (-not $worktreeExisted -and -not $DryRun) {
        $fetchResult = Invoke-Git fetch $Remote --quiet
        Assert-GitSuccess $fetchResult "git fetch $Remote"
    }

    $baseResult = Invoke-Git rev-parse --verify "$Base^{commit}"
    if ($baseResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($baseResult.Output)) {
        throw "base ref does not resolve to a commit: $Base"
    }

    if (-not $worktreeExisted -and -not $DryRun) {
        # Ensure parent container directory exists
        $destParent = Split-Path -Parent $resolvedWorktreePath
        if (-not (Test-Path -LiteralPath $destParent -PathType Container)) {
            New-Item -ItemType Directory -Path $destParent -Force | Out-Null
        }

        if ($branchExists) {
            $addResult = Invoke-Git worktree add $resolvedWorktreePath $Branch
            Assert-GitSuccess $addResult 'git worktree add'
        }
        else {
            $addResult = Invoke-Git worktree add -b $Branch $resolvedWorktreePath $Base
            Assert-GitSuccess $addResult 'git worktree add -b'
            $branchCreated = $true
        }
        $worktreeCreated = $true
    }
}
catch {
    $ok = $false
    $errorMessage = $_.Exception.Message
}

$result = [ordered]@{
    ok = $ok
    error = $errorMessage
    repoRoot = Normalize-Slashes $resolvedRepoRoot
    worktreePath = Normalize-Slashes $resolvedWorktreePath
    feature = $Feature
    featureSlug = $featureSlug
    branch = $Branch
    base = $Base
    branchCreated = [bool]$branchCreated
    worktreeCreated = [bool]$worktreeCreated
    worktreeExisted = [bool]$worktreeExisted
    dryRun = [bool]$DryRun
}

$result | ConvertTo-Json -Depth 4

if (-not $ok) { exit 1 }
