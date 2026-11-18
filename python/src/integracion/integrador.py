"""Integrador del sistema: Python coordina a Scala y a Prolog.

Flujo de cada consulta (seccion 12 de la guia del curso):
    1. Python obtiene los datos (data/*.json) y la solicitud del usuario.
    2. Scala procesa: valida, define la franja y calcula los precios de las opciones.
    3. Python envia a Prolog el catalogo, los precios de Scala y la solicitud.
    4. Prolog infiere: exactas o alternativas, maridaje, puntaje y destacada.
    5. Python muestra el resultado y lo guarda en data/resultados.json.
"""
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from integracion.errores import IntegracionError
from integracion.prolog_service import consultar_prolog
from integracion.scala_service import procesar_con_scala
from modelos.cliente import Cliente
from modelos.recomendacion import Opcion, Paso, ResultadoConsulta, Solicitud
from utils import archivos, herramientas
from utils.formato import nombre_opcion, soles

Avance = Callable[[int, str], None]


class Integrador:
    def __init__(self, proyecto: Path | None = None, datos: Path | None = None, generar_hechos: bool = True):
        self.proyecto = proyecto or herramientas.proyecto_raiz()
        self.datos = datos or self.proyecto        # carpeta que contiene data/
        self.catalogo = archivos.cargar_catalogo(self.datos)
        self.clientes = archivos.cargar_clientes(self.datos)
        if generar_hechos:
            archivos.escribir_hechos(self.proyecto, self.catalogo, self.clientes)

    # ------------------------------------------------------------ preparacion
    def preparar(self) -> bool:
        """Compila Scala si los fuentes cambiaron y comprueba que exista Prolog."""
        compilo = herramientas.compilar_scala(self.proyecto)
        herramientas.buscar_swipl(self.proyecto)
        return compilo

    # ------------------------------------------------------------ perfiles
    def buscar_cliente(self, nombre: str) -> Cliente | None:
        return next((c for c in self.clientes if c.nombre.casefold() == nombre.strip().casefold()), None)

    def guardar_cliente(self, cliente: Cliente) -> None:
        """Agrega o actualiza un perfil en data/clientes.json."""
        existente = self.buscar_cliente(cliente.nombre)
        if existente:
            nuevos = [cliente if c is existente else c for c in self.clientes]
        else:
            nuevos = self.clientes + [cliente]
        archivos.guardar_clientes(self.datos, nuevos)
        self.clientes = nuevos
        if self.datos == self.proyecto:
            archivos.escribir_hechos(self.proyecto, self.catalogo, self.clientes)

    # ------------------------------------------------------------ consulta
    def recomendar(self, solicitud: Solicitud, avance: Avance | None = None,
                   hora_actual: int | None = None, guardar: bool = True) -> ResultadoConsulta:
        avisar = avance or (lambda paso, texto: None)
        pasos: list[Paso] = []
        hora = datetime.now().hour if hora_actual is None else hora_actual

        def medir(numero: int, modulo: str, descripcion: str, accion):
            avisar(numero, descripcion)
            inicio = time.perf_counter()
            valor = accion()
            pasos.append(Paso(modulo, descripcion, int((time.perf_counter() - inicio) * 1000)))
            return valor

        medir(1, "Python", "Python obtiene los datos y la solicitud", lambda: None)
        datos_scala = medir(2, "Scala", "Scala valida y calcula los precios de las opciones",
                            lambda: procesar_con_scala(self.proyecto, solicitud, self.catalogo, hora))
        avisar(3, "Python envía la información a Prolog")
        pasos.append(Paso("Python", f"Python envía a Prolog {len(datos_scala['opciones'])} opciones con precio", 0))
        datos_prolog = medir(4, "Prolog", "Prolog aplica las reglas de inferencia",
                             lambda: consultar_prolog(self.proyecto, self.catalogo, datos_scala))
        avisar(5, "Python arma y muestra el resultado")

        try:
            opciones = [Opcion(tipo=o["tipo"], bebida=o["bebida"], acompanamiento=o["acompanamiento"],
                               total=int(o["total"]), maridaje=o["maridaje"], puntaje=int(o["puntaje"]),
                               destacada=bool(o["destacada"]), motivos=tuple(o["motivos"]))
                        for o in datos_prolog["opciones"]]
            for o in opciones:      # cada producto debe existir en el catalogo
                self.catalogo.bebida(o.bebida)
                if o.acompanamiento != "ninguno":
                    self.catalogo.acompanamiento(o.acompanamiento)
        except (KeyError, TypeError, ValueError, StopIteration):
            raise IntegracionError("Prolog devolvio una opcion incompleta o desconocida.") from None

        s = datos_scala["solicitud"]
        resultado = ResultadoConsulta(
            solicitud=solicitud, franja=s["franja"], franja_automatica=bool(s["franja_automatica"]),
            presupuesto_centimos=int(s["presupuesto"]), opciones=opciones,
            resumen_scala=datos_scala["resumen"], pasos=pasos,
            fecha=datetime.now().isoformat(timespec="seconds"))
        pasos.append(Paso("Python", f"Python presenta {len(opciones)} opciones", 0))
        if guardar:
            archivos.agregar_resultado(self.datos, self._registro(resultado))
        return resultado

    def _registro(self, r: ResultadoConsulta) -> dict:
        d = r.destacada
        return {
            "fecha": r.fecha,
            "cliente": r.solicitud.cliente.nombre,
            "sabor": r.solicitud.cliente.sabor,
            "temperatura": r.solicitud.cliente.temperatura,
            "presupuesto": soles(r.presupuesto_centimos),
            "modo": r.solicitud.modo,
            "franja": r.franja,
            "franja_automatica": r.franja_automatica,
            "total_opciones": len(r.opciones),
            "destacada": f"{nombre_opcion(d, self.catalogo)} ({soles(d.total)}, {d.tipo})" if d else None,
            "opciones": [{"bebida": o.bebida, "acompanamiento": o.acompanamiento, "total": o.total,
                          "tipo": o.tipo, "maridaje": o.maridaje} for o in r.opciones],
        }
