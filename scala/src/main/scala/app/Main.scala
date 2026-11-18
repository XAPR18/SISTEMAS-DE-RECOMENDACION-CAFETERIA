package app

import app.servicios._
import scala.io.{Codec, Source}

// Modulo de procesamiento llamado por Python (python/src/integracion/scala_service.py).
// Lee la solicitud y el catalogo por la entrada estandar y responde una sola linea JSON.
// Codigo de salida: 0 = correcto, 2 = solicitud o datos invalidos.
object Main {
  def ejecutar(lineas: List[String]): Either[String, String] =
    EntradaService.interpretar(lineas).map { case (solicitud, catalogo) =>
      JsonService.resultado(ProcesamientoService.procesar(solicitud, catalogo))
    }

  def main(args: Array[String]): Unit = {
    val lineas = Source.fromInputStream(System.in)(Codec.UTF8).getLines().toList
    ejecutar(lineas) match {
      case Right(json) => println(json)
      case Left(error) =>
        println(JsonService.error(error))
        sys.exit(2)
    }
  }
}
