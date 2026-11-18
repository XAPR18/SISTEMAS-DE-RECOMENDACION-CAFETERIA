package app.servicios

import app.modelos._

// Logica principal de Scala: arma todas las opciones del tipo de pedido y
// calcula sus precios totales. No decide cual se recomienda: eso lo hace Prolog.
object ProcesamientoService {

  // Bebida sola: una opcion por bebida. Combo: una opcion por cada
  // acompanamiento compatible de cada bebida (flatMap + filter).
  def generarOpciones(c: Catalogo, modo: Modo): List[OpcionPrecio] = modo match {
    case Modo.Sola => c.bebidas.map(b => OpcionPrecio(b, None))
    case Modo.Combo =>
      for {
        b <- c.bebidas
        a <- Funciones.filtrar(c.acompanamientos)(a => b.acompanamientos.contains(a.id))
      } yield OpcionPrecio(b, Some(a))
  }

  def resumir(c: Catalogo, opciones: List[OpcionPrecio]): Resumen = {
    val totales = opciones.map(_.total)
    Resumen(
      bebidas = c.bebidas.size,
      acompanamientos = c.acompanamientos.size,
      opcionesGeneradas = opciones.size,
      precioMinimo = totales.minOption,
      precioMaximo = totales.maxOption,
      opcionesPorSabor = Funciones.contarPor(opciones)(_.bebida.sabor.codigo)
    )
  }

  def procesar(s: Solicitud, c: Catalogo): ResultadoProcesamiento = {
    val opciones = Funciones.ordenarPor(generarOpciones(c, s.modo))(o => (o.total, o.bebida.id, o.idAcompanamiento))
    ResultadoProcesamiento(s, opciones, resumir(c, opciones))
  }
}
