"""Pruebas de extremo a extremo: Python -> Scala -> Python -> Prolog -> Python.

Ejecutan los procesos reales de Java y SWI-Prolog con un catalogo de prueba.
"""
import json
import shutil
import unittest
from decimal import Decimal

import apoyo
from apoyo import PROYECTO, carpeta_datos
from integracion import prolog_service, scala_service
from integracion.errores import IntegracionError, SolicitudRechazada
from integracion.integrador import Integrador
from modelos.cliente import Cliente
from modelos.recomendacion import Solicitud
from utils import archivos, herramientas
from utils.formato import explicacion, nombre_opcion, soles


class PruebasIntegracion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        herramientas.compilar_scala(PROYECTO)
        cls.raiz = carpeta_datos()
        cls.sistema = Integrador(proyecto=PROYECTO, datos=cls.raiz, generar_hechos=False)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.raiz, ignore_errors=True)

    def consultar(self, sabor, temp, presupuesto, modo, franja, hora=None, guardar=False):
        s = Solicitud(Cliente("Prueba", sabor, temp), Decimal(presupuesto), modo, franja)
        return self.sistema.recomendar(s, hora_actual=hora, guardar=guardar)

    def resumen(self, r):
        return [(o.tipo, o.bebida, o.acompanamiento, o.total, o.destacada) for o in r.opciones]

    # ------------------------------------------------------------ reglas
    def test_combo_exacto(self):
        r = self.consultar("dulce", "fria", "20", "combo", "tarde")
        self.assertEqual(self.resumen(r), [("exacta", "frappe_mocha", "brownie", 1850, True)])
        self.assertEqual(r.opciones[0].maridaje, "armonia")

    def test_presupuesto_exacto_y_un_centimo_menos(self):
        self.assertEqual(len(self.consultar("dulce", "fria", "18.50", "combo", "tarde").opciones), 1)
        self.assertEqual(self.consultar("dulce", "fria", "18.49", "combo", "tarde").opciones, [])

    def test_no_cambia_horario(self):
        self.assertEqual(self.consultar("dulce", "fria", "20", "sola", "manana").opciones, [])

    def test_varios_combos_ordenados_y_destacada(self):
        r = self.consultar("amargo", "caliente", "20", "combo", "manana")
        self.assertEqual(self.resumen(r), [("exacta", "espresso", "brownie", 1400, True),
                                           ("exacta", "espresso", "croissant", 1500, False)])

    def test_alternativa_de_temperatura(self):
        r = self.consultar("amargo", "fria", "20", "combo", "tarde")
        self.assertTrue(r.opciones and all(o.tipo == "alternativa" for o in r.opciones))
        frases = explicacion(r.opciones[0], r, self.sistema.catalogo)
        self.assertTrue(any(f.startswith("ALTERNATIVA") and "pediste fría" in f for f in frases))

    def test_franja_automatica_la_calcula_scala(self):
        r = self.consultar("suave", "caliente", "20", "sola", "auto", hora=20)
        self.assertEqual((r.franja, r.franja_automatica), ("noche", True))
        self.assertEqual(self.resumen(r), [("exacta", "capuchino", "ninguno", 1000, True)])

    def test_resumen_de_scala(self):
        r = self.consultar("dulce", "fria", "20", "combo", "tarde")
        self.assertEqual(r.resumen_scala["opciones_generadas"], 5)   # combos compatibles del catalogo
        self.assertEqual(r.resumen_scala["precio_minimo"], 1400)
        self.assertEqual([p.modulo for p in r.pasos], ["Python", "Scala", "Python", "Prolog", "Python"])

    def test_guarda_historial_en_la_carpeta_de_datos(self):
        r = self.consultar("citrico", "fria", "9", "sola", "manana", guardar=True)
        historial = archivos.leer_resultados(self.raiz)
        self.assertEqual(historial[-1]["destacada"], f"{nombre_opcion(r.destacada, self.sistema.catalogo)} "
                                                     f"({soles(900)}, exacta)")

    # ------------------------------------------------------------ errores
    def test_scala_rechaza_solicitud_invalida(self):
        s = Solicitud(Cliente("Prueba", "picante", "fria"), Decimal("20"), "sola", "tarde")
        with self.assertRaisesRegex(SolicitudRechazada, "Scala"):
            scala_service.procesar_con_scala(PROYECTO, s, self.sistema.catalogo, 10)

    def test_prolog_rechaza_hecho_no_permitido(self):
        datos = {"opciones": [], "solicitud": {"sabor": "dulce", "temperatura": "fria", "presupuesto": 2000,
                                               "modo": "sola", "franja": "tarde"}}
        original = prolog_service.hechos_para_prolog
        prolog_service.hechos_para_prolog = lambda c, d: original(c, d) + "halt.\n"
        try:
            with self.assertRaisesRegex(SolicitudRechazada, "no permitido"):
                prolog_service.consultar_prolog(PROYECTO, self.sistema.catalogo, datos)
        finally:
            prolog_service.hechos_para_prolog = original

    def test_python_no_envia_texto_libre_a_prolog(self):
        datos = {"opciones": [{"bebida": "x'), halt, ('", "acompanamiento": "ninguno", "total": 1}],
                 "solicitud": {"sabor": "dulce", "temperatura": "fria", "presupuesto": 2000,
                               "modo": "sola", "franja": "tarde"}}
        with self.assertRaises(IntegracionError):
            prolog_service.hechos_para_prolog(self.sistema.catalogo, datos)

    def test_respuesta_json_de_scala(self):
        s = Solicitud(Cliente("Prueba", "dulce", "fria"), Decimal("20.5"), "sola", "noche")
        datos = scala_service.procesar_con_scala(PROYECTO, s, self.sistema.catalogo, 10)
        self.assertEqual(datos["solicitud"]["presupuesto"], 2050)
        self.assertEqual(json.loads(json.dumps(datos))["solicitud"]["franja"], "noche")


if __name__ == "__main__":
    unittest.main()
