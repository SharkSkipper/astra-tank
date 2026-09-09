[CmdletBinding()]
param([int]$Port = 4173)
$ErrorActionPreference = 'Stop'
$AtlasRoot = $PSScriptRoot
$Node = (Get-Command node -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath (Join-Path $AtlasRoot 'dist/index.html'))) {
    throw 'Missing dist/index.html. Run npm ci and npm run build in this folder first.'
}
$env:ATLAS_PORT = $Port.ToString()
$AtlasProcess = Start-Process -FilePath $Node -ArgumentList 'scripts/serve.mjs' -WorkingDirectory $AtlasRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $AtlasRoot 'server.log') -RedirectStandardError (Join-Path $AtlasRoot 'server-error.log')
Start-Sleep -Milliseconds 600
Get-Content -LiteralPath (Join-Path $AtlasRoot 'server.log')
Write-Output "Server process: $($AtlasProcess.Id)"
