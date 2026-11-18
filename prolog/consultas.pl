% Punto de entrada de Prolog.
%
% 1) Uso independiente en SWI-Prolog (con los hechos de hechos.pl):
%      ?- demo.
%      ?- nombre_cliente(Id, Nombre).
%      ?- recomendaciones(cliente_1, tarde, 2000, combo, R).
%      ?- recomendaciones(solicitud(amargo, fria, 1500, sola, tarde), R).
%
% 2) Uso integrado: Python ejecuta
%      swipl -q -s consultas.pl -g cli -t halt
%    y envia por la entrada estandar los hechos del catalogo, los precios
%    calculados por Scala y la solicitud. Prolog responde una linea JSON.
:- use_module(library(http/json)).
:- ensure_loaded(hechos).
:- ensure_loaded(reglas).
:- ensure_loaded(recomendaciones).
:- initialization(preparar_precios_locales).

% En el uso independiente no participa Scala: los totales se calculan aqui
% para poder probar las reglas por separado.
preparar_precios_locales :-
    retractall(precio_opcion(_, _, _)),
    forall(producto(B, bebida, _, _, P), assertz(precio_opcion(B, ninguno, P))),
    forall(( combina(B, A), producto(B, bebida, _, _, PB),
             producto(A, acompanamiento, _, _, PA), T is PB + PA ),
           assertz(precio_opcion(B, A, T))).

% ---------------------------------------------------------------------
% Modo integrado
% ---------------------------------------------------------------------
cli :-
    (   catch(cli_interno, E, (print_message(error, E), halt(2)))
    ->  true
    ;   print_message(error, cafeteria('no se pudo resolver la solicitud')),
        halt(3)
    ).

cli_interno :-
    set_stream(user_input, encoding(utf8)),
    set_stream(user_output, encoding(utf8)),
    limpiar_base,
    leer_hechos(user_input),
    findall(S, solicitud_recibida(S), Solicitudes),
    (   Solicitudes = [Solicitud] -> true
    ;   length(Solicitudes, N),
        format(atom(M), 'se esperaba una solicitud y llegaron ~d', [N]),
        throw(cafeteria(M))
    ),
    recomendaciones(Solicitud, Opciones),
    destacada(Opciones, Mejor),
    maplist(opcion_json(Solicitud, Mejor), Opciones, Lista),
    length(Opciones, Total),
    json_write_dict(current_output, _{total: Total, opciones: Lista}, [width(0)]),
    nl.

:- dynamic solicitud_recibida/1.

limpiar_base :-
    retractall(producto(_,_,_,_,_)), retractall(servido_en(_,_)),
    retractall(combina(_,_)), retractall(precio_opcion(_,_,_)),
    retractall(solicitud_recibida(_)).

% Solo se aceptan hechos conocidos y completamente instanciados.
% No se ejecuta ningun objetivo recibido.
leer_hechos(Flujo) :-
    read_term(Flujo, Termino, []),
    (   Termino == end_of_file -> true
    ;   aceptar_hecho(Termino), leer_hechos(Flujo)
    ).

aceptar_hecho(producto(I, C, S, T, P)) :-
    atom(I), memberchk(C, [bebida, acompanamiento]), sabor_valido(S),
    ( C == bebida -> temperatura_valida(T) ; T == ninguna ),
    integer(P), P > 0, !,
    assertz(producto(I, C, S, T, P)).
aceptar_hecho(servido_en(B, F)) :-
    atom(B), franja_valida(F), !, assertz(servido_en(B, F)).
aceptar_hecho(combina(B, A)) :-
    atom(B), atom(A), !, assertz(combina(B, A)).
aceptar_hecho(precio_opcion(B, A, T)) :-
    atom(B), atom(A), integer(T), T > 0, !, assertz(precio_opcion(B, A, T)).
aceptar_hecho(solicitud(S, T, P, M, F)) :-
    Sol = solicitud(S, T, P, M, F), solicitud_valida(Sol), !,
    assertz(solicitud_recibida(Sol)).
aceptar_hecho(Termino) :-
    format(atom(M), 'hecho no permitido o invalido: ~q', [Termino]),
    throw(cafeteria(M)).

opcion_json(Solicitud, Mejor, Opcion, Dict) :-
    Opcion = opcion(Tipo, Bebida, Acomp, Total, Maridaje),
    puntaje(Opcion, Puntaje),
    motivos(Solicitud, Opcion, Motivos),
    ( Opcion == Mejor -> Destacada = true ; Destacada = false ),
    Dict = _{tipo: Tipo, bebida: Bebida, acompanamiento: Acomp, total: Total,
             maridaje: Maridaje, puntaje: Puntaje, destacada: Destacada,
             motivos: Motivos}.

% ---------------------------------------------------------------------
% Demostracion independiente
% ---------------------------------------------------------------------
demo :-
    forall(member(caso(Cliente, Franja, Presupuesto, Modo),
                  [caso(cliente_1, tarde, 2000, combo),
                   caso(cliente_1, manana, 2000, sola),
                   caso(cliente_2, manana, 2000, combo),
                   caso(cliente_4, tarde, 1500, sola),
                   caso(cliente_5, tarde, 2000, combo)]),
           ( nombre_cliente(Cliente, Nombre),
             format('~n~w / ~w / ~w / ~d centimos~n', [Nombre, Franja, Modo, Presupuesto]),
             recomendaciones(Cliente, Franja, Presupuesto, Modo, Opciones),
             (   Opciones = [] -> writeln('  Sin coincidencias.')
             ;   destacada(Opciones, Mejor),
                 forall(member(O, Opciones),
                        ( O == Mejor -> format('  * ~w  (destacada)~n', [O])
                        ; format('    ~w~n', [O]) ))
             ) )).
