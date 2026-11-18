% Reune las soluciones de las reglas y elige la opcion destacada.
:- ensure_loaded(reglas).

:- multifile prolog:message//1.
prolog:message(cafeteria(Mensaje)) --> ['Cafeteria: ~w'-[Mensaje]].

solicitud_valida(solicitud(Sabor, Temp, Presupuesto, Modo, Franja)) :-
    sabor_valido(Sabor), temperatura_valida(Temp),
    integer(Presupuesto), Presupuesto > 0,
    modo_valido(Modo), franja_valida(Franja).

% Todas las opciones de una solicitud, ordenadas por precio (sin cortes
% que oculten combos). Una solicitud invalida produce un error claro.
recomendaciones(Solicitud, Opciones) :-
    (   solicitud_valida(Solicitud) -> true
    ;   format(atom(M), 'solicitud invalida: ~q', [Solicitud]),
        throw(cafeteria(M))
    ),
    findall(Total-Opcion,
            ( recomendar(Solicitud, Opcion), Opcion = opcion(_, _, _, Total, _) ),
            Pares),
    sort(Pares, Ordenados),
    pares_valores(Ordenados, Opciones).

pares_valores([], []).
pares_valores([_-V|Resto], [V|Valores]) :- pares_valores(Resto, Valores).

% Uso con un cliente de hechos.pl: recomendaciones(cliente_1, tarde, 2000, combo, R).
% Un cliente desconocido no tiene recomendaciones.
recomendaciones(Cliente, Franja, Presupuesto, Modo, Opciones) :-
    (   gusto(Cliente, Sabor), prefiere(Cliente, Temp)
    ->  recomendaciones(solicitud(Sabor, Temp, Presupuesto, Modo, Franja), Opciones)
    ;   Opciones = []
    ).

% Destacada: mayor puntaje; a igual puntaje, menor precio; luego por nombre.
destacada([], ninguna).
destacada([Primera|Resto], Mejor) :-
    Opciones = [Primera|Resto],
    findall(clave(Negativo, Total, Bebida, Acomp)-Opcion,
            ( member(Opcion, Opciones),
              Opcion = opcion(_, Bebida, Acomp, Total, _),
              puntaje(Opcion, P), Negativo is -P ),
            Claves),
    keysort(Claves, [_-Mejor|_]).
