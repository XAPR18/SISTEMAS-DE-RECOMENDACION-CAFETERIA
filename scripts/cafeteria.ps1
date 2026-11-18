param(
    [ValidateSet('Interfaz', 'Web', 'Consola', 'Probar', 'Demo', 'Compilar')]
    [string]$Accion = 'Interfaz'
)
# Lanzador para Windows. Python coordina todo: compila Scala si hace falta,
# y llama a Scala y a Prolog con las herramientas de la carpeta tools/.
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$main = Join-Path $raiz 'python\src\main.py'

function Buscar-Python {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return @($py.Source, '-3') }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python -and $python.Source -notlike '*WindowsApps*') { return @($python.Source) }
    throw 'No se encontro Python 3. Instalalo desde python.org (3.10 o superior).'
}

$python = @(Buscar-Python)
$exe = $python[0]
$extra = @($python | Select-Object -Skip 1)

switch ($Accion) {
    'Interfaz' { & $exe @extra $main }
    'Web'      { & $exe @extra $main --web }
    'Consola'  { & $exe @extra $main --consola }
    'Probar'   { & $exe @extra (Join-Path $raiz 'scripts\probar_todo.py') }
    'Compilar' { & $exe @extra -c "import sys; sys.path.insert(0, r'$raiz\python\src'); from utils import herramientas as h; from pathlib import Path; print('Compilado' if h.compilar_scala(Path(r'$raiz'), con_pruebas=True, forzar=True) else 'Sin cambios')" }
    'Demo' {
        & $exe @extra $main --exportar-hechos
        $swipl = Join-Path $raiz 'tools\swipl\bin\swipl.exe'
        if (-not (Test-Path -LiteralPath $swipl)) { $swipl = 'swipl' }
        Push-Location (Join-Path $raiz 'prolog')
        try { & $swipl -q -s consultas.pl -g demo -t halt } finally { Pop-Location }
    }
}
exit $LASTEXITCODE
