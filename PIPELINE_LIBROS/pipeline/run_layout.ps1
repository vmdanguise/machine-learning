param([string]$Cap = '08')
# Layout de un capitulo NUEVO en los 5 libros (no usar en caps ya hechos: BISHOP 01-02 y BENGIO tienen recortes manuales)
$env:PYTHONIOENCODING = 'utf-8'
Set-Location $PSScriptRoot
$log = "C:\Users\Usuario\AppData\Local\Temp\opencode\layout$Cap.log"
'' | Set-Content $log
foreach ($b in 'BISHOP', 'FUNDAMENTALS', 'GONZALEZ', 'DUDAHART') {
    "=== $b" | Add-Content $log
    $env:BOOK = $b
    python layout.py $Cap 2>&1 | Add-Content $log
}
Set-Location '..\..\BENGIO_traduccion\pipeline'
"=== BENGIO" | Add-Content $log
python layout.py $Cap 2>&1 | Add-Content $log
'FIN' | Add-Content $log
