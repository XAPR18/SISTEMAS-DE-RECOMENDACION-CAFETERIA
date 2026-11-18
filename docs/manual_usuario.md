# Manual de usuario

## Abrir el programa

Hay dos interfaces visuales con las mismas funciones:

| Interfaz | VS Code (Terminal › Run Task…) | Terminal en la carpeta del proyecto |
|---|---|---|
| Página web (con fotos) | **Cafeteria: abrir interfaz web** | `py python/src/main.py --web` |
| Ventana de escritorio | **Cafeteria: abrir interfaz grafica** | `py python/src/main.py` |

La primera vez se compila Scala unos segundos. La página web se abre sola en
`http://127.0.0.1:8000/`; para cerrarla, pulsar **Ctrl+C** en la terminal. En la ventana,
cuando la barra inferior dice **Listo**, el botón *Recomendar* se activa.

## Pestaña «Recomendar»

1. **Perfil**: elegir un cliente guardado (se cargan su sabor y temperatura) o
   **➕ Nuevo cliente** y escribir el nombre.
2. **Sabor preferido** y **Temperatura**: se pueden cambiar para esta consulta.
3. **Presupuesto total** en soles: `20`, `20.50` o `20,50` (hasta 2 decimales, mayor que 0).
4. **Pedido**: *Solo bebida* o *Combo* (bebida + acompañamiento).
5. **Franja horaria**: *Ahora* usa la hora de la PC; también se puede elegir mañana, tarde o noche.
6. **Guardar o actualizar el perfil** (opcional): guarda el perfil en `data/clientes.json`.
7. Pulsar **☕ Recomendar** (o Enter).

Mientras se consulta, la barra de pasos muestra con el **símbolo de cada lenguaje** el
recorrido **Python → Scala → Python → Prolog → Python**: el paso en curso se resalta en
dorado, los terminados quedan en verde con ✓ y los milisegundos reales, y si algo falla el
paso se marca en rojo. Después se ve:

- La tabla de opciones de menor a mayor precio. La fila con **★** (fondo dorado) es la
  **destacada**. Las filas en naranja son **alternativas de temperatura**.
- **¿Por qué se recomienda?**: los motivos que dedujo Prolog. Al hacer clic en otra fila
  se ve su explicación.
- Los tiempos de Scala y Prolog en milisegundos.
- En la página web, la destacada aparece arriba con las fotos de la bebida y del
  acompañamiento; al hacer clic en otra tarjeta se ven sus motivos.

Si no hay opciones, el sistema lo dice y no cambia el sabor ni supera el presupuesto.
Sugerencia: probar otra franja, un presupuesto mayor o «Solo bebida».

## Pestañas «Menú» (o «Carta») e «Historial»

- **Menú / Carta**: todos los productos con sabor, temperatura, precio, horario y
  combinaciones. En la web se puede filtrar por tipo o sabor.
- **Historial**: las últimas consultas (se guardan en `data/resultados.json`).

## Modo consola

```powershell
py python/src/main.py --consola
```
Menú: `1` ver menú, `2` buscar recomendación, `3` perfiles, `4` historial, `0` salir.

## Modificar el catálogo

Editar `data/productos.json` y `data/clientes.json` (ver formato en `docs/arquitectura.md`).
Al iniciar, Python valida los archivos e indica el archivo y el elemento con error, por
ejemplo `productos.json: bebidas[2].sabor: 'DULCE' no es valido`. También regenera
`prolog/hechos.pl`.

Para poner la foto de un producto en la página web, copiar la imagen a
`python/src/web/static/img/productos/` con el código del producto como nombre
(por ejemplo `cold_brew.jpg`).

## Problemas frecuentes

| Mensaje | Solución |
|---|---|
| No se encontró Java | Instalar JDK 21 |
| No se encontró SWI-Prolog | Revisar `tools/swipl` o definir la variable `SWIPL` |
| No hay soporte gráfico | Usar `--consola` o instalar Python desde python.org (incluye tkinter) |
| El puerto 8000 está ocupado | `py python/src/main.py --web --puerto 8080` |
| Monto inválido | Usar números con hasta 2 decimales, por ejemplo 20,50 |
