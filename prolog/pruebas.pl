% Pruebas de las reglas con un catalogo propio (no dependen de data/ ni de hechos.pl).
% Ejecutar desde la carpeta prolog:  swipl -q -s pruebas.pl -g run_tests -t halt
:- ensure_loaded(recomendaciones).
:- use_module(library(plunit)).

catalogo_prueba :-
    retractall(producto(_,_,_,_,_)), retractall(servido_en(_,_)),
    retractall(combina(_,_)), retractall(precio_opcion(_,_,_)),
    forall(member(P, [
        producto(espresso, bebida, amargo, caliente, 800),
        producto(capuchino, bebida, suave, caliente, 1000),
        producto(frappe, bebida, dulce, fria, 1250),
        producto(te_helado, bebida, citrico, fria, 900),
        producto(croissant, acompanamiento, suave, ninguna, 700),
        producto(brownie, acompanamiento, dulce, ninguna, 600),
        servido_en(espresso, manana), servido_en(espresso, tarde),
        servido_en(capuchino, noche), servido_en(frappe, tarde),
        servido_en(te_helado, manana),
        combina(espresso, croissant), combina(espresso, brownie),
        combina(capuchino, croissant), combina(frappe, brownie),
        combina(te_helado, croissant),
        % Totales como los calcularia Scala
        precio_opcion(espresso, ninguno, 800), precio_opcion(capuchino, ninguno, 1000),
        precio_opcion(frappe, ninguno, 1250), precio_opcion(te_helado, ninguno, 900),
        precio_opcion(espresso, croissant, 1500), precio_opcion(espresso, brownie, 1400),
        precio_opcion(capuchino, croissant, 1700), precio_opcion(frappe, brownie, 1850),
        precio_opcion(te_helado, croissant, 1600)
    ]), assertz(P)).

:- begin_tests(cafeteria, [setup(catalogo_prueba)]).

test(combo_exacto) :-
    recomendaciones(solicitud(dulce, fria, 2000, combo, tarde),
                    [opcion(exacta, frappe, brownie, 1850, armonia)]).
test(presupuesto_limite_exacto) :-
    recomendaciones(solicitud(dulce, fria, 1850, combo, tarde), [_]).
test(un_centimo_menos_no_alcanza) :-
    recomendaciones(solicitud(dulce, fria, 1849, combo, tarde), []).
test(no_cambia_horario) :-
    recomendaciones(solicitud(dulce, fria, 2000, sola, manana), []).
test(todos_los_combos_ordenados_por_precio) :-
    recomendaciones(solicitud(amargo, caliente, 2000, combo, manana),
        [opcion(exacta, espresso, brownie, 1400, contraste),
         opcion(exacta, espresso, croissant, 1500, neutro)]).
test(alternativa_de_temperatura_con_combos) :-
    recomendaciones(solicitud(amargo, fria, 2000, combo, tarde),
        [opcion(alternativa, espresso, brownie, 1400, contraste),
         opcion(alternativa, espresso, croissant, 1500, neutro)]).
test(no_cambia_sabor) :-
    recomendaciones(solicitud(dulce, fria, 700, sola, tarde), []).
test(sola_no_incluye_acompanamiento) :-
    recomendaciones(solicitud(citrico, fria, 5000, sola, manana),
        [opcion(exacta, te_helado, ninguno, 900, sin_acompanamiento)]).
test(combo_requiere_combinacion) :-
    \+ candidata(solicitud(dulce, fria, 5000, combo, tarde), frappe, croissant, _).
test(maridaje_contraste) :- maridaje(te_helado, croissant, contraste).
test(maridaje_armonia) :- maridaje(frappe, brownie, armonia).
test(destacada_prefiere_maridaje) :-
    recomendaciones(solicitud(amargo, caliente, 2000, combo, manana), Opciones),
    destacada(Opciones, opcion(_, espresso, brownie, 1400, contraste)).
test(destacada_de_lista_vacia) :- destacada([], ninguna).
test(motivos_alternativa) :-
    motivos(solicitud(amargo, fria, 2000, combo, tarde),
            opcion(alternativa, espresso, brownie, 1400, contraste), M),
    memberchk(temperatura_cambiada, M), memberchk(maridaje_contraste, M).
test(solicitud_invalida, [throws(cafeteria(_))]) :-
    recomendaciones(solicitud(picante, fria, 2000, sola, tarde), _).
test(presupuesto_no_entero, [throws(cafeteria(_))]) :-
    recomendaciones(solicitud(dulce, fria, 20.5, sola, tarde), _).
test(cliente_desconocido) :-
    recomendaciones(no_existe, tarde, 2000, sola, []).

:- end_tests(cafeteria).
