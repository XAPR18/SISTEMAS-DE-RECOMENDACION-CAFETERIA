package app

import app.modelos._
import app.servicios._

// Pruebas del modulo Scala sin bibliotecas externas y sin leer los datos reales:
// cada caso usa su propio catalogo de ejemplo. Termina con codigo 1 si algo falla.
object Pruebas {
  private var fallos = List.empty[String]
  private var total = 0
  private def comprobar(nombre: String)(condicion: => Boolean): Unit = {
    total += 1
    val ok = try condicion catch { case e: Throwable => false }
    if (!ok) fallos ::= nombre
  }

  val entradaEjemplo: List[String] = List(
    "SOLICITUD|dulce|fria|20.00|combo|tarde",
    "BEBIDA|frappe|dulce|fria|12.50|tarde;noche|brownie;galleta",
    "BEBIDA|espresso|amargo|caliente|8|manana|brownie",
    "ACOMP|brownie|dulce|6.00",
    "ACOMP|galleta|suave|3.5"
  )

  def main(args: Array[String]): Unit = {
    // Validacion de montos en centimos
    comprobar("monto con coma")(Validacion.centimos("20,50") == Right(2050L))
    comprobar("monto con un decimal")(Validacion.centimos("12.5") == Right(1250L))
    comprobar("monto entero")(Validacion.centimos("8") == Right(800L))
    List("0", "0.00", "-1", "1.234", "NaN", "1e3", "1000000", "", " ", "12.").foreach { m =>
      comprobar(s"monto invalido '$m'")(Validacion.centimos(m).isLeft)
    }
    comprobar("identificador valido")(Validacion.identificador("te_helado").isRight)
    comprobar("identificador con mayusculas")(Validacion.identificador("Te").isLeft)
    comprobar("lista vacia")(Validacion.lista("") == Nil)

    // Codigos estrictos, iguales a los de Python y Prolog
    comprobar("sabor en mayusculas rechazado")(Sabor.desde("DULCE").isEmpty)
    comprobar("sabor valido")(Sabor.desde("citrico").contains(Sabor.Citrico))

    // Franjas horarias y sus limites
    comprobar("hora fuera de rango")(Franja.deHora(-1).isEmpty && Franja.deHora(24).isEmpty)
    comprobar("05 es noche")(Franja.deHora(5).contains(Franja.Noche))
    comprobar("06 es manana")(Franja.deHora(6).contains(Franja.Manana))
    comprobar("11 es manana")(Franja.deHora(11).contains(Franja.Manana))
    comprobar("12 es tarde")(Franja.deHora(12).contains(Franja.Tarde))
    comprobar("18 es tarde")(Franja.deHora(18).contains(Franja.Tarde))
    comprobar("19 es noche")(Franja.deHora(19).contains(Franja.Noche))

    // Funciones de orden superior
    comprobar("ordenarPor")(Funciones.ordenarPor(List(3, 1, 2))(identity) == List(1, 2, 3))
    comprobar("filtrar")(Funciones.filtrar(List(1, 2, 3))(_ > 1) == List(2, 3))
    comprobar("contarPor")(Funciones.contarPor(List("a", "b", "a"))(identity) == Map("a" -> 2, "b" -> 1))

    // Interpretacion de la entrada enviada por Python
    val interpretado = EntradaService.interpretar(entradaEjemplo)
    comprobar("entrada valida")(interpretado.isRight)
    val (solicitud, catalogo) = interpretado.toOption.get
    comprobar("solicitud interpretada")(solicitud == Solicitud(Sabor.Dulce, Temperatura.Fria, 2000, Modo.Combo, Franja.Tarde, false))
    comprobar("franja desde la hora")(EntradaService.interpretar(
      "SOLICITUD|dulce|fria|20|sola|hora=19" :: entradaEjemplo.tail).exists(_._1.franja == Franja.Noche))
    comprobar("sin solicitud")(EntradaService.interpretar(entradaEjemplo.tail).isLeft)
    comprobar("dos solicitudes")(EntradaService.interpretar(entradaEjemplo.head :: entradaEjemplo).isLeft)
    comprobar("registro desconocido indica linea")(EntradaService.interpretar(entradaEjemplo :+ "OTRO|x")
      .left.exists(_.startsWith("Linea 6")))
    comprobar("acompanamiento inexistente")(EntradaService.interpretar(entradaEjemplo :+ "BEBIDA|te|citrico|fria|9|manana|torta").isLeft)
    comprobar("id repetido")(EntradaService.interpretar(entradaEjemplo :+ "ACOMP|brownie|dulce|6").isLeft)

    // Procesamiento: combos compatibles y precios totales
    val combos = ProcesamientoService.generarOpciones(catalogo, Modo.Combo)
    comprobar("tres combos compatibles")(combos.size == 3)
    comprobar("total del combo")(combos.exists(o => o.bebida.id == "frappe" && o.idAcompanamiento == "brownie" && o.total == 1850))
    val solas = ProcesamientoService.generarOpciones(catalogo, Modo.Sola)
    comprobar("bebidas solas")(solas.map(o => (o.bebida.id, o.idAcompanamiento, o.total)).toSet ==
      Set(("frappe", "ninguno", 1250L), ("espresso", "ninguno", 800L)))
    val resultado = ProcesamientoService.procesar(solicitud, catalogo)
    comprobar("ordenado por precio")(resultado.opciones.map(_.total) == List(1400L, 1600L, 1850L))
    comprobar("resumen")(resultado.resumen.precioMinimo.contains(1400L) && resultado.resumen.opcionesPorSabor == Map("dulce" -> 2, "amargo" -> 1))

    // Salida JSON
    comprobar("escape JSON")(JsonService.texto("a\"b\\c\n") == "\"a\\\"b\\\\c\\n\"")
    comprobar("json de resultado")(Main.ejecutar(entradaEjemplo).exists(j =>
      j.contains("\"opciones\":[{\"bebida\":\"espresso\",\"acompanamiento\":\"brownie\",\"total\":1400}")))
    comprobar("json de error")(Main.ejecutar(List("SOLICITUD|dulce")).isLeft)

    if (fallos.isEmpty) println(s"Pruebas Scala: $total de $total superadas.")
    else {
      println(s"Pruebas Scala: ${fallos.size} de $total fallaron:")
      fallos.reverse.foreach(f => println(s"  - $f"))
      sys.exit(1)
    }
  }
}
