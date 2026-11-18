"""Interfaz grafica (tkinter, incluida en Python). Usa el mismo integrador que la consola.

Las consultas se ejecutan en un hilo aparte para que la ventana no se congele;
el hilo solo se comunica con la ventana mediante una cola (tkinter no es seguro
entre hilos).
"""
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from integracion.errores import IntegracionError, SolicitudRechazada
from integracion.integrador import Integrador
from interfaz.flujo import BarraFlujo, insignias_lenguajes
from modelos.cliente import FRANJAS, SABORES, TEMPERATURAS, Cliente, etiqueta
from modelos.recomendacion import ResultadoConsulta, Solicitud
from utils import archivos
from utils.formato import MARIDAJES, explicacion, nombre_opcion, soles

CAFE = "#3e2723"
CAFE_MEDIO = "#6d4c41"
CREMA = "#faf6f1"
BLANCO = "#ffffff"
DORADO = "#fff1c7"
VERDE = "#2e7d32"
NARANJA = "#c25e00"
GRIS = "#9e9e9e"
TEXTO = "#2b2b2b"
NUEVO = "➕ Nuevo cliente"



def franja_de_hora(hora: int) -> str:
    # Solo para el texto del boton; la franja real la calcula Scala.
    return "noche" if hora < 6 or hora >= 19 else "manana" if hora < 12 else "tarde"


class Aplicacion(tk.Tk):
    def __init__(self, sistema: Integrador):
        super().__init__()
        self.sistema = sistema
        self.cola: queue.Queue = queue.Queue()
        self.resultado: ResultadoConsulta | None = None
        self.ocupado = False

        self.title("Cafetería · Sistema experto multilenguaje")
        ancho = min(1320, self.winfo_screenwidth() - 60)
        alto = min(900, self.winfo_screenheight() - 90)
        self.geometry(f"{ancho}x{alto}+20+10")
        self.minsize(min(1000, ancho), min(640, alto))
        self.configure(bg=CREMA)
        self._estilos()
        self._encabezado()

        cuaderno = ttk.Notebook(self)
        cuaderno.pack(fill="both", expand=True, padx=14, pady=(8, 0))
        self.tab_recomendar = ttk.Frame(cuaderno, style="Crema.TFrame", padding=10)
        self.tab_menu = ttk.Frame(cuaderno, style="Crema.TFrame", padding=10)
        self.tab_historial = ttk.Frame(cuaderno, style="Crema.TFrame", padding=10)
        cuaderno.add(self.tab_recomendar, text="  Recomendar  ")
        cuaderno.add(self.tab_menu, text="  Menú  ")
        cuaderno.add(self.tab_historial, text="  Historial  ")
        cuaderno.bind("<<NotebookTabChanged>>", lambda e: self._cargar_historial())

        self._formulario()
        self._panel_resultados()
        self._menu()
        self._historial()

        self.estado = tk.StringVar(value="Preparando el módulo Scala…")
        tk.Label(self, textvariable=self.estado, anchor="w", bg=CAFE, fg=BLANCO,
                 font=("Segoe UI", 9), padx=12, pady=4).pack(fill="x", side="bottom")

        self._habilitar(False)
        threading.Thread(target=self._preparar, daemon=True).start()
        self.after(60, self._revisar_cola)

    # ------------------------------------------------------------------ estilo
    def _estilos(self) -> None:
        e = ttk.Style(self)
        e.theme_use("clam")
        base = ("Segoe UI", 10)
        e.configure(".", font=base, background=CREMA, foreground=TEXTO)
        e.configure("Crema.TFrame", background=CREMA)
        e.configure("Tarjeta.TFrame", background=BLANCO)
        e.configure("Tarjeta.TLabel", background=BLANCO)
        e.configure("Titulo.TLabel", background=BLANCO, font=("Segoe UI Semibold", 12), foreground=CAFE)
        e.configure("Campo.TLabel", background=BLANCO, font=("Segoe UI Semibold", 10), foreground=CAFE_MEDIO)
        e.configure("Nota.TLabel", background=BLANCO, foreground="#6b6b6b", font=("Segoe UI", 9))
        e.configure("TRadiobutton", background=BLANCO)
        e.configure("TCheckbutton", background=BLANCO)
        e.map("TRadiobutton", background=[("active", BLANCO)])
        e.map("TCheckbutton", background=[("active", BLANCO)])
        e.configure("Accion.TButton", font=("Segoe UI Semibold", 11), foreground=BLANCO,
                    background=CAFE_MEDIO, padding=(10, 8), borderwidth=0)
        e.map("Accion.TButton", background=[("disabled", GRIS), ("active", CAFE)])
        e.configure("TNotebook", background=CREMA, borderwidth=0)
        e.configure("TNotebook.Tab", font=("Segoe UI Semibold", 10), padding=(10, 6))
        e.map("TNotebook.Tab", background=[("selected", BLANCO)], foreground=[("selected", CAFE)])
        e.configure("Treeview", rowheight=28, font=base, fieldbackground=BLANCO, background=BLANCO)
        e.configure("Treeview.Heading", font=("Segoe UI Semibold", 10), background="#efe6dc", foreground=CAFE)
        e.map("Treeview", background=[("selected", CAFE_MEDIO)], foreground=[("selected", BLANCO)])

    def _encabezado(self) -> None:
        barra = tk.Frame(self, bg=CAFE)
        barra.pack(fill="x")
        tk.Label(barra, text="☕  Cafetería — Sistema experto de recomendación", bg=CAFE, fg=BLANCO,
                 font=("Segoe UI Semibold", 17), padx=16, pady=(10)).pack(anchor="w")
        insignias_lenguajes(barra, fondo=CAFE, texto="#d7ccc8").pack(anchor="w", padx=18, pady=(0, 10))

    def _tarjeta(self, padre, **grid) -> ttk.Frame:
        marco = ttk.Frame(padre, style="Tarjeta.TFrame", padding=14)
        marco.grid(**grid)
        return marco

    # ------------------------------------------------------------- formulario
    def _formulario(self) -> None:
        t = self.tab_recomendar
        t.columnconfigure(1, weight=1)
        t.rowconfigure(0, weight=1)
        f = self._tarjeta(t, row=0, column=0, sticky="nsw", padx=(0, 10))

        ttk.Label(f, text="Tu pedido", style="Titulo.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(f, text="Perfil", style="Campo.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.perfil = tk.StringVar()
        self.combo_perfil = ttk.Combobox(f, textvariable=self.perfil, state="readonly", width=30)
        self.combo_perfil.grid(row=2, column=0, columnspan=2, sticky="we")
        self.combo_perfil.bind("<<ComboboxSelected>>", lambda e: self._perfil_elegido())

        ttk.Label(f, text="Nombre", style="Campo.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 2))
        self.nombre = tk.StringVar()
        self.entrada_nombre = ttk.Entry(f, textvariable=self.nombre, width=32)
        self.entrada_nombre.grid(row=4, column=0, columnspan=2, sticky="we")

        self.sabor = tk.StringVar(value="dulce")
        self._grupo(f, 5, "Sabor preferido", self.sabor, [(etiqueta(s), s) for s in SABORES], columnas=2)
        self.temperatura = tk.StringVar(value="fria")
        self._grupo(f, 8, "Temperatura", self.temperatura, [(etiqueta(x), x) for x in TEMPERATURAS], columnas=2)

        ttk.Label(f, text="Presupuesto total (S/)", style="Campo.TLabel").grid(row=10, column=0, columnspan=2,
                                                                               sticky="w", pady=(6, 2))
        self.presupuesto = tk.StringVar(value="20.00")
        ttk.Entry(f, textvariable=self.presupuesto, width=12).grid(row=11, column=0, sticky="w")
        ttk.Label(f, text="Ej.: 20 o 20,50", style="Nota.TLabel").grid(row=11, column=1, sticky="w")

        self.modo = tk.StringVar(value="combo")
        self._grupo(f, 12, "Pedido", self.modo, [("Solo bebida", "sola"), ("Combo", "combo")], columnas=2)

        hora = datetime.now().hour
        self.franja = tk.StringVar(value="auto")
        self._grupo(f, 14, "Franja horaria", self.franja,
                    [(f"Ahora ({etiqueta(franja_de_hora(hora))})", "auto")] + [(etiqueta(x), x) for x in FRANJAS],
                    columnas=2)

        self.guardar = tk.BooleanVar(value=False)
        self.check_guardar = ttk.Checkbutton(f, text="Guardar o actualizar el perfil", variable=self.guardar)
        self.check_guardar.grid(row=17, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.boton = ttk.Button(f, text="☕  Recomendar", style="Accion.TButton", command=self._recomendar)
        self.boton.grid(row=18, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self.bind("<Return>", lambda e: self._recomendar())
        self._actualizar_perfiles()

    def _grupo(self, padre, fila, titulo, variable, opciones, columnas=1) -> None:
        ttk.Label(padre, text=titulo, style="Campo.TLabel").grid(row=fila, column=0, columnspan=2,
                                                                 sticky="w", pady=(6, 1))
        for i, (texto, valor) in enumerate(opciones):
            ttk.Radiobutton(padre, text=texto, value=valor, variable=variable).grid(
                row=fila + 1 + i // columnas, column=i % columnas, sticky="w", padx=(0, 12))

    def _actualizar_perfiles(self, seleccionar: str | None = None) -> None:
        nombres = [c.nombre for c in self.sistema.clientes]
        self.combo_perfil["values"] = nombres + [NUEVO]
        self.perfil.set(seleccionar or (nombres[0] if nombres else NUEVO))
        self._perfil_elegido()

    def _perfil_elegido(self) -> None:
        cliente = self.sistema.buscar_cliente(self.perfil.get())
        if cliente:
            # Carga las preferencias guardadas; se pueden cambiar para esta consulta.
            self.nombre.set(cliente.nombre)
            self.entrada_nombre.configure(state="disabled")
            self.sabor.set(cliente.sabor)
            self.temperatura.set(cliente.temperatura)
            self.guardar.set(False)
        else:
            self.nombre.set("")
            self.entrada_nombre.configure(state="normal")
            self.entrada_nombre.focus_set()
            self.guardar.set(True)

    # --------------------------------------------------------------- resultados
    def _panel_resultados(self) -> None:
        r = self._tarjeta(self.tab_recomendar, row=0, column=1, sticky="nsew")
        r.columnconfigure(0, weight=1)
        r.rowconfigure(3, weight=1)

        # Recorrido de la consulta dibujado con el simbolo de cada lenguaje.
        self.flujo = BarraFlujo(r)
        self.flujo.grid(row=0, column=0, sticky="we")
        self.paso_actual = 0

        self.resumen = tk.StringVar(value="Completa tu pedido y pulsa «Recomendar».")
        ttk.Label(r, textvariable=self.resumen, style="Titulo.TLabel", wraplength=720).grid(
            row=1, column=0, sticky="w", pady=(12, 6))
        self.tiempos = tk.StringVar()
        ttk.Label(r, textvariable=self.tiempos, style="Nota.TLabel").grid(row=2, column=0, sticky="w")

        columnas = ("opcion", "precio", "tipo", "maridaje", "puntaje")
        self.tabla = ttk.Treeview(r, columns=columnas, show="headings", height=5, selectmode="browse")
        for col, texto, ancho, ancla in [("opcion", "Opción", 330, "w"), ("precio", "Precio", 90, "e"),
                                         ("tipo", "Coincidencia", 150, "center"),
                                         ("maridaje", "Maridaje", 110, "center"), ("puntaje", "Puntaje", 70, "center")]:
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor=ancla, stretch=(col == "opcion"))
        self.tabla.tag_configure("destacada", background=DORADO, font=("Segoe UI Semibold", 10))
        self.tabla.tag_configure("alternativa", foreground=NARANJA)
        self.tabla.grid(row=3, column=0, sticky="nsew", pady=(6, 8))
        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._mostrar_detalle())

        ttk.Label(r, text="¿Por qué se recomienda?", style="Campo.TLabel").grid(row=4, column=0, sticky="w")
        self.detalle = tk.Text(r, height=9, wrap="word", relief="flat", bg="#fbf8f4", fg=TEXTO,
                               font=("Segoe UI", 10), padx=10, pady=8)
        self.detalle.grid(row=5, column=0, sticky="we", pady=(4, 0))
        self.detalle.tag_configure("negrita", font=("Segoe UI Semibold", 10))
        self.detalle.tag_configure("aviso", foreground=NARANJA, font=("Segoe UI Semibold", 10))
        self.detalle.configure(state="disabled")

    def _pintar_flujo(self, actual: int, milisegundos: list[int] | None = None) -> None:
        self.paso_actual = actual
        self.flujo.pintar(actual, milisegundos)

    def _escribir_detalle(self, partes: list[tuple[str, str]]) -> None:
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        for texto, estilo in partes:
            self.detalle.insert("end", texto, estilo)
        self.detalle.configure(state="disabled")

    # ------------------------------------------------------------------ menu
    def _menu(self) -> None:
        t = self.tab_menu
        t.columnconfigure(0, weight=1)
        t.rowconfigure(0, weight=1)
        columnas = ("producto", "tipo", "sabor", "temperatura", "precio", "horario", "combina")
        tabla = ttk.Treeview(t, columns=columnas, show="headings")
        for col, texto, ancho in [("producto", "Producto", 230), ("tipo", "Tipo", 150), ("sabor", "Sabor", 90),
                                  ("temperatura", "Temperatura", 100), ("precio", "Precio", 90),
                                  ("horario", "Horario", 190), ("combina", "Combina con", 330)]:
            tabla.heading(col, text=texto)
            tabla.column(col, width=ancho, anchor="w")
        c = self.sistema.catalogo
        for b in c.bebidas:
            tabla.insert("", "end", values=(b.nombre, "Bebida", etiqueta(b.sabor), etiqueta(b.temperatura),
                                            soles(b.precio), ", ".join(etiqueta(f) for f in b.franjas),
                                            ", ".join(c.nombre(a) for a in b.acompanamientos)))
        for a in c.acompanamientos:
            tabla.insert("", "end", values=(a.nombre, "Acompañamiento", etiqueta(a.sabor), "—",
                                            soles(a.precio), "Con su bebida", ""))
        tabla.grid(row=0, column=0, sticky="nsew")

    # -------------------------------------------------------------- historial
    def _historial(self) -> None:
        t = self.tab_historial
        t.columnconfigure(0, weight=1)
        t.rowconfigure(0, weight=1)
        columnas = ("fecha", "cliente", "pedido", "franja", "presupuesto", "opciones", "destacada")
        self.tabla_historial = ttk.Treeview(t, columns=columnas, show="headings")
        for col, texto, ancho in [("fecha", "Fecha", 150), ("cliente", "Cliente", 120), ("pedido", "Pedido", 170),
                                  ("franja", "Franja", 80), ("presupuesto", "Presupuesto", 100),
                                  ("opciones", "Opciones", 80), ("destacada", "Destacada", 420)]:
            self.tabla_historial.heading(col, text=texto)
            self.tabla_historial.column(col, width=ancho, anchor="w")
        self.tabla_historial.grid(row=0, column=0, sticky="nsew")
        ttk.Label(t, text="Se guardan las últimas 200 consultas en data/resultados.json.",
                  background=CREMA, foreground="#6b6b6b").grid(row=1, column=0, sticky="w", pady=(6, 0))

    def _cargar_historial(self) -> None:
        self.tabla_historial.delete(*self.tabla_historial.get_children())
        try:
            registros = archivos.leer_resultados(self.sistema.datos)
        except archivos.DatosInvalidos as e:
            self.estado.set(str(e))
            return
        for h in reversed(registros):
            self.tabla_historial.insert("", "end", values=(
                h.get("fecha", "").replace("T", " "), h.get("cliente", ""),
                {"sola": "Solo bebida", "combo": "Combo"}.get(h.get("modo", ""), h.get("modo", "")),
                etiqueta(h.get("franja", "")), h.get("presupuesto", ""), h.get("total_opciones", 0),
                h.get("destacada") or "Sin opciones"))

    # --------------------------------------------------------- acciones e hilos
    def _habilitar(self, activo: bool) -> None:
        self.boton.configure(state="normal" if activo else "disabled")

    def _preparar(self) -> None:
        try:
            compilo = self.sistema.preparar()
            self.cola.put(("listo", "Listo. Scala compilado." if compilo else "Listo."))
        except Exception as e:  # noqa: BLE001  se muestra al usuario
            self.cola.put(("fatal", str(e)))

    def _leer_solicitud(self) -> tuple[Solicitud, bool]:
        existente = self.sistema.buscar_cliente(self.perfil.get())
        nombre = existente.nombre if existente else archivos.nombre_cliente(self.nombre.get())
        if not existente and self.sistema.buscar_cliente(nombre):
            raise archivos.DatosInvalidos("Ese nombre ya tiene un perfil: elígelo en la lista.")
        cliente = Cliente(nombre, self.sabor.get(), self.temperatura.get())
        return Solicitud(cliente, archivos.dinero(self.presupuesto.get()), self.modo.get(),
                         self.franja.get()), self.guardar.get()

    def _recomendar(self) -> None:
        if self.ocupado or str(self.boton["state"]) == "disabled":
            return
        try:
            solicitud, guardar = self._leer_solicitud()
        except archivos.DatosInvalidos as e:
            messagebox.showwarning("Revisa tu pedido", str(e), parent=self)
            return
        if guardar:
            try:
                self.sistema.guardar_cliente(solicitud.cliente)
                self._actualizar_perfiles(solicitud.cliente.nombre)
            except (OSError, archivos.DatosInvalidos) as e:
                messagebox.showerror("No se pudo guardar el perfil", str(e), parent=self)
        self.ocupado = True
        self._habilitar(False)
        self.tabla.delete(*self.tabla.get_children())
        self._escribir_detalle([])
        self.resumen.set("Consultando…")
        self.tiempos.set("")
        threading.Thread(target=self._consultar, args=(solicitud,), daemon=True).start()

    def _consultar(self, solicitud: Solicitud) -> None:
        try:
            r = self.sistema.recomendar(solicitud, avance=lambda n, texto: self.cola.put(("paso", n, texto)))
            self.cola.put(("resultado", r))
        except SolicitudRechazada as e:
            self.cola.put(("rechazo", str(e)))
        except (IntegracionError, archivos.DatosInvalidos, OSError) as e:
            self.cola.put(("error", str(e)))

    def _revisar_cola(self) -> None:
        try:
            while True:
                mensaje = self.cola.get_nowait()
                tipo = mensaje[0]
                if tipo == "listo":
                    self._habilitar(True)
                    self.estado.set(mensaje[1])
                elif tipo == "fatal":
                    self.estado.set("No se puede consultar: " + mensaje[1])
                    messagebox.showerror("Falta una herramienta", mensaje[1], parent=self)
                elif tipo == "paso":
                    self._pintar_flujo(mensaje[1])
                    self.estado.set(mensaje[2] + "…")
                elif tipo == "resultado":
                    self._mostrar_resultado(mensaje[1])
                    self._terminar("Consulta completada y guardada en el historial.")
                elif tipo in ("rechazo", "error"):
                    self.flujo.fallo(self.paso_actual)
                    self.resumen.set("No se pudo completar la consulta.")
                    self._escribir_detalle([(mensaje[1], "aviso")])
                    self._terminar(mensaje[1])
        except queue.Empty:
            pass
        self.after(60, self._revisar_cola)

    def _terminar(self, estado: str) -> None:
        self.ocupado = False
        self._habilitar(True)
        self.estado.set(estado)

    def _mostrar_resultado(self, r: ResultadoConsulta) -> None:
        self.resultado = r
        self._pintar_flujo(6, [p.milisegundos for p in r.pasos])
        franja = etiqueta(r.franja) + (" (según la hora)" if r.franja_automatica else "")
        generadas = r.resumen_scala.get("opciones_generadas", 0)
        self.tiempos.set("  ·  ".join(f"{p.modulo}: {p.milisegundos} ms" for p in r.pasos if p.milisegundos))
        if not r.opciones:
            self.resumen.set(f"Sin opciones · Franja {franja} · Scala evaluó {generadas} opciones")
            self._escribir_detalle([
                ("Ninguna opción cumple a la vez sabor, franja, presupuesto y tipo de pedido.\n", "negrita"),
                ("No cambiamos tu sabor ni superamos tu presupuesto. Prueba con otra franja, "
                 "un presupuesto mayor o solo bebida.", "")])
            return
        alternativas = r.opciones[0].tipo == "alternativa"
        self.resumen.set(f"{len(r.opciones)} {'alternativas' if alternativas else 'opciones exactas'} "
                         f"de {generadas} evaluadas · Franja {franja} · Presupuesto {soles(r.presupuesto_centimos)}")
        destacada_id = None
        for i, o in enumerate(r.opciones):
            etiquetas = (["destacada"] if o.destacada else []) + (["alternativa"] if o.tipo == "alternativa" else [])
            nombre = ("★ " if o.destacada else "   ") + nombre_opcion(o, self.sistema.catalogo)
            tipo = "Exacta" if o.tipo == "exacta" else "Otra temperatura"
            iid = self.tabla.insert("", "end", iid=str(i), tags=etiquetas,
                                    values=(nombre, soles(o.total), tipo, MARIDAJES[o.maridaje], o.puntaje))
            if o.destacada:
                destacada_id = iid
        if destacada_id is not None:
            self.tabla.selection_set(destacada_id)
            self.tabla.see(destacada_id)

    def _mostrar_detalle(self) -> None:
        seleccion = self.tabla.selection()
        if not seleccion or not self.resultado:
            return
        o = self.resultado.opciones[int(seleccion[0])]
        partes = [(nombre_opcion(o, self.sistema.catalogo) + f" — {soles(o.total)}\n", "negrita")]
        for frase in explicacion(o, self.resultado, self.sistema.catalogo):
            estilo = "aviso" if frase.startswith(("ALTERNATIVA", "DESTACADA")) else ""
            partes.append(("•  " + frase + "\n", estilo))
        self._escribir_detalle(partes)


def ejecutar(sistema: Integrador) -> None:
    try:  # texto nitido en pantallas con escalado (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    Aplicacion(sistema).mainloop()
