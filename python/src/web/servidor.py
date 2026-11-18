"""Interfaz web: servidor HTTP y API REST con la biblioteca estandar de Python.

El navegador habla solo con Python; Python sigue siendo el integrador:
    Navegador -> Python -> Scala -> Python -> Prolog -> Python -> Navegador

Rutas:
    GET  /                     pagina (static/index.html)
    GET  /api/catalogo         productos, clientes y opciones del formulario
    POST /api/recomendar       ejecuta el flujo completo y devuelve el resultado
    GET  /api/historial        ultimas consultas de data/resultados.json
"""
import json
import mimetypes
import threading
from decimal import Decimal
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from integracion.errores import IntegracionError, SolicitudRechazada
from integracion.integrador import Integrador
from modelos.cliente import ETIQUETAS, FRANJAS, MODOS, SABORES, TEMPERATURAS, Cliente, etiqueta
from modelos.recomendacion import ResultadoConsulta, Solicitud
from utils import archivos
from utils.formato import MARIDAJES, explicacion, nombre_opcion, soles

ESTATICOS = Path(__file__).resolve().parent / "static"
FOTOS = ESTATICOS / "img" / "productos"
MAX_CUERPO = 10_000  # bytes
TIPOS = {
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp",
    ".ico": "image/x-icon",
}


class EntradaInvalida(Exception):
    pass


def foto(ident: str) -> str | None:
    """Ruta publica de la foto real del producto, si existe (img/productos/<id>.jpg|png|webp)."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (FOTOS / f"{ident}.{ext}").is_file():
            return f"/img/productos/{ident}.{ext}"
    return None


class Aplicacion:
    """Logica de la API, separada del servidor HTTP para poder probarla."""

    def __init__(self, sistema: Integrador):
        self.sistema = sistema
        self.candado = threading.Lock()   # una consulta o escritura a la vez

    # ----------------------------------------------------------- catalogo
    def catalogo(self) -> dict:
        c = self.sistema.catalogo
        return {
            "bebidas": [{"id": b.id, "nombre": b.nombre, "sabor": b.sabor, "temperatura": b.temperatura,
                         "precio": soles(b.precio), "franjas": list(b.franjas),
                         "acompanamientos": [c.nombre(a) for a in b.acompanamientos], "foto": foto(b.id)}
                        for b in c.bebidas],
            "acompanamientos": [{"id": a.id, "nombre": a.nombre, "sabor": a.sabor, "precio": soles(a.precio),
                                 "foto": foto(a.id)} for a in c.acompanamientos],
            "clientes": [{"nombre": x.nombre, "sabor": x.sabor, "temperatura": x.temperatura}
                         for x in self.sistema.clientes],
            "opciones": {"sabores": list(SABORES), "temperaturas": list(TEMPERATURAS),
                         "franjas": list(FRANJAS), "modos": list(MODOS)},
            "etiquetas": ETIQUETAS,
        }

    def historial(self) -> list[dict]:
        return list(reversed(archivos.leer_resultados(self.sistema.datos)))[:50]

    # ----------------------------------------------------------- recomendar
    def leer_solicitud(self, datos) -> tuple[Solicitud, bool]:
        if not isinstance(datos, dict):
            raise EntradaInvalida("Se esperaba un objeto JSON.")

        def campo(nombre, permitidos):
            valor = datos.get(nombre)
            if valor not in permitidos:
                raise EntradaInvalida(f"Valor no valido para '{nombre}'.")
            return valor

        try:
            nombre = archivos.nombre_cliente(str(datos.get("nombre", "")))
            presupuesto = archivos.dinero(str(datos.get("presupuesto", "")))
        except archivos.DatosInvalidos as e:
            raise EntradaInvalida(str(e)) from None
        nuevo = bool(datos.get("nuevo"))
        if nuevo and self.sistema.buscar_cliente(nombre):
            raise EntradaInvalida("Ese nombre ya tiene un perfil: elígelo en la lista.")
        if not nuevo and not self.sistema.buscar_cliente(nombre):
            raise EntradaInvalida("El perfil elegido no existe.")
        existente = self.sistema.buscar_cliente(nombre)
        cliente = Cliente(existente.nombre if existente else nombre,
                          campo("sabor", SABORES), campo("temperatura", TEMPERATURAS))
        solicitud = Solicitud(cliente, presupuesto, campo("modo", MODOS), campo("franja", FRANJAS + ("auto",)))
        return solicitud, bool(datos.get("guardar"))

    def recomendar(self, datos) -> dict:
        solicitud, guardar = self.leer_solicitud(datos)
        with self.candado:
            if guardar:
                self.sistema.guardar_cliente(solicitud.cliente)
            r = self.sistema.recomendar(solicitud)
        return self.resultado_json(r)

    def resultado_json(self, r: ResultadoConsulta) -> dict:
        c = self.sistema.catalogo
        opciones = []
        for o in r.opciones:
            b = c.bebida(o.bebida)
            a = c.acompanamiento(o.acompanamiento) if o.acompanamiento != "ninguno" else None
            opciones.append({
                "nombre": nombre_opcion(o, c),
                "tipo": o.tipo,
                "total": soles(o.total),
                "saldo": soles(r.presupuesto_centimos - o.total),
                "maridaje": o.maridaje,
                "maridaje_texto": MARIDAJES[o.maridaje],
                "puntaje": o.puntaje,
                "destacada": o.destacada,
                "explicacion": explicacion(o, r, c),
                "bebida": {"id": b.id, "nombre": b.nombre, "sabor": b.sabor, "temperatura": b.temperatura,
                           "precio": soles(b.precio), "foto": foto(b.id)},
                "acompanamiento": None if a is None else {"id": a.id, "nombre": a.nombre, "sabor": a.sabor,
                                                          "precio": soles(a.precio), "foto": foto(a.id)},
            })
        return {
            "cliente": r.solicitud.cliente.nombre,
            "franja": r.franja,
            "franja_texto": etiqueta(r.franja),
            "franja_automatica": r.franja_automatica,
            "presupuesto": soles(r.presupuesto_centimos),
            "modo": r.solicitud.modo,
            "generadas": r.resumen_scala.get("opciones_generadas", 0),
            "opciones": opciones,
            "pasos": [{"modulo": p.modulo, "descripcion": p.descripcion, "ms": p.milisegundos} for p in r.pasos],
            "clientes": [{"nombre": x.nombre, "sabor": x.sabor, "temperatura": x.temperatura}
                         for x in self.sistema.clientes],
        }


def crear_manejador(app: Aplicacion):
    class Manejador(BaseHTTPRequestHandler):
        server_version = "CafeteriaExperta/1.0"

        def log_message(self, formato, *args):  # silencioso: la consola queda limpia
            pass

        def _responder(self, estado: int, cuerpo: bytes, tipo: str) -> None:
            self.send_response(estado)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store" if tipo.startswith("application/json") else "max-age=300")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(cuerpo)

        def _json(self, estado: int, datos) -> None:
            self._responder(estado, json.dumps(datos, ensure_ascii=False).encode("utf-8"),
                            "application/json; charset=utf-8")

        def _estatico(self, ruta: str) -> None:
            relativa = unquote(ruta).lstrip("/") or "index.html"
            archivo = (ESTATICOS / relativa).resolve()
            # Evita salir de la carpeta static (../../data/clientes.json, etc.)
            if not archivo.is_relative_to(ESTATICOS) or not archivo.is_file():
                self._json(HTTPStatus.NOT_FOUND, {"error": "No encontrado"})
                return
            # Tipos fijos: en Windows, mimetypes lee el registro y puede devolver text/plain para .js
            tipo = TIPOS.get(archivo.suffix.lower()) or mimetypes.guess_type(archivo.name)[0] \
                or "application/octet-stream"
            self._responder(HTTPStatus.OK, archivo.read_bytes(), tipo)

        def do_GET(self):
            ruta = urlparse(self.path).path
            try:
                if ruta == "/api/catalogo":
                    self._json(HTTPStatus.OK, app.catalogo())
                elif ruta == "/api/historial":
                    self._json(HTTPStatus.OK, app.historial())
                elif ruta.startswith("/api/"):
                    self._json(HTTPStatus.NOT_FOUND, {"error": "Ruta desconocida"})
                else:
                    self._estatico(ruta)
            except archivos.DatosInvalidos as e:
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})

        do_HEAD = do_GET

        def do_POST(self):
            if urlparse(self.path).path != "/api/recomendar":
                self._json(HTTPStatus.NOT_FOUND, {"error": "Ruta desconocida"})
                return
            try:
                largo = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                largo = -1
            if not 0 < largo <= MAX_CUERPO:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Cuerpo vacío o demasiado grande."})
                return
            try:
                datos = json.loads(self.rfile.read(largo).decode("utf-8"))
                self._json(HTTPStatus.OK, app.recomendar(datos))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "JSON inválido."})
            except (EntradaInvalida, SolicitudRechazada) as e:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(e)})
            except (IntegracionError, archivos.DatosInvalidos, OSError) as e:
                self._json(HTTPStatus.BAD_GATEWAY, {"error": f"No se pudo completar la consulta: {e}"})

    return Manejador


def crear_servidor(sistema: Integrador, puerto: int = 8000) -> ThreadingHTTPServer:
    # Solo escucha en esta PC (127.0.0.1): no se expone a la red.
    return ThreadingHTTPServer(("127.0.0.1", puerto), crear_manejador(Aplicacion(sistema)))


def ejecutar(sistema: Integrador, puerto: int = 8000, abrir_navegador: bool = True) -> None:
    print("Preparando Scala y Prolog...")
    if sistema.preparar():
        print("(Se compiló el módulo Scala.)")
    servidor = crear_servidor(sistema, puerto)
    url = f"http://127.0.0.1:{servidor.server_address[1]}/"
    print(f"Recomendador web listo en {url}  (Ctrl+C para detener)")
    if abrir_navegador:
        import webbrowser
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()
