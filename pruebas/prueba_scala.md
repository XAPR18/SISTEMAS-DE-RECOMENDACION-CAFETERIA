# Pruebas del módulo Scala

**Comando:** `py scripts/probar_todo.py` (o `java -cp scala/target/classes;scala/target/test-classes;tools/scala-2.13.16/scala-library-2.13.16.jar app.Pruebas`)
**Entorno:** JDK 21.0.12, Scala 2.13.16 · **Resultado:** `Pruebas Scala: 44 de 44 superadas.`

Las pruebas usan su propio catálogo de ejemplo y no leen `data/`.

| Grupo | Casos | Qué verifica |
|---|---|---|
| Montos | 13 | `20,50`→2050, `12.5`→1250, `8`→800; rechaza `0`, `-1`, `1.234`, `NaN`, `1e3`, `1000000`, vacío, `12.` |
| Identificadores y listas | 3 | minúsculas obligatorias; lista vacía |
| Códigos estrictos | 2 | `DULCE` rechazado (igual que en Python y Prolog) |
| Franjas horarias | 7 | límites 05→noche, 06→mañana, 11→mañana, 12→tarde, 18→tarde, 19→noche; horas fuera de rango |
| Funciones de orden superior | 3 | `ordenarPor`, `filtrar`, `contarPor` |
| Entrada desde Python | 7 | solicitud correcta, `hora=19`→noche, falta o sobra la solicitud, línea desconocida con número, acompañamiento inexistente, id repetido |
| Procesamiento | 5 | solo combos compatibles, total del combo 1850, bebidas solas, orden por precio, resumen por sabor |
| Salida JSON | 3 | escape de comillas y saltos, JSON completo y error |

## Ejemplo real de procesamiento

Entrada (stdin):
```text
SOLICITUD|amargo|caliente|15.00|combo|manana
BEBIDA|espresso|amargo|caliente|8.00|manana;tarde|croissant;brownie
BEBIDA|latte|suave|caliente|9.50|manana|croissant
ACOMP|croissant|suave|7.00
ACOMP|brownie|dulce|6.00
```
Salida (código 0):
```json
{"solicitud":{"sabor":"amargo","temperatura":"caliente","presupuesto":1500,"modo":"combo","franja":"manana","franja_automatica":false},"opciones":[{"bebida":"espresso","acompanamiento":"brownie","total":1400},{"bebida":"espresso","acompanamiento":"croissant","total":1500},{"bebida":"latte","acompanamiento":"croissant","total":1650}],"resumen":{"bebidas":2,"acompanamientos":2,"opciones_generadas":3,"precio_minimo":1400,"precio_maximo":1650,"opciones_por_sabor":{"amargo":2,"suave":1}}}
```
Scala genera **todas** las opciones con su precio, incluida la de S/ 16.50 que supera el
presupuesto: decidir cuáles se recomiendan le corresponde a Prolog.

Entrada inválida `SOLICITUD|amargo|caliente|15.505|combo|manana` (código 2):
```json
{"error":"Linea 1: Monto invalido: '15.505'. Usa hasta 6 enteros y 2 decimales, por ejemplo 20 o 20.50."}
```
