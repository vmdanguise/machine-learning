param([string]$Book, [string]$Caps)
$env:PYTHONIOENCODING = 'utf-8'
$log = "C:\Users\Usuario\AppData\Local\Temp\opencode\rerender_$Book.log"
'' | Set-Content $log
if ($Book -eq 'BENGIO') { Set-Location (Join-Path $PSScriptRoot '..\..\BENGIO_traduccion\pipeline') }
else { Set-Location $PSScriptRoot; $env:BOOK = $Book }
python render.py @($Caps -split ' ') 2>&1 | Add-Content $log
"FIN" | Add-Content $log
