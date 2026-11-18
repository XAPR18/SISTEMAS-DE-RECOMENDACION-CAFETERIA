package app.servicios

import app.modelos._

// Interpreta el mensaje que envia Python por la entrada estandar.
// Formato (un registro por linea, campos separados por |):
//   SOLICITUD|sabor|temperatura|presupuesto|modo|franja      franja = manana|tarde|noche|hora=HH
//   BEBIDA|id|sabor|temperatura|precio|franja1;franja2|acomp1;acomp2
//   ACOMP|id|sabor|precio
object EntradaService {
  private sealed trait Registro
  private case class RegSolicitud(s: Solicitud) extends Registro
  private case class RegBebida(b: Bebida) extends Registro
  private case class RegAcomp(a: Acompanamiento) extends Registro

  private def campo[A](valor: Option[A], error: => String): Either[String, A] = valor.toRight(error)

  private def franja(texto: String): Either[String, (Franja, Boolean)] = texto match {
    case f if f.startsWith("hora=") =>
      f.drop(5).toIntOption.flatMap(Franja.deHora).map(fr => (fr, true)).toRight(s"Hora invalida: $f")
    case f => Franja.desde(f).map(fr => (fr, false)).toRight(s"Franja invalida: $f")
  }

  private def registro(linea: String): Either[String, Registro] = linea.split("\\|", -1).toList match {
    case List("SOLICITUD", s, t, presupuesto, m, f) => for {
      sabor <- campo(Sabor.desde(s), s"Sabor invalido: $s")
      temp <- campo(Temperatura.desde(t), s"Temperatura invalida: $t")
      monto <- Validacion.centimos(presupuesto)
      modo <- campo(Modo.desde(m), s"Modo invalido: $m")
      fr <- franja(f)
    } yield RegSolicitud(Solicitud(sabor, temp, monto, modo, fr._1, fr._2))

    case List("BEBIDA", id, s, t, precio, franjas, acomps) => for {
      ident <- Validacion.identificador(id)
      sabor <- campo(Sabor.desde(s), s"Sabor invalido: $s")
      temp <- campo(Temperatura.desde(t), s"Temperatura invalida: $t")
      monto <- Validacion.centimos(precio)
      frs <- Validacion.todos(Validacion.lista(franjas).map(f => campo(Franja.desde(f), s"Franja invalida: $f")))
      acs <- Validacion.todos(Validacion.lista(acomps).map(Validacion.identificador))
    } yield RegBebida(Bebida(ident, sabor, temp, monto, frs, acs))

    case List("ACOMP", id, s, precio) => for {
      ident <- Validacion.identificador(id)
      sabor <- campo(Sabor.desde(s), s"Sabor invalido: $s")
      monto <- Validacion.centimos(precio)
    } yield RegAcomp(Acompanamiento(ident, sabor, monto))

    case _ => Left("Registro desconocido o con campos de mas o de menos.")
  }

  def interpretar(lineas: List[String]): Either[String, (Solicitud, Catalogo)] = {
    val conNumero = lineas.zipWithIndex.collect { case (l, i) if l.trim.nonEmpty => (l.trim, i + 1) }
    for {
      registros <- Validacion.todos(conNumero.map { case (l, n) => registro(l).left.map(e => s"Linea $n: $e") })
      solicitud <- registros.collect { case RegSolicitud(s) => s } match {
        case List(s) => Right(s)
        case otras => Left(s"Se esperaba exactamente una SOLICITUD y llegaron ${otras.size}.")
      }
      bebidas = registros.collect { case RegBebida(b) => b }
      acomps = registros.collect { case RegAcomp(a) => a }
      catalogo = Catalogo(bebidas, acomps)
      _ <- validarCatalogo(catalogo)
    } yield (solicitud, catalogo)
  }

  def validarCatalogo(c: Catalogo): Either[String, Unit] = {
    val ids = c.bebidas.map(_.id) ++ c.acompanamientos.map(_.id)
    val desconocidos = c.bebidas.flatMap(b => b.acompanamientos.filterNot(c.acompanamientoPorId.contains).map(a => s"${b.id}->$a"))
    if (c.bebidas.isEmpty) Left("El catalogo no tiene bebidas.")
    else if (ids.distinct.size != ids.size) Left("Hay identificadores de producto repetidos.")
    else if (desconocidos.nonEmpty) Left(s"Acompanamientos desconocidos: ${desconocidos.mkString(", ")}")
    else Right(())
  }
}
