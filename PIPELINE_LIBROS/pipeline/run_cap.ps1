param([string]$Book, [string]$Cap = '07', [int]$Workers = 3)
$env:PYTHONIOENCODING = 'utf-8'
$log = "C:\Users\Usuario\AppData\Local\Temp\opencode\cap${Cap}_$Book.log"
'' | Set-Content $log
if ($Book -eq 'BENGIO') {
    Set-Location (Join-Path $PSScriptRoot '..\..\BENGIO_traduccion\pipeline')
} else {
    Set-Location $PSScriptRoot
    $env:BOOK = $Book
}
foreach ($step in 'transcribe', 'translate') {
    "=== $step $(Get-Date -f HH:mm:ss)" | Add-Content $log
    python "$step.py" $Cap --workers $Workers 2>&1 | Add-Content $log
}
"=== render $(Get-Date -f HH:mm:ss)" | Add-Content $log
python render.py $Cap 2>&1 | Add-Content $log
"FIN $(Get-Date -f HH:mm:ss)" | Add-Content $log
