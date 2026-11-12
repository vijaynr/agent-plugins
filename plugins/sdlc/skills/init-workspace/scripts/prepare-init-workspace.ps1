[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Feature,

    [string]$Subdir = '',
    [string]$Root = '',

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

function Get-BaseSlug {
    param([string]$Value)
    return ($Value -replace '-[0-9]+$', '')
}

function Get-SimilarFeatureFolders {
    param([string]$WantedSlug, [string]$BaseFeaturesDir = '.features')
    if (-not (Test-Path -LiteralPath $BaseFeaturesDir -PathType Container)) { return @() }
    $wantedBase = Get-BaseSlug $WantedSlug
    $matches = @()
    Get-ChildItem -LiteralPath $BaseFeaturesDir -Directory | Sort-Object Name | ForEach-Object {
        $slug = ConvertTo-Slug $_.Name
        $slugBase = Get-BaseSlug $slug
        if ($slug -eq $WantedSlug -or
            $slugBase -eq $wantedBase -or
            $slug.StartsWith("$WantedSlug-") -or
            $WantedSlug.StartsWith("$slug-") -or
            $slugBase -eq $WantedSlug -or
            $wantedBase -eq $slug) {
            $matches += "$BaseFeaturesDir/$($_.Name)"
        }
    }
    return $matches
}

$inputNorm = Normalize-Slashes $Feature
$subdirNorm = (Normalize-Slashes $Subdir).TrimStart('/')
$rootNorm = Normalize-Slashes $Root
$featuresPrefix = if ([string]::IsNullOrWhiteSpace($rootNorm)) { '.features' } else { "$rootNorm/.features" }

$looksLikePath = (
    $inputNorm.StartsWith('.features/') -or
    $inputNorm.Contains('/.features/') -or
    $inputNorm.StartsWith('/') -or
    $inputNorm.StartsWith('./') -or
    $inputNorm.StartsWith('../') -or
    ($inputNorm -match '^[A-Za-z]:/')
)

$matchedSimilar = $false
$ambiguous = $false
$similarFolders = @()

if ($looksLikePath) {
    $featureFolder = $inputNorm
    if (-not (Test-Path -LiteralPath $featureFolder -PathType Container)) {
        $similarFolders = @(Get-SimilarFeatureFolders (ConvertTo-Slug (Split-Path -Leaf $featureFolder)) $featuresPrefix)
        if ($similarFolders.Count -eq 1) {
            $featureFolder = $similarFolders[0]
            $matchedSimilar = $true
        }
        elseif ($similarFolders.Count -gt 1) {
            $ambiguous = $true
        }
    }
}
else {
    $inputSlug = ConvertTo-Slug $inputNorm
    $exactFeatureFolder = "$featuresPrefix/$inputNorm"
    $slugFeatureFolder = "$featuresPrefix/$inputSlug"
    if (Test-Path -LiteralPath $exactFeatureFolder -PathType Container) {
        $featureFolder = $exactFeatureFolder
    }
    elseif (Test-Path -LiteralPath $slugFeatureFolder -PathType Container) {
        $featureFolder = $slugFeatureFolder
    }
    else {
        $similarFolders = @(Get-SimilarFeatureFolders $inputSlug $featuresPrefix)
        if ($similarFolders.Count -eq 1) {
            $featureFolder = $similarFolders[0]
            $matchedSimilar = $true
        }
        elseif ($similarFolders.Count -gt 1) {
            $featureFolder = $slugFeatureFolder
            $ambiguous = $true
        }
        else {
            $featureFolder = $slugFeatureFolder
        }
    }
}

if (-not [string]::IsNullOrWhiteSpace($subdirNorm) -and $featureFolder.EndsWith("/$subdirNorm")) {
    $featureFolder = $featureFolder.Substring(0, $featureFolder.Length - ("/$subdirNorm").Length)
}

if ([string]::IsNullOrWhiteSpace($subdirNorm)) {
    $artifactWorkspace = $featureFolder
}
else {
    $artifactWorkspace = "$featureFolder/$subdirNorm"
}

$featureExisted = Test-Path -LiteralPath $featureFolder -PathType Container
$workspaceExisted = Test-Path -LiteralPath $artifactWorkspace -PathType Container
$createdFeature = $false
$createdWorkspace = $false
$statusPath = "$featureFolder/status.json"
$statusCreated = $false
$ok = $true
$errorMessage = ''

if ($ambiguous) {
    $ok = $false
    $errorMessage = 'multiple similar feature workspaces found; choose one and rerun with its exact path'
}

try {
    if ($ok -and -not $DryRun) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $targetRoot = if ([string]::IsNullOrWhiteSpace($rootNorm)) { '.' } else { $rootNorm }
        & (Join-Path $scriptDir 'ensure-aidd-gitignore.ps1') -Root $targetRoot | Out-Null
        if (-not $featureExisted) {
            New-Item -ItemType Directory -Path $featureFolder -Force | Out-Null
            $createdFeature = $true
        }
        if (-not $workspaceExisted) {
            New-Item -ItemType Directory -Path $artifactWorkspace -Force | Out-Null
            $createdWorkspace = $true
        }
        if (-not (Test-Path -LiteralPath $statusPath -PathType Leaf)) {
            $nowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
            $featureName = $featureFolder -replace '^.*\.features/', ''
            $status = [ordered]@{
                schemaVersion = 1
                feature = $featureName
                featureFolder = $featureFolder
                currentPhase = 'workspace'
                status = 'initialized'
                createdAt = $nowUtc
                updatedAt = $nowUtc
                phases = [ordered]@{
                    workspace = [ordered]@{ status = 'done'; artifact = '.'; updatedAt = $nowUtc }
                    spec = [ordered]@{ status = 'pending'; artifact = 'SPEC.md' }
                    research = [ordered]@{ status = 'optional'; artifact = 'SPEC.md' }
                    design = [ordered]@{ status = 'pending'; artifact = 'SPEC.md|DESIGN.md' }
                    plan = [ordered]@{ status = 'pending'; artifact = 'tasks/PLAN.md' }
                    implement = [ordered]@{ status = 'pending'; artifact = 'tasks/TODO.md' }
                    review = [ordered]@{ status = 'pending'; artifact = 'tasks/TODO.md' }
                    refine = [ordered]@{ status = 'optional'; artifact = 'SPEC.md|tasks/PLAN.md' }
                    ship = [ordered]@{ status = 'pending'; artifact = 'merge-request' }
                }
                blockers = @()
                nextRecommendedPhase = 'spec'
                artifactHashes = [ordered]@{}
                git = [ordered]@{
                    lastVerifiedCommit = $null
                    latestSddCommits = @()
                }
                evidence = [ordered]@{
                    verification = [ordered]@{ status = 'pending'; timestamp = $null; summary = $null }
                }
                history = @([ordered]@{ phase = 'workspace'; status = 'done'; timestamp = $nowUtc; summary = 'Feature workspace initialized.' })
            }
            $status | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusPath -Encoding UTF8
            $statusCreated = $true
        }
    }
}
catch {
    $ok = $false
    $errorMessage = $_.Exception.Message
}

$result = [ordered]@{
    ok = $ok
    error = $errorMessage
    root = if ([string]::IsNullOrWhiteSpace($rootNorm)) { '.' } else { $rootNorm }
    featureInput = $Feature
    featureFolder = $featureFolder
    featureWorkspace = $featureFolder
    artifactSubdir = $subdirNorm
    artifactWorkspace = $artifactWorkspace
    featureFolderExisted = $featureExisted
    workspaceExisted = $workspaceExisted
    createdFeatureFolder = $createdFeature
    createdWorkspace = $createdWorkspace
    statusPath = $statusPath
    statusCreated = $statusCreated
    matchedSimilarFeatureFolder = $matchedSimilar
    ambiguous = $ambiguous
    similarFeatureFolders = $similarFolders
    dryRun = [bool]$DryRun
}

$result | ConvertTo-Json -Depth 4

if (-not $ok) { exit 1 }
