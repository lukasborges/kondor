# Downloads the en_US and pt_BR Hunspell dictionaries from LibreOffice's repository, at a pinned commit.
#   powershell -ExecutionPolicy Bypass -File packaging\windows\fetch-dictionaries.ps1 -Destination <folder>
param([Parameter(Mandatory)] [string] $Destination)
$ErrorActionPreference = 'Stop'
$commit = 'c0865a85eb67dc377f2cf8e8fe2c4fa9e53f0dcb'
New-Item -ItemType Directory -Force $Destination | Out-Null
foreach ($lang in 'en_US', 'pt_BR') {
    $folder = if ($lang -eq 'en_US') { 'en' } else { 'pt_BR' } # en/en_US.*, pt_BR/pt_BR.*
    foreach ($ext in 'dic', 'aff') {
        Invoke-WebRequest "https://raw.githubusercontent.com/LibreOffice/dictionaries/$commit/$folder/$lang.$ext" `
            -OutFile (Join-Path $Destination "$lang.$ext")
    }
}
