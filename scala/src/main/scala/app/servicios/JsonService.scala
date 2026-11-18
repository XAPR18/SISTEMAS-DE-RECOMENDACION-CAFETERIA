package app.servicios

import app.modelos._

// Escritor JSON minimo, sin bibliotecas externas.
object JsonService {
  def texto(s: String): String = {
    val escapado = s.flatMap {
      case '"' => "\\\""
      case '\\' => "\\\\"
      case '\n' => "\\n"
      case '\r' => "\\r"
      case '\t' => "\\t"
      case c if c < ' ' => f"\\u${c.toInt}%04x"
      case c => c.toString
    }
    "\"" + escapado + "\""
  }

  private def objeto(campos: List[(String, String)]): String =
    campos.map { case (k, v) => s"${texto(k)}:$v" }.mkString("{", ",", "}")

  private def numero(n: Option[Long]): String = n.map(_.toString).getOrElse("null")

  def error(mensaje: String): String = objeto(List("error" -> texto(mensaje)))

  def resultado(r: ResultadoProcesamiento): String = {
    val s = r.solicitud
    val solicitud = objeto(List(
      "sabor" -> texto(s.sabor.codigo),
      "temperatura" -> texto(s.temperatura.codigo),
      "presupuesto" -> s.presupuesto.toString,
      "modo" -> texto(s.modo.codigo),
      "franja" -> texto(s.franja.codigo),
      "franja_automatica" -> s.franjaAutomatica.toString
    ))
    val opciones = r.opciones.map(o => objeto(List(
      "bebida" -> texto(o.bebida.id),
      "acompanamiento" -> texto(o.idAcompanamiento),
      "total" -> o.total.toString
    ))).mkString("[", ",", "]")
    val res = r.resumen
    val porSabor = objeto(res.opcionesPorSabor.toList.sortBy(_._1).map { case (k, v) => k -> v.toString })
    val resumen = objeto(List(
      "bebidas" -> res.bebidas.toString,
      "acompanamientos" -> res.acompanamientos.toString,
      "opciones_generadas" -> res.opcionesGeneradas.toString,
      "precio_minimo" -> numero(res.precioMinimo),
      "precio_maximo" -> numero(res.precioMaximo),
      "opciones_por_sabor" -> porSabor
    ))
    objeto(List("solicitud" -> solicitud, "opciones" -> opciones, "resumen" -> resumen))
  }
}
