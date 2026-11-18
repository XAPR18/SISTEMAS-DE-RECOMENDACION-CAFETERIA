# Cambios del avance 2 y correcciones de la auditoría

El avance 1 (Scala + Prolog) se auditó antes de integrar Python. La copia original del
avance 1 se conserva sin cambios en su propia carpeta.

## Correcciones de la auditoría

| # | Prioridad | Hallazgo en el avance 1 | Corrección en el avance 2 |
|---|---|---|---|
| 1 | Alta | Scala y Prolog leían los mismos archivos con reglas distintas: `Ana,DULCE,FRIA` o una línea `# comentario` pasaban en Scala y rompían **todas** las consultas en Prolog; un campo entre comillas tenía el problema inverso | Solo Python lee `data/*.json` y valida una vez. Scala y Prolog reciben datos ya validados. Los códigos son estrictos (minúsculas) en los tres lenguajes y una prueba lo verifica |
| 2 | Alta | Prolog recargaba `clientes.txt` en cada consulta: una fila mala bloqueaba hasta a los clientes nuevos | Prolog ya no lee archivos en el modo integrado: recibe solo catálogo, precios y solicitud |
| 3 | Media | Scala repetía todas las reglas de Prolog al validar la respuesta | Scala procesa **antes** de Prolog (precios y opciones) y no decide. Python solo verifica que los productos devueltos existan |
| 4 | Media | stdout y stderr de Prolog mezclados: un aviso rompía la lectura | Se leen por separado. Las respuestas son JSON |
| 5 | Media | Un CSV con BOM (Excel, Bloc de notas) daba «identificador inválido» | Lectura con `utf-8-sig` (prueba `test_catalogo_con_bom`) |
| 6 | Media | Mensaje de Prolog `Unknown error term: datos_invalidos(...)` | Mensajes propios `Cafeteria: ...` mediante `prolog:message//1`. Python los muestra como «Prolog rechazó la solicitud: ...» |
| 7 | Media | Pruebas acopladas a los datos reales (`size == 6`) que además sobrescribían archivos del proyecto | Scala, Prolog y Python usan catálogos de prueba propios. Las pruebas de Python usan carpetas temporales. Las clases de prueba se compilan en `target/test-classes`. Las pruebas Scala ya no dependen de `assert` |
| 8 | Baja | Al elegir un perfil siempre se volvían a pedir las preferencias | La ventana carga las preferencias del perfil. La consola pregunta «¿usar mis preferencias?» |
| 9 | Baja | Montos con formato distinto (`S/ 20` y `S/ 20.00`) | Un solo formateador: `soles()` siempre con 2 decimales |
| 10 | Baja | Varios `.get` que podían lanzar excepciones | Los montos son `Long` en céntimos y la entrada se valida con `Either`. No quedan `.get` en el código principal de Scala |
| 11 | Baja | `directorio_datos/1` se duplicaba al recargar `hechos.pl` | Eliminado: Prolog ya no busca carpetas |
| 12 | Baja | Sabor del acompañamiento sin uso y una sola bebida por sabor | Catálogo de 11 bebidas y 5 acompañamientos. Nuevas reglas de maridaje (`complementa/2`), puntaje y destacada |
| 13 | Baja | `Funciones.filtrar` solo se usaba en pruebas | Se usa en `ProcesamientoService` y se suma `contarPor` (`groupBy`) |
| 14 | Baja | Sin repositorio git; 37 MB de instaladores en `tools/downloads` | Instaladores excluidos de la copia y `.gitignore` actualizado. **Pendiente del grupo:** crear el repositorio |

## Nuevas funciones del avance 2

- Python como integrador con la estructura de la guía (`main.py`, `integracion/`, `modelos/`, `utils/`).
- Interfaz gráfica con tkinter: formulario, barra del flujo entre lenguajes, tabla de
  opciones, explicación, menú e historial. También queda la interfaz de consola.
- Interfaz web (`--web`) con la biblioteca estándar: fotos reales de los productos, carta con
  filtros, historial y una barra de flujo con los símbolos de Python, Scala y Prolog que
  muestra el tiempo real de cada paso. La ventana tkinter usa la misma barra, con los
  símbolos dibujados en un `Canvas`.
- Datos en JSON y historial de consultas en `data/resultados.json`.
- Perfiles nuevos que se pueden guardar en `clientes.json`.
- Scala como módulo de procesamiento: franja desde la hora, combos compatibles,
  precios totales y resumen estadístico.
- Prolog con maridaje, puntaje, opción destacada y motivos de cada recomendación.
- `prolog/hechos.pl` generado desde los JSON para usar Prolog por separado.
- `scripts/probar_todo.py`: un solo comando para las 98 pruebas.
