"""Textos que ve el usuario: montos y explicacion de cada recomendacion."""
from decimal import Decimal

from modelos.cliente import etiqueta
from modelos.producto import Catalogo
from modelos.recomendacion import Opcion, ResultadoConsulta


def soles(monto: int | Decimal) -> str:
    """Centimos (int) o soles (Decimal) -> 'S/ 18.50'. Siempre con dos decimales."""
    valor = Decimal(monto) / 100 if isinstance(monto, int) else Decimal(monto)
    return f"S/ {valor:.2f}"


def nombre_opcion(o: Opcion, catalogo: Catalogo) -> str:
    if o.acompanamiento == "ninguno":
        return catalogo.nombre(o.bebida)
    return f"{catalogo.nombre(o.bebida)} + {catalogo.nombre(o.acompanamiento)}"


MARIDAJES = {
    "armonia": "Armonía",
    "contraste": "Contraste",
    "neutro": "Neutro",
    "sin_acompanamiento": "—",
}


def explicacion(o: Opcion, r: ResultadoConsulta, catalogo: Catalogo) -> list[str]:
    """Convierte los motivos inferidos por Prolog en frases."""
    s = r.solicitud
    bebida = catalogo.bebida(o.bebida)
    frases = []
    for motivo in o.motivos:
        if motivo == "sabor_coincide":
            frases.append(f"Coincide con tu sabor preferido: {etiqueta(bebida.sabor).lower()}.")
        elif motivo == "servida_en_franja":
            frases.append(f"Se sirve en la franja de la {etiqueta(r.franja).lower()}.")
        elif motivo == "dentro_del_presupuesto":
            saldo = r.presupuesto_centimos - o.total
            frases.append(f"Cuesta {soles(o.total)}: entra en tu presupuesto de "
                          f"{soles(r.presupuesto_centimos)} y te sobran {soles(saldo)}.")
        elif motivo == "temperatura_exacta":
            frases.append(f"Es {etiqueta(bebida.temperatura).lower()}, como la pediste.")
        elif motivo == "temperatura_cambiada":
            frases.append(f"ALTERNATIVA: la bebida es {etiqueta(bebida.temperatura).lower()} y pediste "
                          f"{etiqueta(s.cliente.temperatura).lower()}. No hay ninguna opción "
                          f"{etiqueta(s.cliente.temperatura).lower()} que cumpla todo lo demás, "
                          f"así que solo se cambió la temperatura.")
        elif motivo == "maridaje_armonia":
            a = catalogo.acompanamiento(o.acompanamiento)
            frases.append(f"Maridaje en armonía: {a.nombre.lower()} comparte el sabor "
                          f"{etiqueta(a.sabor).lower()} de la bebida.")
        elif motivo == "maridaje_contraste":
            a = catalogo.acompanamiento(o.acompanamiento)
            frases.append(f"Maridaje por contraste: el sabor {etiqueta(a.sabor).lower()} de "
                          f"{a.nombre.lower()} complementa lo {etiqueta(bebida.sabor).lower()} de la bebida.")
        elif motivo == "maridaje_neutro":
            frases.append("El acompañamiento está permitido para esta bebida, sin afinidad especial de sabores.")
    if o.destacada:
        frases.append("DESTACADA: es la de mayor puntaje según las reglas (coincidencia y maridaje) "
                      "y, a igual puntaje, la más económica.")
    return frases
