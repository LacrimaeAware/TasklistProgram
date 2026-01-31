Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path .\.venv)) {
  py -3 -m venv .venv
}

$py = Join-Path .venv 'Scripts\python.exe'

if (Test-Path .\requirements.txt) {
  & $py -m pip install -r requirements.txt | Out-Null
}

& $py -m tasklistprogram
