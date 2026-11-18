"""Interfaz de texto (modo consola). Usa el mismo integrador que la ventana."""
from datetime import datetime

from integracion.errores import IntegracionError, SolicitudRechazada
from integracion.integrador import Integrador
from modelos.cliente import FRANJAS, SABORES, TEMPERATURAS, Cliente, etiqueta
from modelos.recomendacion import Solicitud
from utils import archivos
from utils.formato import MARIDAJES, explicacion, nombre_opcion, soles


class FinEntrada(Exception):
    pass


def leer(mensaje: str) -> str:
    try:
        return input(mensaje).strip()
    except EOFError:
        raise FinEntrada from None


def elegir(titulo: str, opciones: list[tuple[str, object]]):
    print(f"\n{titulo}")
    for i, (texto, _) in enumerate(opciones, 1):
        print(f"  {i}. {texto}")
    while True:
        r = leer("Elige una opción: ")
        if r.isdigit() and 1 <= int(r) <= len(opciones):
            return opciones[int(r) - 1][1]
        print(f"  Escribe un número del 1 al {len(opciones)}.")


def pedir_valor(mensaje: str, convertir):
    while True:
        try:
            return convertir(leer(mensaje))
        except archivos.DatosInvalidos as e:
            print(f"  {e}")


def mostrar_menu(sistema: Integrador) -> None:
    print("\nMENÚ DE LA CAFETERÍA")
    for b in sistema.catalogo.bebidas:
        franjas = ", ".join(etiqueta(f) for f in b.franjas)
        print(f"- {b.nombre}: {soles(b.precio)} | {etiqueta(b.sabor)}, {etiqueta(b.temperatura)} | {franjas}")
    print("Acompañamientos:")
    for a in sistema.catalogo.acompanamientos:
        print(f"- {a.nombre}: {soles(a.precio)} | {etiqueta(a.sabor)}")


def pedir_cliente(sistema: Integrador) -> Cliente:
    opciones = [(f"{c.nombre} ({etiqueta(c.sabor)}, {etiqueta(c.temperatura)})", c) for c in sistema.clientes]
    elegido = elegir("Selecciona un perfil:", opciones + [("Nuevo cliente", None)])
    if elegido is not None:
        mantener = elegir(f"¿Usar las preferencias guardadas de {elegido.nombre}?",
                          [("Sí, usar mis preferencias", True), ("No, elegir otras para esta consulta", False)])
        if mantener:
            return elegido
        nombre = elegido.nombre
    else:
        def nombre_nuevo(texto):
            n = archivos.nombre_cliente(texto)
            if sistema.buscar_cliente(n):
                raise archivos.DatosInvalidos("Ese nombre ya tiene un perfil. Escribe otro.")
            return n
        nombre = pedir_valor("Tu nombre: ", nombre_nuevo)
    sabor = elegir("¿Qué sabor prefieres?", [(etiqueta(s), s) for s in SABORES])
    temperatura = elegir("¿Cómo prefieres tu bebida?", [(etiqueta(t), t) for t in TEMPERATURAS])
    cliente = Cliente(nombre, sabor, temperatura)
    if elegir("¿Guardar este perfil en data/clientes.json?", [("Sí", True), ("No, solo esta vez", False)]):
        sistema.guardar_cliente(cliente)
        print("  Perfil guardado.")
    return cliente


def buscar(sistema: Integrador) -> None:
    cliente = pedir_cliente(sistema)
    presupuesto = pedir_valor("Presupuesto total en soles (ejemplo 20,50): ", archivos.dinero)
    modo = elegir("¿Qué deseas?", [("Solo bebida", "sola"), ("Combo con acompañamiento", "combo")])
    hora = datetime.now().hour
    franja = elegir("¿Para qué franja?", [(f"Hora actual de la PC ({hora}:00)", "auto")]
                    + [(etiqueta(f), f) for f in FRANJAS])
    solicitud = Solicitud(cliente, presupuesto, modo, franja)

    print()
    try:
        r = sistema.recomendar(solicitud, avance=lambda n, texto: print(f"  [{n}/5] {texto}..."))
    except SolicitudRechazada as e:
        print(f"\n{e}")
        return
    except IntegracionError as e:
        print(f"\nNo se pudo completar la consulta: {e}")
        return

    print(f"\nScala generó {r.resumen_scala['opciones_generadas']} opciones con precio; "
          f"Prolog seleccionó {len(r.opciones)}. Franja: {etiqueta(r.franja)}"
          f"{' (según la hora)' if r.franja_automatica else ''}.")
    if not r.opciones:
        print("No hay opciones que cumplan sabor, franja, presupuesto y tipo de pedido.")
        print("No cambiamos tu sabor ni superamos tu presupuesto. Prueba con otra franja o presupuesto.")
        return
    for i, o in enumerate(r.opciones, 1):
        marca = "★" if o.destacada else " "
        tipo = "COINCIDENCIA EXACTA" if o.tipo == "exacta" else "ALTERNATIVA DE TEMPERATURA"
        print(f"\n{marca} {i}. {nombre_opcion(o, sistema.catalogo)} | {soles(o.total)} | {tipo} | "
              f"maridaje: {MARIDAJES[o.maridaje]}")
        for frase in explicacion(o, r, sistema.catalogo):
            print(f"     - {frase}")


def historial(sistema: Integrador) -> None:
    registros = archivos.leer_resultados(sistema.datos)[-10:]
    if not registros:
        print("\nTodavía no hay consultas guardadas.")
    for h in registros:
        print(f"- {h['fecha']} | {h['cliente']} | {etiqueta(h['modo'])} | {etiqueta(h['franja'])} | "
              f"{h['presupuesto']} | {h['destacada'] or 'sin opciones'}")


def ejecutar(sistema: Integrador) -> None:
    print("=== SISTEMA EXPERTO DE LA CAFETERÍA ===")
    print("Python integra · Scala procesa · Prolog infiere. No usa IA generativa.")
    try:
        if sistema.preparar():
            print("(Se compiló el módulo Scala.)")
        while True:
            print("\n1. Ver menú\n2. Buscar una recomendación\n3. Ver perfiles\n4. Ver historial\n0. Salir")
            op = leer("Opción: ")
            if op == "0":
                print("Hasta pronto.")
                return
            elif op == "1":
                mostrar_menu(sistema)
            elif op == "2":
                buscar(sistema)
            elif op == "3":
                for c in sistema.clientes:
                    print(f"- {c.nombre}: {etiqueta(c.sabor)}, {etiqueta(c.temperatura)}")
            elif op == "4":
                historial(sistema)
            else:
                print("Elige 0, 1, 2, 3 o 4.")
    except FinEntrada:
        print("\nFin de la entrada. Sesión terminada.")
