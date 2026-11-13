param([string]$Book)
$env:PYTHONIOENCODING = 'utf-8'
$log = "C:\Users\Usuario\AppData\Local\Temp\opencode\render_$Book.log"
'' | Set-Content $log
if ($Book -eq 'BENGIO') { Set-Location (Join-Path $PSScriptRoot '..\..\BENGIO_traduccion\pipeline') }
else { Set-Location $PSScriptRoot; $env:BOOK = $Book }
python render.py 01 02 03 04 05 06 07 2>&1 | Add-Content $log
"FIN" | Add-Content $log
