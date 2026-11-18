"""Pruebas de la interfaz web: el servidor HTTP real con la API y los archivos estaticos.

Levanta el servidor en un puerto libre de 127.0.0.1 con datos temporales; las consultas
recorren de verdad Python -> Scala -> Python -> Prolog -> Python.
"""
import http.client
import json
import shutil
import threading
import unittest

import apoyo  # noqa: F401  (agrega src al path)
from apoyo import PROYECTO, carpeta_datos
from integracion.integrador import Integrador
from utils import archivos, herramientas
from web import servidor

PEDIDO_ANA = {"nombre": "Ana", "sabor": "dulce", "temperatura": "fria", "presupuesto": "20",
              "modo": "combo", "franja": "tarde"}


class PruebasWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        herramientas.compilar_scala(PROYECTO)
        cls.raiz = carpeta_datos()
        cls.sistema = Integrador(proyecto=PROYECTO, datos=cls.raiz, generar_hechos=False)
        cls.http = servidor.crear_servidor(cls.sistema, puerto=0)   # 0 = puerto libre
        cls.puerto = cls.http.server_address[1]
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        shutil.rmtree(cls.raiz, ignore_errors=True)

    def pedir(self, metodo, ruta, cuerpo=None, crudo: bytes | None = None):
        con = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=60)
        datos = crudo if crudo is not None else (None if cuerpo is None else json.dumps(cuerpo).encode())
        con.request(metodo, ruta, body=datos, headers={"Content-Type": "application/json"} if datos else {})
        r = con.getresponse()
        contenido, tipo = r.read(), r.getheader("Content-Type", "")
        con.close()
        return r.status, tipo, contenido

    def pedir_json(self, metodo, ruta, cuerpo=None, crudo=None):
        estado, tipo, contenido = self.pedir(metodo, ruta, cuerpo, crudo)
        self.assertTrue(tipo.startswith("application/json"), tipo)
        return estado, json.loads(contenido)

    # ------------------------------------------------------------ API
    def test_catalogo(self):
        estado, c = self.pedir_json("GET", "/api/catalogo")
        self.assertEqual(estado, 200)
        self.assertEqual([b["id"] for b in c["bebidas"]], ["espresso", "capuchino", "frappe_mocha", "te_helado"])
        self.assertEqual([x["nombre"] for x in c["clientes"]], ["Ana", "Carlos"])
        capuchino = c["bebidas"][1]
        self.assertEqual(capuchino["precio"], "S/ 10.00")
        self.assertEqual(capuchino["foto"], "/img/productos/capuchino.jpg")   # foto real
        self.assertIsNone(c["bebidas"][3]["foto"])                            # sin foto: ilustracion
        self.assertEqual(c["opciones"]["franjas"], ["manana", "tarde", "noche"])

    def test_recomendar_flujo_completo(self):
        estado, r = self.pedir_json("POST", "/api/recomendar", PEDIDO_ANA)
        self.assertEqual(estado, 200)
        self.assertEqual(len(r["opciones"]), 1)
        o = r["opciones"][0]
        self.assertEqual((o["nombre"], o["total"], o["tipo"], o["destacada"]),
                         ("Frappe mocha + Brownie", "S/ 18.50", "exacta", True))
        self.assertEqual(o["acompanamiento"]["foto"], "/img/productos/brownie.jpg")
        self.assertEqual([p["modulo"] for p in r["pasos"]], ["Python", "Scala", "Python", "Prolog", "Python"])
        # Se guarda en el historial de la carpeta temporal.
        estado, historial = self.pedir_json("GET", "/api/historial")
        self.assertEqual(estado, 200)
        self.assertTrue(any(h.get("cliente") == "Ana" for h in historial))

    def test_perfil_nuevo_se_guarda(self):
        pedido = dict(PEDIDO_ANA, nombre="Lucia", nuevo=True, guardar=True, sabor="citrico", franja="manana")
        estado, r = self.pedir_json("POST", "/api/recomendar", pedido)
        self.assertEqual(estado, 200)
        self.assertIn("Lucia", [c["nombre"] for c in r["clientes"]])
        self.assertIn("Lucia", [c.nombre for c in archivos.cargar_clientes(self.raiz)])

    def test_entradas_invalidas_dan_400(self):
        casos = [
            dict(PEDIDO_ANA, sabor="salado"),
            dict(PEDIDO_ANA, franja="madrugada"),
            dict(PEDIDO_ANA, presupuesto="-5"),
            dict(PEDIDO_ANA, presupuesto="abc"),
            dict(PEDIDO_ANA, nombre="NoExiste"),
            dict(PEDIDO_ANA, nuevo=True),          # Ana ya existe
            ["no", "es", "objeto"],
        ]
        for caso in casos:
            with self.subTest(caso=caso):
                estado, r = self.pedir_json("POST", "/api/recomendar", caso)
                self.assertEqual(estado, 400)
                self.assertIn("error", r)

    def test_cuerpo_mal_formado_o_grande(self):
        self.assertEqual(self.pedir_json("POST", "/api/recomendar", crudo=b"{no es json")[0], 400)
        grande = json.dumps(dict(PEDIDO_ANA, nombre="x" * 20_000)).encode()
        self.assertEqual(self.pedir_json("POST", "/api/recomendar", crudo=grande)[0], 400)

    def test_rutas_desconocidas(self):
        self.assertEqual(self.pedir_json("GET", "/api/nada")[0], 404)
        self.assertEqual(self.pedir_json("POST", "/api/catalogo", PEDIDO_ANA)[0], 404)

    # ------------------------------------------------------------ estaticos
    def test_archivos_estaticos_con_tipo_correcto(self):
        for ruta, tipo in [("/", "text/html"), ("/app.js", "text/javascript"), ("/estilos.css", "text/css"),
                           ("/img/lenguajes/prolog.svg", "image/svg+xml"),
                           ("/img/productos/latte.jpg", "image/jpeg")]:
            with self.subTest(ruta=ruta):
                estado, recibido, _ = self.pedir("GET", ruta)
                self.assertEqual(estado, 200)
                self.assertTrue(recibido.startswith(tipo), recibido)

    def test_no_sale_de_la_carpeta_static(self):
        for ruta in ["/../../../data/clientes.json", "/%2e%2e/%2e%2e/%2e%2e/data/clientes.json",
                     "/..%5c..%5c..%5cdata%5cclientes.json", "/no_existe.html"]:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.pedir("GET", ruta)[0], 404)


if __name__ == "__main__":
    unittest.main()
