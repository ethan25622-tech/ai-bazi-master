$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path $Python)) {
    throw "Bundled Python not found: $Python"
}

& $Python -m bazi_master.cli @args
