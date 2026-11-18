ThisBuild / scalaVersion := "2.13.16"

// Modulo de procesamiento. Normalmente lo compila y ejecuta Python
// (python/src/utils/herramientas.py) con los JAR de tools/scala-2.13.16.
// Con sbt:  sbt "run" < entrada.txt     y     sbt "Test / runMain app.Pruebas"
lazy val root = (project in file("."))
  .settings(
    name := "sistema-cafeteria",
    version := "0.3.0",
    Compile / run / fork := true,
    Compile / run / connectInput := true,
    scalacOptions ++= Seq("-deprecation", "-feature", "-unchecked", "-encoding", "UTF-8")
  )
