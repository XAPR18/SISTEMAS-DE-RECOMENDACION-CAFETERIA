# Pruebas de integración (Python + Scala + Prolog)

**Comando:** `py scripts/probar_todo.py` (o, desde `python/tests`: `py -m unittest -v`)
**Entorno:** Python 3.12.10, JDK 21.0.12, Scala 2.13.16, SWI-Prolog 10.0.2 en Windows 11.
**Resultado:** 37 de 37 pruebas Python superadas. Las 12 de `test_integracion.py` y las 8 de
`test_web.py` ejecutan los procesos reales de Java y SWI-Prolog. Sumando las 44 de Scala y
las 17 de Prolog, `probar_todo.py` termina con **TODAS LAS PRUEBAS SUPERADAS** (98 en total).

Las pruebas crean una carpeta temporal con su propio `data/`: no leen ni modifican los
datos ni el historial reales.

## Casos de integración (flujo completo)

| Perfil de prueba | Pedido | Franja | Presupuesto | Resultado |
|---|---|---|---|---|
| Dulce, fría | Combo | Tarde | S/ 20.00 | Frappe mocha + Brownie S/ 18.50, exacta, armonía, destacada |
| Dulce, fría | Combo | Tarde | S/ 18.50 / S/ 18.49 | 1 opción / ninguna |
| Dulce, fría | Bebida | Mañana | S/ 20.00 | Ninguna (no cambia el horario) |
| Amargo, caliente | Combo | Mañana | S/ 20.00 | Espresso + Brownie S/ 14.00 (destacada) y Espresso + Croissant S/ 15.00 |
| Amargo, fría | Combo | Tarde | S/ 20.00 | Solo alternativas; la explicación dice «pediste fría» |
| Suave, caliente | Bebida | Automática (hora 20) | S/ 20.00 | Scala calcula **noche**; Capuchino S/ 10.00 |
| Cítrico, fría | Bebida | Mañana | S/ 9.00 | Se guarda en el historial de la carpeta de prueba |

Además: los 5 pasos quedan registrados en orden (Python, Scala, Python, Prolog, Python);
Scala rechaza un sabor inválido; Prolog rechaza un hecho no permitido; Python no envía
texto libre a Prolog; Scala convierte `20.5` en 2050 céntimos.

## Interfaz web (`test_web.py`, 8 pruebas)

Levantan el servidor real en un puerto libre de `127.0.0.1` con datos temporales.

| Prueba | Qué comprueba |
|---|---|
| Catálogo | Productos, perfiles, precios `S/ 10.00` y ruta de la foto real (o `null` si no hay) |
| Recomendar | Flujo completo por HTTP: Frappe mocha + Brownie S/ 18.50, 5 pasos en orden, foto del brownie y registro en el historial |
| Perfil nuevo | Con «guardar», el perfil queda en `clientes.json` |
| Entradas inválidas | Sabor o franja desconocidos, monto negativo o no numérico, perfil inexistente o repetido, cuerpo que no es objeto → **400** |
| Cuerpo mal formado | JSON roto o de más de 10 KB → **400** |
| Rutas desconocidas | `/api/nada` y POST a `/api/catalogo` → **404** |
| Archivos estáticos | HTML, JS, CSS, SVG y JPG con el `Content-Type` correcto |
| Carpeta protegida | `../`, `%2e%2e/` y `..\` hacia `data/clientes.json` → **404** |

## Validación de datos (`test_archivos.py`, 17 pruebas)

JSON con BOM aceptado; sabor en mayúsculas, acompañamiento inexistente, id repetido,
precio con 3 decimales, JSON mal formado y clientes repetidos rechazados con el
archivo y la posición del error. También: guardado de perfiles con tildes, historial
limitado a 200 registros y escape de comillas en `hechos.pl` (`O'Connor`).

## Conversación real en consola (cliente nuevo, sin guardar perfil)

Entradas: `2`, `6` (nuevo), `Maria del Carmen O'Connor`, cítrico, fría, no guardar,
`9,00`, solo bebida, mañana, `4` (historial), `0`.

```text
  [1/5] Python obtiene los datos y la solicitud...
  [2/5] Scala valida y calcula los precios de las opciones...
  [3/5] Python envía la información a Prolog...
  [4/5] Prolog aplica las reglas de inferencia...
  [5/5] Python arma y muestra el resultado...

Scala generó 11 opciones con precio; Prolog seleccionó 2. Franja: Mañana.

★ 1. Limonada frozen | S/ 8.50 | COINCIDENCIA EXACTA | maridaje: —
     - Coincide con tu sabor preferido: cítrico.
     - Se sirve en la franja de la mañana.
     - Cuesta S/ 8.50: entra en tu presupuesto de S/ 9.00 y te sobran S/ 0.50.
     - Es fría, como la pediste.
     - DESTACADA: es la de mayor puntaje según las reglas (coincidencia y maridaje) y, a igual puntaje, la más económica.

  2. Te helado de limon | S/ 9.00 | COINCIDENCIA EXACTA | maridaje: —
     ...
Opción: - 2026-11-17T19:40:50 | Maria del Carmen O'Connor | Solo bebida | Mañana | S/ 9.00 | Limonada frozen (S/ 8.50, exacta)
Opción: Hasta pronto.
```

## Interfaz gráfica

Capturas reales en `docs/capturas/`:

| Archivo | Caso |
|---|---|
| `01_recomendacion_exacta.png` | Luis, combo, mañana: 5 exactas; destacada Café americano + Alfajor S/ 11.50 (contraste) |
| `02_alternativas_temperatura.png` | Sofía (suave, fría), combo, mañana: 5 alternativas calientes en naranja |
| `03_menu.png` | Catálogo completo con horarios y combinaciones |
| `04_historial.png` | Historial de consultas leído de `resultados.json` |

La barra superior muestra el símbolo de cada lenguaje y el tiempo real de cada paso.
La misma consulta se puede hacer en la página web (`--web`), que además muestra las fotos.

Tiempo medido por consulta: Scala ≈ 350 ms y Prolog ≈ 190 ms (cada uno arranca un proceso).
