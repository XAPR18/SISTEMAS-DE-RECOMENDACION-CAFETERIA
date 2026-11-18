"""Cliente y valores admitidos del dominio (los mismos codigos que Scala y Prolog)."""
from dataclasses import dataclass

SABORES = ("dulce", "amargo", "suave", "citrico")
TEMPERATURAS = ("fria", "caliente")
FRANJAS = ("manana", "tarde", "noche")
MODOS = ("sola", "combo")

# Textos visibles para la interfaz
ETIQUETAS = {
    "dulce": "Dulce", "amargo": "Amargo", "suave": "Suave", "citrico": "Cítrico",
    "fria": "Fría", "caliente": "Caliente",
    "manana": "Mañana", "tarde": "Tarde", "noche": "Noche",
    "sola": "Solo bebida", "combo": "Combo con acompañamiento",
}


def etiqueta(codigo: str) -> str:
    return ETIQUETAS.get(codigo, codigo)


@dataclass(frozen=True)
class Cliente:
    nombre: str
    sabor: str
    temperatura: str
