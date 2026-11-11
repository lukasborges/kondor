# Sets up KDE Craft (MSVC 2022, binary cache), builds Kondor and deploys it.
#   powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1 [-CraftRoot C:\CraftRoot]
#       [-HunspellDir <folder with en_US/pt_BR .dic and .aff>] [-Output build-win\dist\Kondor]
# Needs Visual Studio 2022 (C++ workload + Windows SDK), Git for Windows and Python 3.
# Used by CI (build.yml, release.yml) and documented in the README.
param(
    [string] $CraftRoot = $(if ($env:KONDOR_CRAFT_ROOT) { $env:KONDOR_CRAFT_ROOT } else { 'C:\CraftRoot' }),
    [Parameter(Mandatory)] [string] $HunspellDir,
    [string] $BuildDir = 'build-win',
    [string] $Output = 'build-win\dist\Kondor'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $repo

function Enter-Craft {
    $callerErrorAction = $ErrorActionPreference
    # craftenv.ps1 resets the console cursor, which throws without a real console (CI).
    $script:ErrorActionPreference = 'Continue'
    . "$CraftRoot\craft\craftenv.ps1" 2>$null | Out-Null
    $script:ErrorActionPreference = $callerErrorAction
}

if (-not (Test-Path "$CraftRoot\craft\craftenv.ps1")) {
    $python = Get-Command py -ErrorAction SilentlyContinue
    if (-not $python) { $python = Get-Command python -ErrorAction Stop }
    $bootstrapDir = Join-Path ([IO.Path]::GetTempPath()) 'kondor-craft-bootstrap'
    New-Item -ItemType Directory -Force $bootstrapDir | Out-Null
    Invoke-WebRequest https://raw.githubusercontent.com/KDE/craft/master/setup/CraftBootstrap.py `
        -OutFile "$bootstrapDir\CraftBootstrap.py"
    & $python.Source -I "$bootstrapDir\CraftBootstrap.py" --prefix $CraftRoot --use-defaults
    if ($LASTEXITCODE -ne 0) { throw "Craft bootstrap failed ($LASTEXITCODE)" }
}
Enter-Craft

$packages = Get-Content "$PSScriptRoot\craft-packages.txt" | Where-Object { $_.Trim() -and -not $_.StartsWith('#') }
craft @packages
if ($LASTEXITCODE -ne 0) { throw "craft failed ($LASTEXITCODE)" }

cmake -S . -B $BuildDir -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_PREFIX_PATH=$CraftRoot" `
    -DBUILD_TESTING=OFF "-DKONDOR_HUNSPELL_DIR=$HunspellDir"
if ($LASTEXITCODE -ne 0) { throw "cmake configure failed ($LASTEXITCODE)" }
cmake --build $BuildDir --parallel 4
if ($LASTEXITCODE -ne 0) { throw "cmake build failed ($LASTEXITCODE)" }

& "$PSScriptRoot\deploy.ps1" -CraftRoot $CraftRoot -BuildDir $BuildDir -Output $Output
if ($LASTEXITCODE -ne 0) { throw "deploy failed ($LASTEXITCODE)" }
