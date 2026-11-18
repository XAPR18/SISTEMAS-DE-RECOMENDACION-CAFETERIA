"""Comunicacion Python -> Prolog.

Python envia como hechos Prolog: el catalogo, los precios totales calculados
por Scala y la solicitud normalizada por Scala. Prolog aplica sus reglas y
responde una linea JSON. stdout y stderr se leen por separado: un aviso de
Prolog nunca se confunde con la respuesta.
"""
import json
import re
import subprocess
from pathlib import Path

from integracion.errores import IntegracionError, SolicitudRechazada
from modelos.producto import Catalogo
from utils import herramientas
from utils.archivos import centimos

TIEMPO_MAXIMO = 15
_ATOMO = re.compile(r"[a-z][a-z0-9_]*")


def _atomo(valor: str) -> str:
    # Solo se envian codigos validados: nunca texto libre del usuario.
    if not isinstance(valor, str) or not _ATOMO.fullmatch(valor):
        raise IntegracionError(f"Valor no permitido para Prolog: {valor!r}")
    return valor


def _entero(valor) -> int:
    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        raise IntegracionError(f"Monto no permitido para Prolog: {valor!r}")
    return valor


def hechos_para_prolog(catalogo: Catalogo, datos_scala: dict) -> str:
    lineas = []
    for b in catalogo.bebidas:
        lineas.append(f"producto({_atomo(b.id)},bebida,{_atomo(b.sabor)},{_atomo(b.temperatura)},{centimos(b.precio)}).")
        lineas += [f"servido_en({b.id},{_atomo(f)})." for f in b.franjas]
        lineas += [f"combina({b.id},{_atomo(a)})." for a in b.acompanamientos]
    for a in catalogo.acompanamientos:
        lineas.append(f"producto({_atomo(a.id)},acompanamiento,{_atomo(a.sabor)},ninguna,{centimos(a.precio)}).")
    # Precios procesados por Scala
    for o in datos_scala["opciones"]:
        lineas.append(f"precio_opcion({_atomo(o['bebida'])},{_atomo(o['acompanamiento'])},{_entero(o['total'])}).")
    s = datos_scala["solicitud"]
    lineas.append(f"solicitud({_atomo(s['sabor'])},{_atomo(s['temperatura'])},{_entero(s['presupuesto'])},"
                  f"{_atomo(s['modo'])},{_atomo(s['franja'])}).")
    return "\n".join(lineas) + "\n"


def consultar_prolog(proyecto: Path, catalogo: Catalogo, datos_scala: dict) -> dict:
    comando = [herramientas.buscar_swipl(proyecto), "-q", "-s",
               str(proyecto / "prolog" / "consultas.pl"), "-g", "cli", "-t", "halt"]
    try:
        r = subprocess.run(comando, input=hechos_para_prolog(catalogo, datos_scala), capture_output=True,
                           text=True, encoding="utf-8", timeout=TIEMPO_MAXIMO, cwd=proyecto / "prolog")
    except subprocess.TimeoutExpired:
        raise IntegracionError(f"Prolog supero el tiempo de espera de {TIEMPO_MAXIMO} s.") from None
    except OSError as e:
        raise IntegracionError(f"No se pudo ejecutar SWI-Prolog: {e}") from None

    error = r.stderr.strip()
    if r.returncode == 2 and "Cafeteria:" in error:
        raise SolicitudRechazada("Prolog rechazo la solicitud: " + error.split("Cafeteria:", 1)[1].strip())
    if r.returncode != 0:
        raise IntegracionError(f"Prolog termino con error (codigo {r.returncode}): {error[:600]}")
    try:
        respuesta = json.loads(r.stdout.strip())
    except json.JSONDecodeError:
        raise IntegracionError(f"Respuesta de Prolog ilegible: {r.stdout.strip()[:300]}") from None
    if not isinstance(respuesta, dict) or not isinstance(respuesta.get("opciones"), list):
        raise IntegracionError("Respuesta de Prolog sin lista de opciones.")
    return respuesta
