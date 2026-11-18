"""Datos de prueba propios: las pruebas no leen ni modifican data/ del proyecto."""
import json
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PROYECTO = Path(__file__).resolve().parents[2]

PRODUCTOS = {
    "bebidas": [
        {"id": "espresso", "nombre": "Espresso", "sabor": "amargo", "temperatura": "caliente", "precio": "8.00",
         "franjas": ["manana", "tarde"], "acompanamientos": ["croissant", "brownie"]},
        {"id": "capuchino", "nombre": "Capuchino", "sabor": "suave", "temperatura": "caliente", "precio": "10",
         "franjas": ["manana", "tarde", "noche"], "acompanamientos": ["croissant"]},
        {"id": "frappe_mocha", "nombre": "Frappe mocha", "sabor": "dulce", "temperatura": "fria", "precio": "12.50",
         "franjas": ["tarde", "noche"], "acompanamientos": ["brownie"]},
        {"id": "te_helado", "nombre": "Te helado", "sabor": "citrico", "temperatura": "fria", "precio": "9.00",
         "franjas": ["manana", "tarde"], "acompanamientos": ["croissant"]},
    ],
    "acompanamientos": [
        {"id": "croissant", "nombre": "Croissant", "sabor": "suave", "precio": "7.00"},
        {"id": "brownie", "nombre": "Brownie", "sabor": "dulce", "precio": "6.00"},
    ],
}
CLIENTES = [
    {"nombre": "Ana", "sabor": "dulce", "temperatura": "fria"},
    {"nombre": "Carlos", "sabor": "amargo", "temperatura": "fria"},
]


def carpeta_datos(productos=None, clientes=None, texto_productos: str | None = None) -> Path:
    """Crea una carpeta temporal con data/*.json y devuelve su ruta."""
    raiz = Path(tempfile.mkdtemp(prefix="cafeteria-prueba-"))
    (raiz / "data").mkdir()
    if texto_productos is not None:
        (raiz / "data" / "productos.json").write_bytes(texto_productos.encode("utf-8"))
    else:
        (raiz / "data" / "productos.json").write_text(json.dumps(productos or PRODUCTOS), encoding="utf-8")
    (raiz / "data" / "clientes.json").write_text(json.dumps(CLIENTES if clientes is None else clientes),
                                                 encoding="utf-8")
    (raiz / "data" / "resultados.json").write_text("[]", encoding="utf-8")
    return raiz
