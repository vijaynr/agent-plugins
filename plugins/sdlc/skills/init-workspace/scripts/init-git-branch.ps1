[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Branch,

    [string]$Base = '',
    [string]$Remote = 'origin',
    [switch]$StashApproved,
    [Alias('n')]
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# Run git without turning stderr text into terminating errors (Windows PowerShell 5.1 does
# that when stderr is redirected). Success comes only from the git exit code. Stdout and
# stderr stay separate, so that a warning on stderr is never read as data.
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

function To-Bool($Value) { return [bool]$Value }

$ok = $true
$errorMessage = ''
$requiresStashApproval = $false
$stashCreated = $false
$branchCreated = $false
$checkedOut = $false
$stashRef = ''
$dirty = $false
$currentBranch = ''
$gitRoot = ''

try {
    $rootResult = Invoke-Git rev-parse --show-toplevel
    if ($rootResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($rootResult.Output)) { throw 'not inside a git repository' }
    $gitRoot = $rootResult.Output
    Set-Location $gitRoot

    $currentBranch = (Invoke-Git branch --show-current).Output
    if ([string]::IsNullOrWhiteSpace($Base)) {
        if ([string]::IsNullOrWhiteSpace($currentBranch)) { $Base = 'HEAD' } else { $Base = $currentBranch }
    }

    $statusResult = Invoke-Git status --porcelain
    Assert-GitSuccess $statusResult 'git status'
    $dirty = -not [string]::IsNullOrWhiteSpace($statusResult.Output)

    $branchExists = (Invoke-Git show-ref --verify --quiet "refs/heads/$Branch").ExitCode -eq 0
    if ($branchExists) {
        $ok = $false
        $errorMessage = "branch already exists: $Branch"
    }
    elseif ($dirty -and -not $StashApproved) {
        $ok = $false
        $requiresStashApproval = $true
        $errorMessage = 'working tree has changes; rerun with -StashApproved after user approval or continue without creating a branch'
    }
    elseif (-not $DryRun) {
        if ($dirty) {
            Assert-GitSuccess (Invoke-Git stash push -u -m "init-workspace before creating $Branch") 'git stash push'
            $stashCreated = $true
            $stashRef = (Invoke-Git stash list -n 1 --format='%gd').Output
        }
        # A failed fetch is not fatal; continue with the local base ref, as the Bash helper does.
        Invoke-Git fetch $Remote --quiet | Out-Null
        $switchResult = Invoke-Git switch -c $Branch $Base
        if ($switchResult.ExitCode -ne 0 -and $stashCreated) {
            $switchResult.Error = "$($switchResult.Error)`nYour changes are in $stashRef. Run 'git stash pop' to restore them.".Trim()
        }
        Assert-GitSuccess $switchResult 'git switch'
        $branchCreated = $true
        $checkedOut = $true
    }
}
catch {
    $ok = $false
    $errorMessage = $_.Exception.Message
}

$result = [ordered]@{
    ok = $ok
    error = $errorMessage
    gitRoot = $gitRoot
    currentBranch = $currentBranch
    requestedBranch = $Branch
    base = $Base
    remote = $Remote
    dirty = [bool]$dirty
    requiresStashApproval = [bool]$requiresStashApproval
    stashApproved = [bool]$StashApproved
    stashCreated = [bool]$stashCreated
    stashRef = $stashRef
    branchCreated = [bool]$branchCreated
    checkedOut = [bool]$checkedOut
    dryRun = [bool]$DryRun
}

$result | ConvertTo-Json -Depth 4

if (-not $ok) { exit 1 }
