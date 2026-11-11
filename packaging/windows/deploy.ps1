# Packs an installed Kondor build into a self-contained folder and Kondor-windows-x86_64.zip.
#   powershell -ExecutionPolicy Bypass -File packaging\windows\deploy.ps1 `
#       -CraftRoot C:\CraftRoot -BuildDir build-win -Output build-win\dist\Kondor
# Run it inside the Craft environment (dumpbin, windeployqt on PATH); build.ps1 does.
param(
    [Parameter(Mandatory)] [string] $CraftRoot,
    [Parameter(Mandatory)] [string] $BuildDir,
    [Parameter(Mandatory)] [string] $Output
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
$out = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
$buildPath = (Resolve-Path $BuildDir).Path
$bin = Join-Path $out 'bin'

if (Test-Path $out) { Remove-Item -Recurse -Force $out }

# 1. kondor.exe and the dictionaries.
cmake --install $buildPath --prefix $out
if ($LASTEXITCODE -ne 0) { throw "cmake --install failed ($LASTEXITCODE)" }

# 2. windeployqt looks for the WebEngine resources in <CraftRoot>\resources; Craft keeps them in bin\.
New-Item -ItemType Directory -Force "$CraftRoot\resources" | Out-Null
Get-ChildItem "$CraftRoot\bin" |
    Where-Object { $_.Name -match '^(icudtl\.dat|v8_context_snapshot\.bin|qtwebengine_.*\.pak)$' } |
    Where-Object { -not (Test-Path "$CraftRoot\resources\$($_.Name)") } |
    Copy-Item -Destination "$CraftRoot\resources"

# 3. Qt libraries, plugins, QML modules. The org.kde.desktop style is set from C++, so import
#    scanning of qml\ never finds it: scan its folder explicitly.
& "$CraftRoot\bin\windeployqt6.exe" --release --qmldir "$repo\qml" --qmldir "$CraftRoot\qml\org\kde\desktop" `
    --qmlimport "$CraftRoot\qml" --no-compiler-runtime --no-system-d3d-compiler --dir $bin "$bin\kondor.exe"
if ($LASTEXITCODE -ne 0) { throw "windeployqt failed ($LASTEXITCODE)" }

# 4. Plugins windeployqt does not know about, keeping their relative paths under bin\.
$kdePlugins = @(
    'kf6\kirigami\platform\org.kde.desktop.dll',
    'styles\breeze6.dll',
    'kiconthemes6\iconengines\KIconEnginePlugin.dll',
    'tls\qopensslbackend.dll'
)
foreach ($plugin in $kdePlugins) {
    $target = Join-Path $bin (Split-Path $plugin -Parent)
    New-Item -ItemType Directory -Force $target | Out-Null
    Copy-Item "$CraftRoot\plugins\$plugin" $target
}
New-Item -ItemType Directory -Force "$bin\data" | Out-Null
Copy-Item -Recurse -Force "$CraftRoot\bin\data\color-schemes" "$bin\data\"

# 5. Non-Qt DLLs the executable and the plugins import, resolved from the PE imports.
$seen = @{}
$pending = New-Object System.Collections.Queue
Get-ChildItem $bin -Recurse -Include *.dll, *.exe | ForEach-Object { $pending.Enqueue($_.FullName) }
while ($pending.Count -gt 0) {
    $imports = & dumpbin /nologo /dependents $pending.Dequeue() |
        Where-Object { $_ -match '^\s+\S+\.dll\s*$' } | ForEach-Object { $_.Trim() }
    foreach ($dll in $imports) {
        $key = $dll.ToLowerInvariant()
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true
        # Already deployed, or part of Windows (not in Craft's bin).
        if ((Test-Path "$bin\$dll") -or -not (Test-Path "$CraftRoot\bin\$dll")) { continue }
        Copy-Item "$CraftRoot\bin\$dll" $bin
        $pending.Enqueue("$bin\$dll")
    }
}

# MSVC runtime next to the executable: no VC++ redistributable needed.
if ($env:VCToolsRedistDir) {
    $crt = Get-ChildItem "${env:VCToolsRedistDir}x64\Microsoft.VC*.CRT" -Directory | Select-Object -First 1
    if ($crt) { Copy-Item "$($crt.FullName)\*.dll" $bin }
}

# 6. License and a start note.
Copy-Item "$repo\LICENSE" $out
Set-Content -Path "$out\README.txt" -Encoding ascii -Value 'Start Kondor Browser with bin\kondor.exe.'

# 7. Fail when something essential is missing.
$required = @(
    'bin\kondor.exe', 'bin\QtWebEngineProcess.exe',
    'bin\qtwebengine_dictionaries\en-US.bdic', 'bin\qtwebengine_dictionaries\pt-BR.bdic',
    'bin\styles\breeze6.dll', 'bin\kf6\kirigami\platform\org.kde.desktop.dll'
)
$missing = $required | Where-Object { -not (Test-Path (Join-Path $out $_)) }
if ($missing) { throw "Deployed folder is missing: $($missing -join ', ')" }

# Zip with `Kondor\` as the top-level folder.
$zip = Join-Path (Split-Path $out -Parent) 'Kondor-windows-x86_64.zip'
if (Test-Path $zip) { Remove-Item $zip }
$staging = Join-Path (Split-Path $out -Parent) 'zip-staging'
if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }
New-Item -ItemType Directory $staging | Out-Null
Move-Item $out "$staging\Kondor"
Compress-Archive -Path "$staging\Kondor" -DestinationPath $zip
Move-Item "$staging\Kondor" $out
Remove-Item $staging
"{0}: {1:N0} MB zipped" -f $zip, ((Get-Item $zip).Length / 1MB)
