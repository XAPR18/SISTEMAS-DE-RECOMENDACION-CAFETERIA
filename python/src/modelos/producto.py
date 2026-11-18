"""Productos del catalogo. Los precios se guardan como Decimal (sin redondeos de float)."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Bebida:
    id: str
    nombre: str
    sabor: str
    temperatura: str
    precio: Decimal
    franjas: tuple[str, ...]
    acompanamientos: tuple[str, ...]


@dataclass(frozen=True)
class Acompanamiento:
    id: str
    nombre: str
    sabor: str
    precio: Decimal


@dataclass(frozen=True)
class Catalogo:
    bebidas: tuple[Bebida, ...]
    acompanamientos: tuple[Acompanamiento, ...]

    def bebida(self, ident: str) -> Bebida:
        return next(b for b in self.bebidas if b.id == ident)

    def acompanamiento(self, ident: str) -> Acompanamiento:
        return next(a for a in self.acompanamientos if a.id == ident)

    def nombre(self, ident: str) -> str:
        for p in (*self.bebidas, *self.acompanamientos):
            if p.id == ident:
                return p.nombre
        return ident
