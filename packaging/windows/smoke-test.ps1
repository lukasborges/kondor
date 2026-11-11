# Offscreen smoke test of a deployed Kondor folder: runs bin\kondor.exe for 15 s and fails on QML
# errors or an early non-zero exit.
#   powershell -ExecutionPolicy Bypass -File packaging\windows\smoke-test.ps1 -Folder build-win\dist\Kondor
param([Parameter(Mandatory)] [string] $Folder)
$ErrorActionPreference = 'Stop'
$exe = (Resolve-Path "$Folder\bin\kondor.exe").Path
$log = Join-Path ([IO.Path]::GetTempPath()) 'kondor-smoke'
New-Item -ItemType Directory -Force $log | Out-Null
$env:QT_QPA_PLATFORM = 'offscreen'
# kondor.exe has no console, so ask Qt to print its messages to the debugger-less stderr via a file.
$env:QT_LOGGING_TO_CONSOLE = '1'
$process = Start-Process $exe -ArgumentList '--new-instance' -PassThru `
    -RedirectStandardOutput "$log\out.txt" -RedirectStandardError "$log\err.txt"
if ($process.WaitForExit(15000)) {
    Get-Content "$log\out.txt", "$log\err.txt" -ErrorAction SilentlyContinue
    if ($process.ExitCode -ne 0) { throw "kondor.exe exited early with code $($process.ExitCode)" }
    throw 'kondor.exe exited before the 15 s were up'
}
$process.Kill()
$output = Get-Content "$log\out.txt", "$log\err.txt" -ErrorAction SilentlyContinue
$output
if ($output -match 'ReferenceError|TypeError|Cannot assign|is not a type') {
    throw 'QML errors in the smoke test output'
}
'Smoke test passed'
