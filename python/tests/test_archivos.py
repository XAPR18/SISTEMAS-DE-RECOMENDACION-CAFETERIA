import copy
import json
import shutil
import unittest
from decimal import Decimal

import apoyo  # noqa: F401  (agrega python/src al path)
from apoyo import CLIENTES, PRODUCTOS, carpeta_datos
from modelos.cliente import Cliente
from utils import archivos


class PruebasDatos(unittest.TestCase):
    def setUp(self):
        self.carpetas = []

    def tearDown(self):
        for c in self.carpetas:
            shutil.rmtree(c, ignore_errors=True)

    def datos(self, **kwargs):
        c = carpeta_datos(**kwargs)
        self.carpetas.append(c)
        return c

    def productos_con(self, cambio):
        p = copy.deepcopy(PRODUCTOS)
        cambio(p)
        return p

    # -------------------------------------------------------------- montos
    def test_montos_validos(self):
        self.assertEqual(archivos.dinero("20,50"), Decimal("20.50"))
        self.assertEqual(archivos.dinero("8"), Decimal("8.00"))
        self.assertEqual(archivos.dinero(" 12.5 "), Decimal("12.50"))
        self.assertEqual(archivos.centimos(Decimal("18.50")), 1850)

    def test_montos_invalidos(self):
        for m in ["0", "0.00", "-1", "1.234", "NaN", "1e3", "1000000", "", "12.", "abc"]:
            with self.subTest(m=m), self.assertRaises(archivos.DatosInvalidos):
                archivos.dinero(m)

    def test_nombre(self):
        self.assertEqual(archivos.nombre_cliente("  Maria del Carmen O'Connor "), "Maria del Carmen O'Connor")
        for n in ["", "   ", "x" * 61, "a\nb"]:
            with self.subTest(n=n), self.assertRaises(archivos.DatosInvalidos):
                archivos.nombre_cliente(n)

    # ------------------------------------------------------------- catalogo
    def test_catalogo_valido(self):
        c = archivos.cargar_catalogo(self.datos())
        self.assertEqual(len(c.bebidas), 4)
        self.assertEqual(c.bebida("frappe_mocha").precio, Decimal("12.50"))
        self.assertEqual(c.nombre("brownie"), "Brownie")

    def test_catalogo_con_bom(self):
        # Archivo guardado con BOM (Bloc de notas / Excel): ahora se acepta.
        raiz = self.datos(texto_productos="﻿" + json.dumps(PRODUCTOS))
        self.assertEqual(len(archivos.cargar_catalogo(raiz).bebidas), 4)

    def test_sabor_en_mayusculas_rechazado(self):
        p = self.productos_con(lambda p: p["bebidas"][0].update(sabor="AMARGO"))
        with self.assertRaisesRegex(archivos.DatosInvalidos, r"bebidas\[0\]\.sabor"):
            archivos.cargar_catalogo(self.datos(productos=p))

    def test_acompanamiento_inexistente(self):
        p = self.productos_con(lambda p: p["bebidas"][0]["acompanamientos"].append("torta"))
        with self.assertRaisesRegex(archivos.DatosInvalidos, "torta"):
            archivos.cargar_catalogo(self.datos(productos=p))

    def test_id_repetido(self):
        p = self.productos_con(lambda p: p["acompanamientos"].append(dict(p["acompanamientos"][0])))
        with self.assertRaisesRegex(archivos.DatosInvalidos, "repetidos"):
            archivos.cargar_catalogo(self.datos(productos=p))

    def test_precio_invalido(self):
        p = self.productos_con(lambda p: p["bebidas"][1].update(precio="10.999"))
        with self.assertRaisesRegex(archivos.DatosInvalidos, r"bebidas\[1\]\.precio"):
            archivos.cargar_catalogo(self.datos(productos=p))

    def test_json_mal_formado(self):
        with self.assertRaisesRegex(archivos.DatosInvalidos, "mal formado"):
            archivos.cargar_catalogo(self.datos(texto_productos="{ bebidas: "))

    # ------------------------------------------------------------- clientes
    def test_clientes(self):
        raiz = self.datos()
        self.assertEqual(archivos.cargar_clientes(raiz)[0], Cliente("Ana", "dulce", "fria"))

    def test_clientes_repetidos(self):
        raiz = self.datos(clientes=CLIENTES + [{"nombre": "ANA", "sabor": "suave", "temperatura": "fria"}])
        with self.assertRaisesRegex(archivos.DatosInvalidos, "repetidos"):
            archivos.cargar_clientes(raiz)

    def test_cliente_invalido_indica_posicion(self):
        raiz = self.datos(clientes=[{"nombre": "Ana", "sabor": "DULCE", "temperatura": "fria"}])
        with self.assertRaisesRegex(archivos.DatosInvalidos, r"\[0\]\.sabor"):
            archivos.cargar_clientes(raiz)

    def test_guardar_clientes(self):
        raiz = self.datos()
        nuevos = archivos.cargar_clientes(raiz) + [Cliente("José Ñuñez", "citrico", "fria")]
        archivos.guardar_clientes(raiz, nuevos)
        self.assertEqual(archivos.cargar_clientes(raiz), nuevos)

    # ------------------------------------------------------------ historial
    def test_historial_limitado(self):
        raiz = self.datos()
        for i in range(archivos.MAX_HISTORIAL + 5):
            archivos.agregar_resultado(raiz, {"n": i})
        historial = archivos.leer_resultados(raiz)
        self.assertEqual(len(historial), archivos.MAX_HISTORIAL)
        self.assertEqual(historial[-1], {"n": archivos.MAX_HISTORIAL + 4})

    # ------------------------------------------------------------ Prolog
    def test_atomo_prolog_escapa_comillas(self):
        self.assertEqual(archivos.atomo_prolog("O'Connor"), "'O\\'Connor'")
        self.assertEqual(archivos.atomo_prolog("a\\b"), "'a\\\\b'")

    def test_hechos_generados(self):
        raiz = self.datos()
        texto = archivos.hechos_prolog(archivos.cargar_catalogo(raiz), archivos.cargar_clientes(raiz))
        self.assertIn("producto(frappe_mocha, bebida, dulce, fria, 1250).", texto)
        self.assertIn("producto(brownie, acompanamiento, dulce, ninguna, 600).", texto)
        self.assertIn("combina(espresso, brownie).", texto)
        self.assertIn("nombre_cliente(cliente_2, 'Carlos').", texto)


if __name__ == "__main__":
    unittest.main()
