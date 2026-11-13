$env:PYTHONIOENCODING = 'utf-8'
Set-Location $PSScriptRoot
$log = 'C:\Users\Usuario\AppData\Local\Temp\opencode\layout07.log'
'' | Set-Content $log
foreach ($b in 'BISHOP', 'FUNDAMENTALS', 'GONZALEZ', 'DUDAHART') {
    "=== $b" | Add-Content $log
    $env:BOOK = $b
    python layout.py 07 2>&1 | Add-Content $log
}
Set-Location '..\..\BENGIO_traduccion\pipeline'
"=== BENGIO" | Add-Content $log
python layout.py 07 2>&1 | Add-Content $log
'FIN' | Add-Content $log
