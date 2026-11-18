"""Solicitud del usuario y resultado final que arma el integrador."""
from dataclasses import dataclass, field
from decimal import Decimal

from modelos.cliente import Cliente


@dataclass(frozen=True)
class Solicitud:
    cliente: Cliente
    presupuesto: Decimal
    modo: str             # "sola" o "combo"
    franja: str           # "manana", "tarde", "noche" o "auto" (hora de la PC)


@dataclass(frozen=True)
class Opcion:
    tipo: str             # "exacta" o "alternativa"
    bebida: str
    acompanamiento: str   # "ninguno" si es bebida sola
    total: int            # centimos
    maridaje: str
    puntaje: int
    destacada: bool
    motivos: tuple[str, ...]


@dataclass
class Paso:
    modulo: str           # Python, Scala o Prolog
    descripcion: str
    milisegundos: int


@dataclass
class ResultadoConsulta:
    solicitud: Solicitud
    franja: str                   # franja usada (calculada por Scala si era "auto")
    franja_automatica: bool
    presupuesto_centimos: int
    opciones: list[Opcion]
    resumen_scala: dict
    pasos: list[Paso] = field(default_factory=list)
    fecha: str = ""

    @property
    def destacada(self) -> Opcion | None:
        return next((o for o in self.opciones if o.destacada), None)
