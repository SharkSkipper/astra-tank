[CmdletBinding()]
param(
    [int]$Port = 41738
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Node = (Get-Command node -ErrorAction Stop).Source
$Existing = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if ($Existing) {
    Write-Output "Viewer already listening at http://localhost:$Port/viewer/"
    exit 0
}

$env:ASTRA_TRAIN_PORT = $Port.ToString()
$Process = Start-Process -FilePath $Node -ArgumentList @((Join-Path $ProjectRoot 'scripts\serve_viewer.mjs')) -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru
Start-Sleep -Milliseconds 500
$Healthy = $false
try {
    $Response = Invoke-WebRequest -UseBasicParsing "http://localhost:$Port/viewer/" -TimeoutSec 3
    $Healthy = $Response.StatusCode -eq 200
} catch {
    $Healthy = $false
}
if (-not $Healthy) {
    Stop-Process -Id $Process.Id -ErrorAction SilentlyContinue
    throw "Viewer failed to start on port $Port."
}
Write-Output "Viewer started in background at http://localhost:$Port/viewer/ (PID $($Process.Id))"
