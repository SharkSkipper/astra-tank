[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('qj', 'cr400af')]
    [string]$Subject,

    [Parameter(Mandatory = $true)]
    [ValidateSet('initial', 'repair', 'human-finish')]
    [string]$Stage,

    [Parameter(Mandatory = $true)]
    [string]$PromptPath,

    [string[]]$ReferenceIds,

    [string]$RunId
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RunsRoot = Join-Path $ProjectRoot 'runs'
$IndexPath = Join-Path $ProjectRoot 'references\reference-index.csv'
$PromptSource = (Resolve-Path -LiteralPath $PromptPath).Path

$DefaultReferences = @{
    qj = @('QJ-side', 'QJ-three-quarter', 'QJ-front-detail')
    cr400af = @('CR400AF-front', 'CR400AF-side', 'CR400AF-bogie', 'CR400AF-line-scan')
}
if (-not $ReferenceIds -or $ReferenceIds.Count -eq 0) {
    $ReferenceIds = $DefaultReferences[$Subject]
}

if (-not $RunId) {
    $RunId = '{0}_{1}_{2}' -f (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd_HHmmss'), $Subject, $Stage
}
$RunPath = Join-Path $RunsRoot $RunId
if (Test-Path -LiteralPath $RunPath) {
    throw "Run directory already exists: $RunPath"
}

$ReferenceIdByFile = @{
    'qj\qj-2655-side-1600.jpg' = 'QJ-side'
    'qj\qj-2655-three-quarter-1600.jpg' = 'QJ-three-quarter'
    'qj\qj-2655-front-detail-1600.jpg' = 'QJ-front-detail'
    'cr400af\cr400af-front-cc0-1600.jpg' = 'CR400AF-front'
    'cr400af\cr400af-side-1600.jpg' = 'CR400AF-side'
    'cr400af\cr400af-bogie-1600.jpg' = 'CR400AF-bogie'
    'cr400af\cr400af-line-scan-1600.jpg' = 'CR400AF-line-scan'
}

$allRows = Import-Csv -LiteralPath $IndexPath
$usedRows = foreach ($row in $allRows) {
    $normalizedFile = $row.local_file.Replace('/', '\')
    $referenceId = $ReferenceIdByFile[$normalizedFile]
    if ($ReferenceIds -contains $referenceId) {
        [PSCustomObject]@{
            reference_id = $referenceId
            local_file = $row.local_file
            subject = $row.subject
            component = $row.component
            view = $row.view
            source_page = $row.source_page
            direct_url = $row.direct_url
            artist = $row.artist
            license = $row.license
            license_url = $row.license_url
            accessed_utc = $row.accessed_utc
            sha256 = $row.sha256
            notes = $row.notes
        }
    }
}
if (-not $usedRows) {
    throw "No reference rows matched: $($ReferenceIds -join ', ')"
}

New-Item -ItemType Directory -Path $RunPath, (Join-Path $RunPath 'checkpoints'), (Join-Path $RunPath 'exports') | Out-Null
Copy-Item -LiteralPath $PromptSource -Destination (Join-Path $RunPath 'prompt.md')
$usedRows | Export-Csv -LiteralPath (Join-Path $RunPath 'reference-used.csv') -NoTypeInformation -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $RunsRoot 'run-log-template.csv') -Destination (Join-Path $RunPath 'run-log.csv')

@"
# Manual intervention log

No intervention has been recorded yet. Add one row for every human edit with:

- UTC timestamp
- affected object or component
- reason for taking over
- before/after checkpoint names
- evidence used to make the correction
"@ | Set-Content -LiteralPath (Join-Path $RunPath 'manual-interventions.md') -Encoding UTF8

@"
# Checkpoint policy

Store the untouched AI result as `v00_ai_initial.blend` before repairs.
Store each repair as `v01_ai_repair.blend`, `v02_ai_repair.blend`, and so on.
Store the last human-edited file as `v99_human_finish.blend` only after logging
the intervention in `manual-interventions.md`.
"@ | Set-Content -LiteralPath (Join-Path $RunPath 'checkpoints\README.md') -Encoding UTF8

@"
{
  "subject": "$Subject",
  "stage": "$Stage",
  "status": "awaiting_capture",
  "created_utc": "$((Get-Date).ToUniversalTime().ToString('o'))",
  "prompt_file": "prompt.md",
  "reference_file": "reference-used.csv",
  "screen_recording": "screen-recording.mkv",
  "recording_note": "Place the untouched full-screen recording here after capture; do not create a placeholder video."
}
"@ | Set-Content -LiteralPath (Join-Path $RunPath 'capture-status.json') -Encoding UTF8

@"
Place the untouched full-screen recording at this path after the Astra run:

screen-recording.mkv

This marker is intentionally not a media file. The run is incomplete until the
real recording, checkpoints, and logs are present.
"@ | Set-Content -LiteralPath (Join-Path $RunPath 'screen-recording.required.txt') -Encoding UTF8

Write-Output "Created Astra run archive: $RunPath"
