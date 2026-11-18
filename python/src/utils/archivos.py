"""Lectura y escritura de data/*.json.

Python es el UNICO modulo que lee los archivos de datos. Scala y Prolog reciben
la informacion ya validada, por eso los tres lenguajes aplican siempre las
mismas reglas (en el avance 1 Scala y Prolog leian los CSV por separado y
podian no coincidir).
"""
import json
import os
import re
from decimal import Decimal
from pathlib import Path

from modelos.cliente import FRANJAS, SABORES, TEMPERATURAS, Cliente
from modelos.producto import Acompanamiento, Bebida, Catalogo

PATRON_ID = re.compile(r"[a-z][a-z0-9_]*")
PATRON_DINERO = re.compile(r"([0-9]{1,6})(?:[.,]([0-9]{1,2}))?")
MAX_HISTORIAL = 200


class DatosInvalidos(Exception):
    """Error en un archivo de datos o en un valor escrito por el usuario."""


# ---------------------------------------------------------------- utilidades
def leer_json(ruta: Path):
    try:
        # utf-8-sig acepta archivos guardados con BOM (Bloc de notas, Excel).
        with open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        raise DatosInvalidos(f"No existe el archivo {ruta}") from None
    except json.JSONDecodeError as e:
        raise DatosInvalidos(f"{ruta.name}: JSON mal formado en la linea {e.lineno}: {e.msg}") from None


def escribir_json(ruta: Path, datos) -> None:
    """Escritura atomica: si el programa se cierra a la mitad, el archivo anterior queda intacto."""
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    with open(temporal, "w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temporal, ruta)


def dinero(texto) -> Decimal:
    """'20', '20.5' o '20,50' -> Decimal con dos decimales. Mismas reglas que Scala."""
    m = PATRON_DINERO.fullmatch(str(texto).strip())
    if not m:
        raise DatosInvalidos(f"Monto invalido '{texto}'. Usa hasta 6 enteros y 2 decimales, por ejemplo 20 o 20,50.")
    valor = Decimal(f"{m.group(1)}.{(m.group(2) or '').ljust(2, '0')}")
    if valor <= 0:
        raise DatosInvalidos("El monto debe ser mayor que cero.")
    return valor


def centimos(valor: Decimal) -> int:
    return int(valor * 100)


def nombre_cliente(texto: str) -> str:
    limpio = (texto or "").strip()
    if not limpio or len(limpio) > 60 or any(ord(c) < 32 for c in limpio):
        raise DatosInvalidos("Escribe un nombre de 1 a 60 caracteres.")
    return limpio


def _codigo(valor, permitidos, donde: str) -> str:
    # Estricto: "DULCE" no se acepta. Asi Python, Scala y Prolog coinciden.
    if valor not in permitidos:
        raise DatosInvalidos(f"{donde}: '{valor}' no es valido. Valores permitidos: {', '.join(permitidos)}.")
    return valor


def _identificador(valor, donde: str) -> str:
    if not isinstance(valor, str) or not PATRON_ID.fullmatch(valor):
        raise DatosInvalidos(f"{donde}: identificador '{valor}' invalido (minusculas, digitos y _).")
    return valor


def _texto(valor, donde: str) -> str:
    if not isinstance(valor, str) or not valor.strip() or len(valor) > 60:
        raise DatosInvalidos(f"{donde}: se esperaba un nombre de 1 a 60 caracteres.")
    return valor.strip()


# ---------------------------------------------------------------- catalogo
def cargar_catalogo(raiz: Path) -> Catalogo:
    datos = leer_json(raiz / "data" / "productos.json")
    if not isinstance(datos, dict) or not isinstance(datos.get("bebidas"), list) \
            or not isinstance(datos.get("acompanamientos"), list):
        raise DatosInvalidos("productos.json: se esperaban las listas 'bebidas' y 'acompanamientos'.")

    acompanamientos = []
    for i, a in enumerate(datos["acompanamientos"]):
        donde = f"productos.json: acompanamientos[{i}]"
        if not isinstance(a, dict):
            raise DatosInvalidos(f"{donde}: se esperaba un objeto.")
        acompanamientos.append(Acompanamiento(
            id=_identificador(a.get("id"), donde),
            nombre=_texto(a.get("nombre"), donde),
            sabor=_codigo(a.get("sabor"), SABORES, f"{donde}.sabor"),
            precio=_precio(a.get("precio"), donde),
        ))
    ids_acomp = {a.id for a in acompanamientos}

    bebidas = []
    for i, b in enumerate(datos["bebidas"]):
        donde = f"productos.json: bebidas[{i}]"
        if not isinstance(b, dict):
            raise DatosInvalidos(f"{donde}: se esperaba un objeto.")
        franjas = b.get("franjas")
        combina = b.get("acompanamientos", [])
        if not isinstance(franjas, list) or not franjas:
            raise DatosInvalidos(f"{donde}.franjas: indica al menos una franja.")
        if not isinstance(combina, list):
            raise DatosInvalidos(f"{donde}.acompanamientos: se esperaba una lista.")
        for f in franjas:
            _codigo(f, FRANJAS, f"{donde}.franjas")
        for a in combina:
            if a not in ids_acomp:
                raise DatosInvalidos(f"{donde}.acompanamientos: '{a}' no existe en el catalogo.")
        if len(set(franjas)) != len(franjas) or len(set(combina)) != len(combina):
            raise DatosInvalidos(f"{donde}: hay franjas o acompanamientos repetidos.")
        bebidas.append(Bebida(
            id=_identificador(b.get("id"), donde),
            nombre=_texto(b.get("nombre"), donde),
            sabor=_codigo(b.get("sabor"), SABORES, f"{donde}.sabor"),
            temperatura=_codigo(b.get("temperatura"), TEMPERATURAS, f"{donde}.temperatura"),
            precio=_precio(b.get("precio"), donde),
            franjas=tuple(franjas),
            acompanamientos=tuple(combina),
        ))

    if not bebidas:
        raise DatosInvalidos("productos.json: el catalogo no tiene bebidas.")
    ids = [p.id for p in (*bebidas, *acompanamientos)]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        raise DatosInvalidos(f"productos.json: identificadores repetidos: {', '.join(repetidos)}.")
    return Catalogo(tuple(bebidas), tuple(acompanamientos))


def _precio(valor, donde: str) -> Decimal:
    if isinstance(valor, bool) or not isinstance(valor, (str, int, float)):
        raise DatosInvalidos(f"{donde}.precio: se esperaba un monto como \"8.50\".")
    try:
        return dinero(valor)
    except DatosInvalidos as e:
        raise DatosInvalidos(f"{donde}.precio: {e}") from None


# ---------------------------------------------------------------- clientes
def cargar_clientes(raiz: Path) -> list[Cliente]:
    datos = leer_json(raiz / "data" / "clientes.json")
    if not isinstance(datos, list):
        raise DatosInvalidos("clientes.json: se esperaba una lista de clientes.")
    clientes = []
    for i, c in enumerate(datos):
        donde = f"clientes.json: [{i}]"
        if not isinstance(c, dict):
            raise DatosInvalidos(f"{donde}: se esperaba un objeto.")
        try:
            nombre = nombre_cliente(c.get("nombre"))
        except DatosInvalidos as e:
            raise DatosInvalidos(f"{donde}.nombre: {e}") from None
        clientes.append(Cliente(nombre,
                                _codigo(c.get("sabor"), SABORES, f"{donde}.sabor"),
                                _codigo(c.get("temperatura"), TEMPERATURAS, f"{donde}.temperatura")))
    nombres = [c.nombre.casefold() for c in clientes]
    if len(set(nombres)) != len(nombres):
        raise DatosInvalidos("clientes.json: hay nombres de clientes repetidos.")
    return clientes


def guardar_clientes(raiz: Path, clientes: list[Cliente]) -> None:
    escribir_json(raiz / "data" / "clientes.json",
                  [{"nombre": c.nombre, "sabor": c.sabor, "temperatura": c.temperatura} for c in clientes])


# ---------------------------------------------------------------- historial
def leer_resultados(raiz: Path) -> list[dict]:
    ruta = raiz / "data" / "resultados.json"
    if not ruta.exists():
        return []
    datos = leer_json(ruta)
    return datos if isinstance(datos, list) else []


def agregar_resultado(raiz: Path, registro: dict) -> None:
    historial = leer_resultados(raiz)
    historial.append(registro)
    escribir_json(raiz / "data" / "resultados.json", historial[-MAX_HISTORIAL:])


# ---------------------------------------------------------------- Prolog
def atomo_prolog(texto: str) -> str:
    """Texto libre -> atomo Prolog entre comillas simples, con escapes."""
    return "'" + texto.replace("\\", "\\\\").replace("'", "\\'") + "'"


def hechos_prolog(catalogo: Catalogo, clientes: list[Cliente]) -> str:
    """Base de conocimiento legible para usar Prolog por separado (prolog/hechos.pl)."""
    lineas = [
        "% ARCHIVO GENERADO por Python desde data/productos.json y data/clientes.json.",
        "% No editar a mano: los cambios se hacen en los JSON y se regenera al iniciar.",
        "% Precios en centimos: 1250 representa S/ 12,50.",
        "",
        "% producto(Id, Categoria, Sabor, Temperatura, Precio).",
    ]
    for b in catalogo.bebidas:
        lineas.append(f"producto({b.id}, bebida, {b.sabor}, {b.temperatura}, {centimos(b.precio)}).")
    for a in catalogo.acompanamientos:
        lineas.append(f"producto({a.id}, acompanamiento, {a.sabor}, ninguna, {centimos(a.precio)}).")
    lineas += ["", "% nombre_producto(Id, NombreVisible)."]
    for p in (*catalogo.bebidas, *catalogo.acompanamientos):
        lineas.append(f"nombre_producto({p.id}, {atomo_prolog(p.nombre)}).")
    lineas += ["", "% servido_en(Bebida, Franja)."]
    for b in catalogo.bebidas:
        lineas += [f"servido_en({b.id}, {f})." for f in b.franjas]
    lineas += ["", "% combina(Bebida, Acompanamiento)."]
    for b in catalogo.bebidas:
        lineas += [f"combina({b.id}, {a})." for a in b.acompanamientos]
    numerados = list(enumerate(clientes, 1))
    lineas += ["", "% nombre_cliente(Id, NombreVisible)."]
    lineas += [f"nombre_cliente(cliente_{i}, {atomo_prolog(c.nombre)})." for i, c in numerados]
    lineas += ["", "% gusto(Cliente, Sabor)."]
    lineas += [f"gusto(cliente_{i}, {c.sabor})." for i, c in numerados]
    lineas += ["", "% prefiere(Cliente, Temperatura)."]
    lineas += [f"prefiere(cliente_{i}, {c.temperatura})." for i, c in numerados]
    return "\n".join(lineas) + "\n"


def escribir_hechos(proyecto: Path, catalogo: Catalogo, clientes: list[Cliente]) -> bool:
    """Regenera prolog/hechos.pl solo si cambio. Devuelve True si lo reescribio."""
    ruta = proyecto / "prolog" / "hechos.pl"
    contenido = hechos_prolog(catalogo, clientes)
    if ruta.exists() and ruta.read_text(encoding="utf-8") == contenido:
        return False
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    return True
