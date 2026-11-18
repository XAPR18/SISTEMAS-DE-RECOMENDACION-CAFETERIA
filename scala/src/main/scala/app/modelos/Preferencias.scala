package app.modelos

// Valores cerrados del dominio. Cada codigo coincide con el atomo usado en Prolog.
sealed trait Sabor { def codigo: String }
object Sabor {
  case object Dulce extends Sabor { val codigo = "dulce" }
  case object Amargo extends Sabor { val codigo = "amargo" }
  case object Suave extends Sabor { val codigo = "suave" }
  case object Citrico extends Sabor { val codigo = "citrico" }
  val valores: List[Sabor] = List(Dulce, Amargo, Suave, Citrico)
  // Coincidencia estricta: Python y Prolog tambien exigen minusculas.
  def desde(texto: String): Option[Sabor] = valores.find(_.codigo == texto)
}

sealed trait Temperatura { def codigo: String }
object Temperatura {
  case object Fria extends Temperatura { val codigo = "fria" }
  case object Caliente extends Temperatura { val codigo = "caliente" }
  val valores: List[Temperatura] = List(Fria, Caliente)
  def desde(texto: String): Option[Temperatura] = valores.find(_.codigo == texto)
}

sealed trait Modo { def codigo: String }
object Modo {
  case object Sola extends Modo { val codigo = "sola" }
  case object Combo extends Modo { val codigo = "combo" }
  def desde(texto: String): Option[Modo] = texto match {
    case "sola" => Some(Sola)
    case "combo" => Some(Combo)
    case _ => None
  }
}

sealed trait Franja { def codigo: String }
object Franja {
  case object Manana extends Franja { val codigo = "manana" }
  case object Tarde extends Franja { val codigo = "tarde" }
  case object Noche extends Franja { val codigo = "noche" }
  val valores: List[Franja] = List(Manana, Tarde, Noche)
  def desde(texto: String): Option[Franja] = valores.find(_.codigo == texto)

  // Manana 06:00-11:59, tarde 12:00-18:59, noche 19:00-05:59.
  def deHora(hora: Int): Option[Franja] = hora match {
    case h if h < 0 || h > 23 => None
    case h if h < 6 => Some(Noche)
    case h if h < 12 => Some(Manana)
    case h if h < 19 => Some(Tarde)
    case _ => Some(Noche)
  }
}
