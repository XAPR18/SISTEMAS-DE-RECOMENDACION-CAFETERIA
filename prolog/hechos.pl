% ARCHIVO GENERADO por Python desde data/productos.json y data/clientes.json.
% No editar a mano: los cambios se hacen en los JSON y se regenera al iniciar.
% Precios en centimos: 1250 representa S/ 12,50.

% producto(Id, Categoria, Sabor, Temperatura, Precio).
producto(espresso, bebida, amargo, caliente, 800).
producto(americano, bebida, amargo, caliente, 700).
producto(cold_brew, bebida, amargo, fria, 1100).
producto(capuchino, bebida, suave, caliente, 1000).
producto(latte, bebida, suave, caliente, 950).
producto(chocolate_caliente, bebida, dulce, caliente, 900).
producto(frappe_mocha, bebida, dulce, fria, 1250).
producto(milkshake_vainilla, bebida, dulce, fria, 1100).
producto(te_helado, bebida, citrico, fria, 900).
producto(limonada_frozen, bebida, citrico, fria, 850).
producto(infusion_jengibre, bebida, citrico, caliente, 750).
producto(croissant, acompanamiento, suave, ninguna, 700).
producto(brownie, acompanamiento, dulce, ninguna, 600).
producto(alfajor, acompanamiento, dulce, ninguna, 450).
producto(galleta_avena, acompanamiento, suave, ninguna, 350).
producto(cheesecake_maracuya, acompanamiento, citrico, ninguna, 900).

% nombre_producto(Id, NombreVisible).
nombre_producto(espresso, 'Espresso').
nombre_producto(americano, 'Cafe americano').
nombre_producto(cold_brew, 'Cold brew').
nombre_producto(capuchino, 'Capuchino').
nombre_producto(latte, 'Cafe latte').
nombre_producto(chocolate_caliente, 'Chocolate caliente').
nombre_producto(frappe_mocha, 'Frappe mocha').
nombre_producto(milkshake_vainilla, 'Milkshake de vainilla').
nombre_producto(te_helado, 'Te helado de limon').
nombre_producto(limonada_frozen, 'Limonada frozen').
nombre_producto(infusion_jengibre, 'Infusion de limon y jengibre').
nombre_producto(croissant, 'Croissant').
nombre_producto(brownie, 'Brownie').
nombre_producto(alfajor, 'Alfajor').
nombre_producto(galleta_avena, 'Galleta de avena').
nombre_producto(cheesecake_maracuya, 'Cheesecake de maracuya').

% servido_en(Bebida, Franja).
servido_en(espresso, manana).
servido_en(espresso, tarde).
servido_en(americano, manana).
servido_en(americano, tarde).
servido_en(americano, noche).
servido_en(cold_brew, tarde).
servido_en(cold_brew, noche).
servido_en(capuchino, manana).
servido_en(capuchino, tarde).
servido_en(capuchino, noche).
servido_en(latte, manana).
servido_en(latte, tarde).
servido_en(chocolate_caliente, tarde).
servido_en(chocolate_caliente, noche).
servido_en(frappe_mocha, tarde).
servido_en(frappe_mocha, noche).
servido_en(milkshake_vainilla, tarde).
servido_en(te_helado, manana).
servido_en(te_helado, tarde).
servido_en(limonada_frozen, manana).
servido_en(limonada_frozen, tarde).
servido_en(infusion_jengibre, manana).
servido_en(infusion_jengibre, noche).

% combina(Bebida, Acompanamiento).
combina(espresso, croissant).
combina(espresso, brownie).
combina(americano, croissant).
combina(americano, alfajor).
combina(americano, galleta_avena).
combina(cold_brew, brownie).
combina(cold_brew, alfajor).
combina(capuchino, croissant).
combina(capuchino, galleta_avena).
combina(latte, croissant).
combina(latte, galleta_avena).
combina(latte, brownie).
combina(chocolate_caliente, brownie).
combina(chocolate_caliente, alfajor).
combina(frappe_mocha, brownie).
combina(frappe_mocha, alfajor).
combina(milkshake_vainilla, alfajor).
combina(milkshake_vainilla, galleta_avena).
combina(te_helado, croissant).
combina(te_helado, cheesecake_maracuya).
combina(limonada_frozen, cheesecake_maracuya).
combina(limonada_frozen, galleta_avena).
combina(infusion_jengibre, galleta_avena).

% nombre_cliente(Id, NombreVisible).
nombre_cliente(cliente_1, 'Ana').
nombre_cliente(cliente_2, 'Luis').
nombre_cliente(cliente_3, 'Rosa').
nombre_cliente(cliente_4, 'Carlos').
nombre_cliente(cliente_5, 'Sofia').
nombre_cliente(cliente_6, 'andres').

% gusto(Cliente, Sabor).
gusto(cliente_1, dulce).
gusto(cliente_2, amargo).
gusto(cliente_3, suave).
gusto(cliente_4, amargo).
gusto(cliente_5, suave).
gusto(cliente_6, amargo).

% prefiere(Cliente, Temperatura).
prefiere(cliente_1, fria).
prefiere(cliente_2, caliente).
prefiere(cliente_3, caliente).
prefiere(cliente_4, fria).
prefiere(cliente_5, fria).
prefiere(cliente_6, caliente).
