% Reglas de inferencia del sistema experto.
% Hechos que usan estas reglas:
%   producto/5, servido_en/2, combina/2       catalogo (hechos.pl o enviados por Python)
%   precio_opcion/3                           precio total calculado por Scala
%   solicitud(Sabor, Temperatura, Presupuesto, Modo, Franja)
% Montos en centimos: 2000 representa S/ 20,00.

:- dynamic producto/5, servido_en/2, combina/2, precio_opcion/3.
:- dynamic nombre_producto/2, nombre_cliente/2, gusto/2, prefiere/2.

sabor_valido(S) :- memberchk(S, [dulce, amargo, suave, citrico]).
temperatura_valida(T) :- memberchk(T, [fria, caliente]).
franja_valida(F) :- memberchk(F, [manana, tarde, noche]).
modo_valido(M) :- memberchk(M, [sola, combo]).

% ---------------------------------------------------------------------
% Conocimiento del maridaje: que sabor de acompanamiento complementa
% a cada sabor de bebida (contraste agradable).
% ---------------------------------------------------------------------
complementa(amargo, dulce).
complementa(citrico, dulce).
complementa(citrico, suave).
complementa(suave, dulce).

% Clasificacion del acompanamiento respecto de la bebida.
maridaje(_, ninguno, sin_acompanamiento).
maridaje(Bebida, Acomp, Tipo) :-
    Acomp \== ninguno,
    producto(Bebida, bebida, SaborBebida, _, _),
    producto(Acomp, acompanamiento, SaborAcomp, _, _),
    (   SaborBebida == SaborAcomp -> Tipo = armonia
    ;   complementa(SaborBebida, SaborAcomp) -> Tipo = contraste
    ;   Tipo = neutro
    ).

% El tipo de pedido exige o prohibe el acompanamiento.
compatible(_, ninguno, sola).
compatible(Bebida, Acomp, combo) :- combina(Bebida, Acomp).

% ---------------------------------------------------------------------
% Reglas principales. Nunca se relaja sabor, horario ni presupuesto.
% ---------------------------------------------------------------------
candidata(solicitud(Sabor, _, Presupuesto, Modo, Franja), Bebida, Acomp, Total) :-
    producto(Bebida, bebida, Sabor, _, _),
    servido_en(Bebida, Franja),
    precio_opcion(Bebida, Acomp, Total),
    compatible(Bebida, Acomp, Modo),
    Total =< Presupuesto.

exacta(Solicitud, Bebida, Acomp, Total) :-
    candidata(Solicitud, Bebida, Acomp, Total),
    Solicitud = solicitud(_, Temperatura, _, _, _),
    producto(Bebida, bebida, _, Temperatura, _).

% Si existe al menos una exacta, solo se muestran exactas.
% Si no existe ninguna (negacion por fallo), se permite cambiar la temperatura.
recomendar(Solicitud, opcion(Tipo, Bebida, Acomp, Total, Maridaje)) :-
    (   exacta(Solicitud, Bebida, Acomp, Total), Tipo = exacta
    ;   \+ exacta(Solicitud, _, _, _),
        candidata(Solicitud, Bebida, Acomp, Total), Tipo = alternativa
    ),
    maridaje(Bebida, Acomp, Maridaje).

% ---------------------------------------------------------------------
% Puntaje para elegir la opcion destacada.
% ---------------------------------------------------------------------
puntos_tipo(exacta, 3).
puntos_tipo(alternativa, 0).
puntos_maridaje(armonia, 2).
puntos_maridaje(contraste, 2).
puntos_maridaje(neutro, 0).
puntos_maridaje(sin_acompanamiento, 0).

puntaje(opcion(Tipo, _, _, _, Maridaje), Puntaje) :-
    puntos_tipo(Tipo, P1), puntos_maridaje(Maridaje, P2),
    Puntaje is P1 + P2.

% Motivos de la recomendacion. Python los convierte en una explicacion.
motivos(solicitud(_, Temperatura, _, _, _), opcion(_, Bebida, _, _, Maridaje), Motivos) :-
    producto(Bebida, bebida, _, TempBebida, _),
    (   TempBebida == Temperatura -> MotivoTemp = temperatura_exacta
    ;   MotivoTemp = temperatura_cambiada
    ),
    atom_concat(maridaje_, Maridaje, MotivoMaridaje),
    Motivos = [sabor_coincide, servida_en_franja, dentro_del_presupuesto, MotivoTemp, MotivoMaridaje].
