package app.modelos

case class Solicitud(
  sabor: Sabor,
  temperatura: Temperatura,
  presupuesto: Long,
  modo: Modo,
  franja: Franja,
  franjaAutomatica: Boolean
)

// Opcion de pedido con su precio total calculado por Scala.
// Prolog decide despues si la opcion se recomienda o no.
case class OpcionPrecio(bebida: Bebida, acompanamiento: Option[Acompanamiento]) {
  def total: Long = bebida.precio + acompanamiento.map(_.precio).getOrElse(0L)
  def idAcompanamiento: String = acompanamiento.map(_.id).getOrElse("ninguno")
}

case class Resumen(
  bebidas: Int,
  acompanamientos: Int,
  opcionesGeneradas: Int,
  precioMinimo: Option[Long],
  precioMaximo: Option[Long],
  opcionesPorSabor: Map[String, Int]
)

case class ResultadoProcesamiento(solicitud: Solicitud, opciones: List[OpcionPrecio], resumen: Resumen)
