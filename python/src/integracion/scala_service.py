"""Comunicacion Python -> Scala.

Python envia la solicitud y el catalogo por la entrada estandar (un registro
por linea) y Scala responde una linea JSON con las opciones y sus precios.
"""
import json
import subprocess
from pathlib import Path

from integracion.errores import IntegracionError, SolicitudRechazada
from modelos.producto import Catalogo
from modelos.recomendacion import Solicitud
from utils import herramientas

TIEMPO_MAXIMO = 30  # segundos (la primera ejecucion de la JVM puede tardar)


def mensaje_para_scala(solicitud: Solicitud, catalogo: Catalogo, hora_actual: int) -> str:
    franja = f"hora={hora_actual}" if solicitud.franja == "auto" else solicitud.franja
    c = solicitud.cliente
    lineas = [f"SOLICITUD|{c.sabor}|{c.temperatura}|{solicitud.presupuesto}|{solicitud.modo}|{franja}"]
    for b in catalogo.bebidas:
        lineas.append(f"BEBIDA|{b.id}|{b.sabor}|{b.temperatura}|{b.precio}|"
                      f"{';'.join(b.franjas)}|{';'.join(b.acompanamientos)}")
    for a in catalogo.acompanamientos:
        lineas.append(f"ACOMP|{a.id}|{a.sabor}|{a.precio}")
    return "\n".join(lineas) + "\n"


def procesar_con_scala(proyecto: Path, solicitud: Solicitud, catalogo: Catalogo, hora_actual: int) -> dict:
    comando = [herramientas.buscar_java(), "-Dfile.encoding=UTF-8", "-cp",
               herramientas.classpath_scala(proyecto), "app.Main"]
    try:
        r = subprocess.run(comando, input=mensaje_para_scala(solicitud, catalogo, hora_actual),
                           capture_output=True, text=True, encoding="utf-8", timeout=TIEMPO_MAXIMO)
    except subprocess.TimeoutExpired:
        raise IntegracionError(f"Scala supero el tiempo de espera de {TIEMPO_MAXIMO} s.") from None
    except OSError as e:
        raise IntegracionError(f"No se pudo ejecutar Java: {e}") from None

    try:
        respuesta = json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else None
    except json.JSONDecodeError:
        respuesta = None
    if r.returncode == 2 and isinstance(respuesta, dict) and "error" in respuesta:
        raise SolicitudRechazada(f"Scala rechazo la solicitud: {respuesta['error']}")
    if r.returncode != 0 or not isinstance(respuesta, dict) or "opciones" not in respuesta:
        detalle = (r.stderr or r.stdout).strip()[:600]
        raise IntegracionError(f"Scala no respondio correctamente (codigo {r.returncode}). {detalle}")
    return respuesta
