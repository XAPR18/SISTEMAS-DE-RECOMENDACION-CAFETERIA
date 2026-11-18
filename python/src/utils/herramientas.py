"""Ubica Java, SWI-Prolog y Scala, y compila el modulo Scala cuando hace falta."""
import os
import shutil
import subprocess
from pathlib import Path

VERSION_SCALA = "2.13.16"


class HerramientaNoEncontrada(Exception):
    pass


def proyecto_raiz() -> Path:
    # python/src/utils/herramientas.py -> raiz del proyecto
    return Path(__file__).resolve().parents[3]


def buscar_java() -> str:
    candidatos = []
    programas = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Java"
    candidatos += sorted(programas.glob("jdk-21*/bin/java.exe"))
    if os.environ.get("JAVA_HOME"):
        candidatos.append(Path(os.environ["JAVA_HOME"]) / "bin" / ("java.exe" if os.name == "nt" else "java"))
    for c in candidatos:
        if c.is_file():
            return str(c)
    encontrado = shutil.which("java")
    if encontrado:
        return encontrado
    raise HerramientaNoEncontrada("No se encontro Java. Instala un JDK (recomendado: 21).")


def buscar_swipl(proyecto: Path) -> str:
    variable = os.environ.get("SWIPL", "").strip().strip('"')
    candidatos = [Path(variable)] if variable else []
    candidatos += [proyecto / "tools" / "swipl" / "bin" / "swipl.exe",
                   Path("C:/Program Files/swipl/bin/swipl.exe"),
                   Path("C:/Program Files (x86)/swipl/bin/swipl.exe")]
    for c in candidatos:
        if c.is_file():
            return str(c)
    encontrado = shutil.which("swipl")
    if encontrado:
        return encontrado
    raise HerramientaNoEncontrada("No se encontro SWI-Prolog. Revisa tools/swipl o define la variable SWIPL.")


def _jar(proyecto: Path, nombre: str) -> Path:
    ruta = proyecto / "tools" / f"scala-{VERSION_SCALA}" / f"{nombre}-{VERSION_SCALA}.jar"
    if not ruta.is_file():
        raise HerramientaNoEncontrada(f"Falta {ruta}. Revisa la carpeta tools (ver README).")
    return ruta


def classpath_scala(proyecto: Path, con_pruebas: bool = False) -> str:
    partes = [proyecto / "scala" / "target" / "classes"]
    if con_pruebas:
        partes.append(proyecto / "scala" / "target" / "test-classes")
    partes.append(_jar(proyecto, "scala-library"))
    return os.pathsep.join(str(p) for p in partes)


def _fuentes(carpeta: Path) -> list[Path]:
    return sorted(carpeta.rglob("*.scala"))


def _desactualizado(fuentes: list[Path], destino: Path) -> bool:
    marca = destino / ".compilado"
    if not marca.exists():
        return True
    hecho = marca.stat().st_mtime
    return any(f.stat().st_mtime > hecho for f in fuentes)


def _compilar(proyecto: Path, fuentes: list[Path], destino: Path, classpath_extra: str = "") -> None:
    compilador = os.pathsep.join(str(_jar(proyecto, n)) for n in ("scala-compiler", "scala-library", "scala-reflect"))
    destino.mkdir(parents=True, exist_ok=True)
    comando = [buscar_java(), "-cp", compilador, "scala.tools.nsc.Main", "-usejavacp",
               "-encoding", "UTF-8", "-deprecation", "-feature", "-unchecked", "-d", str(destino)]
    if classpath_extra:
        comando += ["-classpath", classpath_extra]
    comando += [str(f) for f in fuentes]
    r = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    if r.returncode != 0:
        raise RuntimeError("La compilacion de Scala fallo:\n" + (r.stdout + r.stderr).strip())
    (destino / ".compilado").touch()


def compilar_scala(proyecto: Path, con_pruebas: bool = False, forzar: bool = False) -> bool:
    """Compila src/main (y src/test si se pide) solo si hay cambios. Devuelve True si compilo."""
    compilo = False
    principal = _fuentes(proyecto / "scala" / "src" / "main" / "scala")
    clases = proyecto / "scala" / "target" / "classes"
    if forzar or _desactualizado(principal, clases):
        _compilar(proyecto, principal, clases)
        compilo = True
    if con_pruebas:
        pruebas = _fuentes(proyecto / "scala" / "src" / "test" / "scala")
        destino = proyecto / "scala" / "target" / "test-classes"
        if compilo or forzar or _desactualizado(pruebas, destino):
            _compilar(proyecto, pruebas, destino, classpath_extra=str(clases))
            compilo = True
    return compilo
