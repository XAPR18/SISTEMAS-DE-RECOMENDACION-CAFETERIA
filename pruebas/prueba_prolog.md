# Pruebas del módulo Prolog

**Comando:** desde `prolog/`: `..\tools\swipl\bin\swipl.exe -q -s pruebas.pl -g run_tests -t halt`
**Entorno:** SWI-Prolog 10.0.2 · **Resultado:** 17 de 17 pruebas PlUnit superadas, sin avisos.

Las pruebas cargan `reglas.pl` y `recomendaciones.pl` con un catálogo propio (no usan `hechos.pl`).

| Prueba | Solicitud (sabor, temperatura, presupuesto, modo, franja) | Resultado esperado |
|---|---|---|
| combo_exacto | dulce, fría, 2000, combo, tarde | `opcion(exacta, frappe, brownie, 1850, armonia)` |
| presupuesto_limite_exacto | ídem con 1850 | 1 opción |
| un_centimo_menos_no_alcanza | ídem con 1849 | `[]` |
| no_cambia_horario | dulce, fría, 2000, sola, mañana | `[]` |
| todos_los_combos_ordenados_por_precio | amargo, caliente, 2000, combo, mañana | espresso+brownie 1400 (contraste), espresso+croissant 1500 (neutro) |
| alternativa_de_temperatura_con_combos | amargo, fría, 2000, combo, tarde | los mismos dos combos como `alternativa` |
| no_cambia_sabor | dulce, fría, 700, sola, tarde | `[]` (no inventa otro sabor) |
| sola_no_incluye_acompanamiento | cítrico, fría, 5000, sola, mañana | té helado, `ninguno` |
| combo_requiere_combinacion | — | frappe + croissant no es candidata |
| maridaje_contraste / maridaje_armonia | — | té helado + croissant = contraste; frappe + brownie = armonía |
| destacada_prefiere_maridaje | amargo, caliente, 2000, combo, mañana | destacada espresso + brownie (puntaje 5) |
| destacada_de_lista_vacia | — | `ninguna` |
| motivos_alternativa | — | incluye `temperatura_cambiada` y `maridaje_contraste` |
| solicitud_invalida / presupuesto_no_entero | sabor `picante` / presupuesto 20.5 | error `cafeteria(...)` |
| cliente_desconocido | `recomendaciones(no_existe, ...)` | `[]` |

## Consultas independientes con `hechos.pl` (salida real de `?- demo.`)

```text
Ana / tarde / combo / 2000 centimos
    opcion(exacta,milkshake_vainilla,galleta_avena,1450,neutro)
  * opcion(exacta,milkshake_vainilla,alfajor,1550,armonia)  (destacada)
    opcion(exacta,frappe_mocha,alfajor,1700,armonia)
    opcion(exacta,frappe_mocha,brownie,1850,armonia)

Ana / manana / sola / 2000 centimos
  Sin coincidencias.

Luis / manana / combo / 2000 centimos
    opcion(exacta,americano,galleta_avena,1050,neutro)
  * opcion(exacta,americano,alfajor,1150,contraste)  (destacada)
    opcion(exacta,americano,croissant,1400,neutro)
    opcion(exacta,espresso,brownie,1400,contraste)
    opcion(exacta,espresso,croissant,1500,neutro)

Carlos / tarde / sola / 1500 centimos
  * opcion(exacta,cold_brew,ninguno,1100,sin_acompanamiento)  (destacada)

Sofia / tarde / combo / 2000 centimos
  * opcion(alternativa,latte,galleta_avena,1300,armonia)  (destacada)
    opcion(alternativa,capuchino,galleta_avena,1350,armonia)
    opcion(alternativa,latte,brownie,1550,contraste)
    opcion(alternativa,latte,croissant,1650,armonia)
    opcion(alternativa,capuchino,croissant,1700,armonia)
```

## Modo integrado (`cli`) con hechos por stdin

```text
producto(frappe_mocha,bebida,dulce,fria,1250).
servido_en(frappe_mocha,tarde).
precio_opcion(frappe_mocha,ninguno,1250).
solicitud(dulce,fria,2000,sola,tarde).
```
Respuesta (código 0):
```json
{"opciones": [ {"acompanamiento":"ninguno","bebida":"frappe_mocha","destacada":true,"maridaje":"sin_acompanamiento","motivos": ["sabor_coincide", "servida_en_franja", "dentro_del_presupuesto", "temperatura_exacta", "maridaje_sin_acompanamiento" ],"puntaje":3,"tipo":"exacta","total":1250} ],"total":1}
```
Un término distinto de los cinco permitidos (por ejemplo `halt.`) se rechaza con
`Cafeteria: hecho no permitido o invalido: halt` y código 2; no se ejecuta.
