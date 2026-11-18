package app.servicios

// Funciones genericas de orden superior usadas por el procesamiento.
object Funciones {
  def filtrar[A](elementos: List[A])(criterio: A => Boolean): List[A] = elementos.filter(criterio)

  def ordenarPor[A, B: Ordering](elementos: List[A])(criterio: A => B): List[A] = elementos.sortBy(criterio)

  def contarPor[A, K](elementos: List[A])(clave: A => K): Map[K, Int] =
    elementos.groupBy(clave).map { case (k, grupo) => k -> grupo.size }
}
