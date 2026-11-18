package app.servicios

object Validacion {
  private val FormatoDinero = """([0-9]{1,6})(?:[.,]([0-9]{1,2}))?""".r
  private val FormatoId = """[a-z][a-z0-9_]*""".r

  // "20", "20.5", "20,50" -> centimos. Rechaza negativos, cero y mas de dos decimales.
  def centimos(texto: String): Either[String, Long] = texto.trim match {
    case FormatoDinero(enteros, decimales) =>
      val fraccion = Option(decimales).getOrElse("").padTo(2, '0')
      val total = enteros.toLong * 100 + fraccion.toLong
      if (total > 0) Right(total) else Left("El monto debe ser mayor que cero.")
    case _ => Left(s"Monto invalido: '$texto'. Usa hasta 6 enteros y 2 decimales, por ejemplo 20 o 20.50.")
  }

  def identificador(texto: String): Either[String, String] = texto match {
    case FormatoId() => Right(texto)
    case _ => Left(s"Identificador invalido: '$texto'. Usa minusculas, digitos y guion bajo.")
  }

  // "a;b;c" -> List("a", "b", "c"). Una lista vacia se escribe como campo vacio.
  def lista(texto: String): List[String] =
    if (texto.isEmpty) Nil else texto.split(";", -1).toList

  // Convierte una lista de Either en un Either de lista: falla con el primer error.
  def todos[A](valores: List[Either[String, A]]): Either[String, List[A]] =
    valores.foldRight[Either[String, List[A]]](Right(Nil)) { (actual, resto) =>
      for { a <- actual; r <- resto } yield a :: r
    }
}
