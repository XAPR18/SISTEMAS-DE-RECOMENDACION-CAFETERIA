package app.modelos

// Los montos se guardan en centimos (Long): 1250 representa S/ 12,50.
// Asi no hay redondeos de Double ni conversiones que puedan fallar.
case class Bebida(
  id: String,
  sabor: Sabor,
  temperatura: Temperatura,
  precio: Long,
  franjas: List[Franja],
  acompanamientos: List[String]
)

case class Acompanamiento(id: String, sabor: Sabor, precio: Long)

case class Catalogo(bebidas: List[Bebida], acompanamientos: List[Acompanamiento]) {
  // Map para buscar acompanamientos por identificador.
  val acompanamientoPorId: Map[String, Acompanamiento] = acompanamientos.map(a => a.id -> a).toMap
}
