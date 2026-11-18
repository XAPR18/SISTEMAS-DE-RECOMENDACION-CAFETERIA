"""Simbolos de los lenguajes y barra de flujo de la ventana.

Los logos se dibujan con figuras del Canvas de tkinter (sin imagenes externas), sobre una
cuadricula de 64 x 64 unidades igual a la de los SVG de la interfaz web, y se escalan al
tamano pedido. Cuando un paso aun no empieza su logo se dibuja en tonos de gris.
"""
import tkinter as tk

PASOS = [("python", "Obtiene datos"), ("scala", "Procesa"), ("python", "Envía"),
         ("prolog", "Infiere"), ("python", "Muestra")]

ESTADOS = {
    #            fondo      borde      texto      insignia
    "pendiente": ("#f6f2ec", "#e7ded2", "#a39a90", "#cfc6bb"),
    "activo":    ("#fff4dc", "#d4ad70", "#3e2723", "#b98b45"),
    "hecho":     ("#ecf6ed", "#7cb987", "#2e7d32", "#2e7d32"),
    "error":     ("#fdecea", "#e57373", "#b71c1c", "#c62828"),
}


def escala(widget: tk.Misc) -> float:
    """Factor de pantalla: en Windows con zoom 125 % o 150 % el texto crece y las figuras no."""
    return max(1.0, widget.winfo_fpixels("1i") / 96)


def _gris(color: str) -> str:
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    y = 170 + (int(0.3 * r + 0.59 * g + 0.11 * b) * 70) // 255   # gris suave, nunca negro
    return f"#{y:02x}{y:02x}{y:02x}"


def rectangulo(lienzo: tk.Canvas, x0, y0, x1, y1, r, **opciones) -> int:
    """Rectangulo con esquinas redondeadas."""
    puntos = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
              x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return lienzo.create_polygon(puntos, smooth=True, **opciones)


def dibujar_logo(lienzo: tk.Canvas, lenguaje: str, x: float, y: float, lado: float, gris: bool = False) -> None:
    """Dibuja el simbolo de Python, Scala o Prolog en el cuadrado (x, y, lado)."""
    e = lado / 64
    c = _gris if gris else (lambda col: col)

    def p(*coords):  # pasa puntos de la cuadricula 64x64 a pixeles
        return [x + v * e if k % 2 == 0 else y + v * e for k, v in enumerate(coords)]

    if lenguaje == "python":
        # Serpiente azul (arriba-izquierda) y amarilla (abajo-derecha, girada 180°).
        for color, cajas, ojo in (
            ("#3f7cb5", [(20.6, 4, 43.4, 26.4), (8.4, 16, 32, 26.4), (8.4, 16, 19, 38.5)], (25.5, 9.6)),
            ("#ffd43b", [(20.6, 37.6, 43.4, 60), (32, 37.6, 55.6, 48), (45, 25.5, 55.6, 48)], (38.5, 54.4)),
        ):
            for caja in cajas:
                rectangulo(lienzo, *p(*caja), 6 * e, fill=c(color), outline="")
            lienzo.create_oval(*p(ojo[0] - 2.4, ojo[1] - 2.4, ojo[0] + 2.4, ojo[1] + 2.4), fill="#ffffff", outline="")
    elif lenguaje == "scala":
        # Tres cintas rojas en espiral con su cara posterior mas oscura.
        for base in (17.5, 33.5):
            lienzo.create_polygon(p(17, base, 47, base + 7.2, 47, base + 12.8, 17, base + 5.6),
                                  fill=c("#8c1c13"), outline="")
        for base in (6.5, 22.5, 38.5):
            lienzo.create_polygon(p(17, base, 47, base + 7.2, 47, base + 18.2, 17, base + 11),
                                  fill=c("#de3423"), outline="")
    else:
        # Buho estilizado, simbolo de SWI-Prolog.
        lienzo.create_polygon(p(14, 8, 23, 16, 41, 16, 50, 8, 50, 30, 47, 43, 40, 52, 32, 56,
                                24, 52, 17, 43, 14, 30), fill=c("#2b2b2b"), outline="")
        for ox in (24.5, 39.5):
            lienzo.create_oval(*p(ox - 8.6, 18.4, ox + 8.6, 35.6), fill=c("#f4b43d"), outline="")
            lienzo.create_oval(*p(ox - 6.4, 20.6, ox + 6.4, 33.4), fill="#ffffff", outline="")
        for ox in (25.5, 38.5):
            lienzo.create_oval(*p(ox - 3.4, 24.1, ox + 3.4, 30.9), fill=c("#1a1a1a"), outline="")
        lienzo.create_polygon(p(32, 33, 28.6, 37.2, 32, 42, 35.4, 37.2), fill=c("#e07b24"), outline="")
        for y_linea in (46, 51):
            lienzo.create_line(*p(25, y_linea, 32, y_linea + 3, 39, y_linea), smooth=True,
                               fill=c("#6a6a6a"), width=max(1, 1.6 * e))


class BarraFlujo(tk.Canvas):
    """Cinco tarjetas unidas por flechas: Python → Scala → Python → Prolog → Python."""

    def __init__(self, padre, fondo: str = "#ffffff"):
        self.k = escala(padre)
        super().__init__(padre, height=int(112 * self.k), bg=fondo, highlightthickness=0)
        self.estados = ["pendiente"] * len(PASOS)
        self.textos = [""] * len(PASOS)
        self.bind("<Configure>", lambda e: self.dibujar())

    # ---------------------------------------------------------------- estado
    def pintar(self, actual: int, milisegundos: list[int] | None = None) -> None:
        """actual = paso en curso (1..5); 0 = reiniciar; 6 = todo terminado."""
        for i in range(len(PASOS)):
            n = i + 1
            self.estados[i] = "hecho" if n < actual else "activo" if n == actual else "pendiente"
            if n < actual:
                ms = milisegundos[i] if milisegundos and i < len(milisegundos) else 0
                self.textos[i] = f"{ms} ms" if ms else "listo"
            else:
                self.textos[i] = "en curso…" if n == actual else ""
        self.dibujar()

    def fallo(self, paso: int) -> None:
        """Marca en rojo el paso donde se detuvo la consulta."""
        if 1 <= paso <= len(PASOS):
            self.estados[paso - 1] = "error"
            self.textos[paso - 1] = "detenido"
        self.dibujar()

    # ---------------------------------------------------------------- dibujo
    def dibujar(self) -> None:
        self.delete("all")
        k = self.k
        ancho, alto = self.winfo_width(), int(self["height"])
        if ancho < 50:
            return
        n = len(PASOS)
        hueco = 26 * k
        tarjeta = (ancho - 4 - hueco * (n - 1)) / n
        for i, (lenguaje, verbo) in enumerate(PASOS):
            x0 = 2 + i * (tarjeta + hueco)
            if i:
                hecho = self.estados[i - 1] == "hecho"
                self.create_line(x0 - hueco + 3 * k, alto / 2, x0 - 3 * k, alto / 2,
                                 fill="#7cb987" if hecho else "#d6ccc0", width=2.5 * k, arrow="last",
                                 arrowshape=(8 * k, 9 * k, 4 * k), dash=() if hecho else (3, 3))
            self._tarjeta(i, x0, 4 * k, x0 + tarjeta, alto - 3 * k, lenguaje, verbo)

    def _tarjeta(self, i, x0, y0, x1, y1, lenguaje, verbo) -> None:
        k = self.k
        estado = self.estados[i]
        fondo, borde, texto, insignia = ESTADOS[estado]
        rectangulo(self, x0, y0, x1, y1, 12 * k, fill=fondo, outline=borde,
                   width=(1 if estado == "pendiente" else 2) * k)

        # Insignia: numero del paso, o ✓ / ✕ al terminar.
        marca = {"hecho": "✓", "error": "✕"}.get(estado, str(i + 1))
        r = 10 * k
        self.create_oval(x0 + 7 * k, y0 + 7 * k, x0 + 7 * k + 2 * r, y0 + 7 * k + 2 * r, fill=insignia, outline="")
        self.create_text(x0 + 7 * k + r, y0 + 7 * k + r, text=marca, fill="#ffffff", font=("Segoe UI Semibold", 9))

        # Logo del lenguaje en lugar de su nombre.
        lado = min(52 * k, (y1 - y0) - 44 * k)
        cx = (x0 + x1) / 2
        dibujar_logo(self, lenguaje, cx - lado / 2, y0 + 4 * k, lado, gris=(estado == "pendiente"))

        self.create_text(cx, y1 - 25 * k, text=verbo, fill=texto, font=("Segoe UI Semibold", 10))
        if self.textos[i]:
            self.create_text(cx, y1 - 10 * k, text=self.textos[i], fill=texto, font=("Segoe UI", 8))


def insignias_lenguajes(padre, fondo: str, texto: str) -> tk.Canvas:
    """Fila «[logo] integra  [logo] procesa  [logo] infiere» para la cabecera."""
    k = escala(padre)
    lado = 26 * k
    lienzo = tk.Canvas(padre, height=int(lado + 8 * k), bg=fondo, highlightthickness=0)
    x = 2
    for lenguaje, verbo in (("python", "integra"), ("scala", "procesa"), ("prolog", "infiere")):
        dibujar_logo(lienzo, lenguaje, x, 4 * k, lado)
        t = lienzo.create_text(x + lado + 6 * k, 4 * k + lado / 2, text=verbo, anchor="w",
                               fill=texto, font=("Segoe UI", 10))
        x = lienzo.bbox(t)[2] + 22 * k
    lienzo.configure(width=int(x))
    return lienzo
