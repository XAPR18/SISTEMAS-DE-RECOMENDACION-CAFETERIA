"""Sistema experto de recomendacion para una cafeteria (Scala + Prolog + Python).

Uso (desde la raiz del proyecto):
    py python/src/main.py                    interfaz grafica
    py python/src/main.py --consola          interfaz de texto
    py python/src/main.py --web              interfaz web (http://127.0.0.1:8000)
    py python/src/main.py --exportar-hechos  regenera prolog/hechos.pl y termina
"""
import argparse
import sys

from integracion.integrador import Integrador
from utils import archivos, herramientas


def main() -> int:
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Sistema experto de la cafeteria")
    parser.add_argument("--consola", action="store_true", help="usar la interfaz de texto")
    parser.add_argument("--web", action="store_true", help="abrir la interfaz web en el navegador")
    parser.add_argument("--puerto", type=int, default=8000, help="puerto de la interfaz web (por defecto 8000)")
    parser.add_argument("--sin-navegador", action="store_true", help="con --web: no abrir el navegador")
    parser.add_argument("--exportar-hechos", action="store_true", help="regenerar prolog/hechos.pl")
    args = parser.parse_args()

    try:
        sistema = Integrador()  # Python obtiene y valida los datos de data/*.json
    except archivos.DatosInvalidos as e:
        print(f"No se pudo iniciar: {e}", file=sys.stderr)
        return 1

    if args.exportar_hechos:
        print("prolog/hechos.pl actualizado desde data/*.json.")
        return 0

    if args.web:
        from web import servidor
        try:
            servidor.ejecutar(sistema, args.puerto, abrir_navegador=not args.sin_navegador)
        except (herramientas.HerramientaNoEncontrada, RuntimeError) as e:
            print(f"No se pudo preparar el sistema: {e}", file=sys.stderr)
            return 1
        except OSError as e:
            print(f"No se pudo abrir el puerto {args.puerto}: {e}. Prueba con --puerto 8080.", file=sys.stderr)
            return 1
        return 0

    if args.consola:
        from interfaz import consola
        try:
            consola.ejecutar(sistema)
        except (herramientas.HerramientaNoEncontrada, RuntimeError) as e:
            print(f"No se pudo preparar el sistema: {e}", file=sys.stderr)
            return 1
        return 0

    try:
        from interfaz import ventana
    except ImportError as e:  # Python sin tkinter
        print(f"No hay soporte grafico ({e}). Usa --consola.", file=sys.stderr)
        return 1
    ventana.ejecutar(sistema)
    return 0


if __name__ == "__main__":
    sys.exit(main())
