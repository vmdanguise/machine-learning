$env:PYTHONIOENCODING = 'utf-8'
Set-Location $PSScriptRoot
$log = 'C:\Users\Usuario\AppData\Local\Temp\opencode\registro_run.log'
'' | Set-Content $log
foreach ($b in 'FUNDAMENTALS', 'BENGIO', 'BISHOP', 'DUDAHART', 'GONZALEZ') {
    python fix_registro.py $b 01 02 03 04 05 06 2>&1 | Add-Content $log
}
'FIN' | Add-Content $log
