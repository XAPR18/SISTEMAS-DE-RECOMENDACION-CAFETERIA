"""Ejecuta todas las pruebas: Scala, Prolog y Python (unitarias e integracion).

Uso desde la raiz del proyecto:  py scripts/probar_todo.py
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "python" / "src"))

from utils import herramientas  # noqa: E402


def paso(titulo: str, comando: list[str], cwd: Path) -> bool:
    print(f"\n=== {titulo} ===", flush=True)
    r = subprocess.run(comando, cwd=cwd)
    print("OK" if r.returncode == 0 else f"FALLO (codigo {r.returncode})", flush=True)
    return r.returncode == 0


def main() -> int:
    print("Compilando Scala (principal y pruebas)...", flush=True)
    herramientas.compilar_scala(RAIZ, con_pruebas=True)
    java = herramientas.buscar_java()
    swipl = herramientas.buscar_swipl(RAIZ)
    resultados = [
        paso("Pruebas Scala", [java, "-cp", herramientas.classpath_scala(RAIZ, con_pruebas=True), "app.Pruebas"], RAIZ),
        paso("Pruebas Prolog", [swipl, "-q", "-s", "pruebas.pl", "-g", "run_tests", "-t", "halt"], RAIZ / "prolog"),
        paso("Pruebas Python e integracion de los tres lenguajes",
             [sys.executable, "-m", "unittest", "-v"], RAIZ / "python" / "tests"),
    ]
    print("\n" + ("TODAS LAS PRUEBAS SUPERADAS" if all(resultados) else "HAY PRUEBAS QUE FALLARON"))
    return 0 if all(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
