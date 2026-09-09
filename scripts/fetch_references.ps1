$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$IndexPath = Join-Path $ProjectRoot 'references\reference-index.csv'
$AccessedUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$References = @(
    [PSCustomObject]@{
        LocalFile = 'qj\qj-2655-side-1600.jpg'
        Subject = 'QJ 2655 / QJ steam locomotive'
        Component = 'overall silhouette, boiler, cab, running gear'
        View = 'side / three-quarter'
        SourcePage = 'https://commons.wikimedia.org/wiki/File:00_3781_Steam_locomotives_of_China.jpg'
        DirectUrl = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/75/00_3781_Steam_locomotives_of_China.jpg/1920px-00_3781_Steam_locomotives_of_China.jpg'
        Artist = 'W. Bulach'
        License = 'CC BY-SA 4.0'
        LicenseUrl = 'https://creativecommons.org/licenses/by-sa/4.0/'
        Notes = 'QJ 2655 in Technik Museum Speyer; resized Commons thumbnail, no crop.'
    }
    [PSCustomObject]@{
        LocalFile = 'qj\qj-2655-three-quarter-1600.jpg'
        Subject = 'QJ 2655 / QJ steam locomotive'
        Component = 'front, chimney, smoke box, headlamp, buffers'
        View = 'front three-quarter'
        SourcePage = 'https://commons.wikimedia.org/wiki/File:China_Railways_QJ_locomotive.jpg'
        DirectUrl = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/7/71/China_Railways_QJ_locomotive.jpg/1920px-China_Railways_QJ_locomotive.jpg'
        Artist = 'Marcin Wichary'
        License = 'CC BY 2.0'
        LicenseUrl = 'https://creativecommons.org/licenses/by/2.0/'
        Notes = 'QJ 2655 in Technik Museum Speyer; resized Commons thumbnail, no crop.'
    }
    [PSCustomObject]@{
        LocalFile = 'qj\qj-2655-front-detail-1600.jpg'
        Subject = 'QJ 2655 / QJ steam locomotive'
        Component = 'front face, wheel arrangement, pilot, buffers'
        View = 'front / detail'
        SourcePage = 'https://commons.wikimedia.org/wiki/File:CHINESE_STEAM_LOCOMOTIVE_AT_THE_TECHNIK_MUSEUM_SPEYER_GERMANY_APRIL_2013_(8701857639).jpg'
        DirectUrl = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/1/18/CHINESE_STEAM_LOCOMOTIVE_AT_THE_TECHNIK_MUSEUM_SPEYER_GERMANY_APRIL_2013_%288701857639%29.jpg/1920px-CHINESE_STEAM_LOCOMOTIVE_AT_THE_TECHNIK_MUSEUM_SPEYER_GERMANY_APRIL_2013_%288701857639%29.jpg'
        Artist = 'calflier001 / Stephen Mason'
        License = 'CC BY-SA 2.0'
        LicenseUrl = 'https://creativecommons.org/licenses/by-sa/2.0/'
        Notes = 'Chinese steam locomotive identified as QJ 2655; resized Commons thumbnail, no crop.'
    }
    [PSCustomObject]@{
        LocalFile = 'cr400af\cr400af-front-cc0-1600.jpg'
        Subject = 'CR400AF EMU'
        Component = 'nose, windshield, headlights, livery'
        View = 'front three-quarter'
        SourcePage = 'https://commons.wikimedia.org/wiki/File:20240615_CR400AF-2003@G418.jpg'
        DirectUrl = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/4/46/20240615_CR400AF-2003%40G418.jpg/1920px-20240615_CR400AF-2003%40G418.jpg'
        Artist = 'TrainGuyHK102'
        License = 'CC0'
        LicenseUrl = 'https://creativecommons.org/publicdomain/zero/1.0/'
        Notes = 'CR400AF at Shenzhen North; resized Commons thumbnail, no crop.'
    }
    [PSCustomObject]@{
        LocalFile = 'cr400af\cr400af-side-1600.jpg'
        Subject = 'CR400AF EMU'
        Component = 'car body, windows, doors, roof line'
        View = 'side / moving'
        SourcePage = 'https://commons.wikimedia.org/wiki/File:CR400AF-2007_at_Guangnan_(20181107092901).jpg'
        DirectUrl = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a6/CR400AF-2007_at_Guangnan_%2820181107092901%29.jpg/1920px-CR400AF-2007_at_Guangnan_%2820181107092901%29.jpg'
        Artist = 'N509FZ'
        License = 'CC BY-SA 4.0'
        LicenseUrl = 'https://creativecommons.org/licenses/by-sa/4.0/'
        Notes = 'CR400AF side view; resized Commons thumbnail, no crop.'
    }
    [PSCustomObject]@{
        LocalFile = 'cr400af\cr400af-bogie-1600.jpg'
        Subject = 'CR400AF EMU'
        Component = 'bogie, wheelset, suspension, underframe'
        View = 'bogie detail'
        SourcePage = 'https://commons.wikimedia.org/wiki/File:Car_8_bogie_of_CR400AF_(20190517113456).jpg'
        DirectUrl = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b1/Car_8_bogie_of_CR400AF_%2820190517113456%29.jpg/1920px-Car_8_bogie_of_CR400AF_%2820190517113456%29.jpg'
        Artist = 'N509FZ'
        License = 'CC BY-SA 4.0'
        LicenseUrl = 'https://creativecommons.org/licenses/by-sa/4.0/'
        Notes = 'CR400AF bogie detail; resized Commons thumbnail, no crop.'
    }
    [PSCustomObject]@{
        LocalFile = 'cr400af\cr400af-line-scan-1600.jpg'
        Subject = 'CR400AF EMU'
        Component = 'cab end, nose profile, front lighting'
        View = 'long side profile'
        SourcePage = 'https://commons.wikimedia.org/wiki/File:Line_scan_photo_of_CR400AF_ZES206400_dllu.jpg'
        DirectUrl = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d3/Line_scan_photo_of_CR400AF_ZES206400_dllu.jpg/1920px-Line_scan_photo_of_CR400AF_ZES206400_dllu.jpg'
        Artist = 'Dllu'
        License = 'CC BY-SA 4.0'
        LicenseUrl = 'https://creativecommons.org/licenses/by-sa/4.0/'
        Notes = 'CR400AF cab-end line-scan photograph; resized Commons thumbnail, no crop.'
    }
)

$Rows = New-Object System.Collections.Generic.List[object]
foreach ($reference in $References) {
    $outputPath = Join-Path $ProjectRoot ('references\' + $reference.LocalFile)
    $outputDir = Split-Path -Parent $outputPath
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

    Write-Host "Downloading $($reference.LocalFile)"
    Invoke-WebRequest -Uri $reference.DirectUrl -Headers @{ 'User-Agent' = 'AstraTrainProject/1.0 reference archive' } -OutFile $outputPath
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $outputPath).Hash.ToLowerInvariant()

    $Rows.Add([PSCustomObject]@{
        local_file = $reference.LocalFile
        subject = $reference.Subject
        component = $reference.Component
        view = $reference.View
        source_page = $reference.SourcePage
        direct_url = $reference.DirectUrl
        artist = $reference.Artist
        license = $reference.License
        license_url = $reference.LicenseUrl
        accessed_utc = $AccessedUtc
        sha256 = $hash
        notes = $reference.Notes
    })
}

$Rows | Export-Csv -LiteralPath $IndexPath -NoTypeInformation -Encoding UTF8
Write-Host "Wrote $($Rows.Count) records to $IndexPath"

