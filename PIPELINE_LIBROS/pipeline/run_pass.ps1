param([string]$Script, [string]$Book, [string]$Caps, [string]$Extra = '')
# Corre una pasada (fix_registro.py / fix_ingles.py) para un libro y deja log en Temp\opencode\<script>_<book>.log
$env:PYTHONIOENCODING = 'utf-8'
Set-Location $PSScriptRoot
$name = [IO.Path]::GetFileNameWithoutExtension($Script)
$log = "C:\Users\Usuario\AppData\Local\Temp\opencode\${name}_$Book.log"
"=== $Script $Book $Caps $(Get-Date -Format HH:mm:ss)" | Set-Content $log
$a = @($Script, $Book) + ($Caps -split ' ')
if ($Extra) { $a += ($Extra -split ' ') }
python @a 2>&1 | Add-Content $log
"FIN $(Get-Date -Format HH:mm:ss)" | Add-Content $log
