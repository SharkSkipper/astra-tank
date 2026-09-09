$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Blender = Get-Command blender -ErrorAction SilentlyContinue
if ($Blender) {
    $BlenderExe = $Blender.Source
} else {
    $Candidates = @(
        'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe',
        'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe',
        'C:\Program Files\Blender Foundation\Blender 4.4\blender.exe'
    )
    $BlenderExe = $Candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

if (-not $BlenderExe) {
    throw 'Blender was not found. Install Blender or add blender.exe to PATH.'
}

& $BlenderExe --background --python (Join-Path $ProjectRoot 'scripts\generate_train_models.py')
if ($LASTEXITCODE -ne 0) {
    throw "Blender build failed with exit code $LASTEXITCODE"
}

$RequiredOutputs = @(
    (Join-Path $ProjectRoot 'models\QJ_steam_locomotive.blend'),
    (Join-Path $ProjectRoot 'models\QJ_steam_locomotive.glb'),
    (Join-Path $ProjectRoot 'models\CR400AF_emu.blend'),
    (Join-Path $ProjectRoot 'models\CR400AF_emu.glb'),
    (Join-Path $ProjectRoot 'assets\two_track_baseline_preview.png')
)
foreach ($output in $RequiredOutputs) {
    if (-not (Test-Path -LiteralPath $output)) {
        throw "Blender build did not create required output: $output"
    }
}
