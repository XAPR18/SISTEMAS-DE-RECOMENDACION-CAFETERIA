"use strict";
// Interfaz web del sistema experto. Solo habla con Python (API en /api/...).

const NUEVO = "__nuevo__";
const $ = (sel) => document.querySelector(sel);
const estado = { catalogo: null, resultado: null, seleccion: 0 };

// ------------------------------------------------------------------ utilidades
function esc(texto) {
  return String(texto ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const et = (codigo) => (estado.catalogo?.etiquetas?.[codigo]) || codigo;

function avisar(mensaje) {
  const aviso = $("#aviso");
  aviso.textContent = mensaje;
  aviso.hidden = false;
  clearTimeout(avisar.t);
  avisar.t = setTimeout(() => { aviso.hidden = true; }, 5000);
}

async function api(ruta, opciones) {
  const r = await fetch(ruta, opciones);
  let datos = null;
  try { datos = await r.json(); } catch { /* respuesta vacia */ }
  if (!r.ok) throw new Error(datos?.error || `Error ${r.status}`);
  return datos;
}

const espera = (ms) => new Promise((ok) => setTimeout(ok, ms));
const franjaDeHora = (h) => (h < 6 || h >= 19 ? "noche" : h < 12 ? "manana" : "tarde");

// Colores por sabor para las ilustraciones de productos sin foto
const TONOS = {
  dulce: ["#7a3f2e", "#c98b6b", "#f3d2bd"],
  amargo: ["#22160f", "#5a3c2a", "#c7a27c"],
  suave: ["#8d6e52", "#d9bf9f", "#fbf1e2"],
  citrico: ["#9b6a12", "#e9b949", "#fff1bf"],
};
const PUNTO = { dulce: "#c98b6b", amargo: "#5a3c2a", suave: "#d9bf9f", citrico: "#e9b949" };

// Ilustracion SVG para productos sin foto: taza humeante, vaso con hielo o plato.
function ilustracion(p, esBebida) {
  const [oscuro, medio, claro] = TONOS[p.sabor] || TONOS.suave;
  const id = "g" + Math.random().toString(36).slice(2, 8);
  let dibujo;
  if (!esBebida) {
    dibujo = `<ellipse cx="100" cy="104" rx="64" ry="14" fill="#fff" opacity=".9"/>
      <ellipse cx="100" cy="100" rx="46" ry="9" fill="${claro}"/>
      <path d="M62 98c4-26 22-38 38-38s34 12 38 38z" fill="${medio}"/>
      <path d="M76 82c8-8 16-10 24-10M88 92c6-6 14-8 22-8" stroke="${claro}" stroke-width="4" fill="none" stroke-linecap="round" opacity=".7"/>`;
  } else if (p.temperatura === "fria") {
    dibujo = `<path d="M74 34h52l-7 80H81z" fill="#fff" opacity=".35"/>
      <path d="M77 54h46l-5 58H82z" fill="${medio}"/>
      <rect x="86" y="58" width="13" height="13" rx="3" fill="#fff" opacity=".7" transform="rotate(-12 92 64)"/>
      <rect x="102" y="66" width="12" height="12" rx="3" fill="#fff" opacity=".6" transform="rotate(14 108 72)"/>
      <path d="M110 18l-6 52" stroke="${claro}" stroke-width="5" stroke-linecap="round"/>`;
  } else {
    dibujo = `<path d="M84 22c-6 8 6 12 0 20M100 18c-6 8 6 12 0 20M116 22c-6 8 6 12 0 20" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round" opacity=".55"/>
      <ellipse cx="100" cy="114" rx="56" ry="10" fill="#fff" opacity=".9"/>
      <path d="M66 54h68v30c0 18-14 28-34 28s-34-10-34-28z" fill="#fff"/>
      <path d="M134 62c18 0 18 26-2 26" stroke="#fff" stroke-width="7" fill="none"/>
      <ellipse cx="100" cy="56" rx="32" ry="6" fill="${medio}"/>`;
  }
  // "meet" mantiene el dibujo completo; el fondo se extiende mas alla del viewBox
  return `<svg viewBox="0 0 200 140" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${esc(p.nombre)}">
    <defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${oscuro}"/><stop offset="1" stop-color="${medio}"/></linearGradient></defs>
    <rect x="-400" y="-400" width="1000" height="940" fill="url(#${id})"/>
    <circle cx="170" cy="20" r="46" fill="#fff" opacity=".06"/><circle cx="20" cy="130" r="40" fill="#000" opacity=".08"/>
    ${dibujo}</svg>`;
}

function imagen(p, esBebida) {
  return p.foto
    ? `<img src="${esc(p.foto)}" alt="${esc(p.nombre)}" loading="lazy">`
    : ilustracion(p, esBebida);
}

function fotosOpcion(o) {
  const partes = [imagen(o.bebida, true)];
  if (o.acompanamiento) partes.push(imagen(o.acompanamiento, false));
  return `<div class="fotos">${partes.join("")}${o.acompanamiento ? '<span class="fotos__mas">+</span>' : ""}</div>`;
}

const estrellas = (n) => `<span class="estrellas" title="Puntaje ${n} de 5">${"★".repeat(n)}${"☆".repeat(Math.max(0, 5 - n))}</span>`;

// ------------------------------------------------------------------ formulario
function chips(contenedor, nombre, valores, texto, punto) {
  $(contenedor).innerHTML = valores.map((v, i) => `
    <label class="chip"><input type="radio" name="${nombre}" value="${esc(v)}" ${i === 0 ? "checked" : ""}>
      <span>${punto ? `<i style="background:${PUNTO[v]}"></i>` : ""}${esc(texto(v))}</span></label>`).join("");
}
const valor = (nombre) => document.querySelector(`input[name="${nombre}"]:checked`)?.value;
function marcar(nombre, v) {
  const el = document.querySelector(`input[name="${nombre}"][value="${v}"]`);
  if (el) el.checked = true;
}

function llenarPerfiles(clientes, seleccionado) {
  const sel = $("#perfil");
  sel.innerHTML = clientes.map((c) => `<option value="${esc(c.nombre)}">${esc(c.nombre)} · ${esc(et(c.sabor))}, ${esc(et(c.temperatura))}</option>`).join("")
    + `<option value="${NUEVO}">➕ Nuevo cliente</option>`;
  sel.value = seleccionado && clientes.some((c) => c.nombre === seleccionado) ? seleccionado : (clientes[0]?.nombre ?? NUEVO);
  perfilElegido();
}

function perfilElegido() {
  const nombre = $("#perfil").value;
  const cliente = estado.catalogo.clientes.find((c) => c.nombre === nombre);
  $("#campo-nombre").hidden = Boolean(cliente);
  if (cliente) {
    marcar("sabor", cliente.sabor);
    marcar("temperatura", cliente.temperatura);
    $("#guardar").checked = false;
  } else {
    $("#nombre").value = "";
    $("#guardar").checked = true;
    $("#nombre").focus();
  }
}

function prepararFormulario() {
  const o = estado.catalogo.opciones;
  chips("#sabores", "sabor", o.sabores, et, true);
  chips("#temperaturas", "temperatura", o.temperaturas, (t) => (t === "fria" ? "❄ " : "♨ ") + et(t));
  chips("#modos", "modo", ["combo", "sola"], (m) => (m === "combo" ? "Combo" : "Solo bebida"));
  const ahora = franjaDeHora(new Date().getHours());
  chips("#franjas", "franja", ["auto", ...o.franjas], (f) => (f === "auto" ? `Ahora (${et(ahora)})` : et(f)));
  $("#rapidos").innerHTML = ["10", "15", "20", "30"].map((m) => `<button type="button" class="rapido" data-monto="${m}">S/ ${m}</button>`).join("");
  $("#rapidos").addEventListener("click", (e) => {
    const m = e.target.dataset.monto;
    if (m) $("#presupuesto").value = `${m}.00`;
  });
  llenarPerfiles(estado.catalogo.clientes);
  $("#perfil").addEventListener("change", perfilElegido);
  $("#formulario").addEventListener("submit", recomendar);
}

// ------------------------------------------------------------------ flujo
const pasos = () => [...document.querySelectorAll(".paso")];
function pintarFlujo(actual) {
  pasos().forEach((p, i) => {
    p.classList.toggle("hecho", i + 1 < actual);
    p.classList.toggle("activo", i + 1 === actual);
    if (i + 1 >= actual) p.querySelector(".paso__ms").textContent = "";
  });
}
function tiemposFlujo(lista) {
  pasos().forEach((p, i) => {
    const paso = lista[i];
    p.querySelector(".paso__ms").textContent = paso ? (paso.ms ? `${paso.ms} ms` : "listo") : "";
    p.title = paso ? paso.descripcion : "";
  });
}

// ------------------------------------------------------------------ recomendar
async function recomendar(evento) {
  evento.preventDefault();
  const perfil = $("#perfil").value;
  const nuevo = perfil === NUEVO;
  const cuerpo = {
    nombre: nuevo ? $("#nombre").value : perfil,
    nuevo,
    sabor: valor("sabor"),
    temperatura: valor("temperatura"),
    presupuesto: $("#presupuesto").value,
    modo: valor("modo"),
    franja: valor("franja"),
    guardar: $("#guardar").checked,
  };
  if (nuevo && !cuerpo.nombre.trim()) { avisar("Escribe tu nombre para crear el perfil."); $("#nombre").focus(); return; }

  const boton = $("#boton");
  boton.disabled = true;
  boton.classList.add("cargando");
  const peticion = api("/api/recomendar", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) });

  // Animacion del recorrido mientras Python, Scala y Prolog trabajan
  let terminado = false;
  peticion.finally(() => { terminado = true; });
  for (const [paso, minimo] of [[1, 180], [2, 380], [3, 180], [4, 380]]) {
    pintarFlujo(paso);
    await espera(minimo);
  }
  while (!terminado) await espera(60);

  try {
    const r = await peticion;
    pintarFlujo(5);
    await espera(220);
    pintarFlujo(6);
    tiemposFlujo(r.pasos);
    estado.resultado = r;
    estado.seleccion = Math.max(0, r.opciones.findIndex((o) => o.destacada));
    estado.catalogo.clientes = r.clientes;
    if (cuerpo.guardar) llenarPerfiles(r.clientes, r.cliente);
    mostrarResultado();
  } catch (e) {
    pintarFlujo(0);
    avisar(e.message);
  } finally {
    boton.disabled = false;
    boton.classList.remove("cargando");
  }
}

function mostrarResultado() {
  const r = estado.resultado;
  const franja = `${r.franja_texto}${r.franja_automatica ? " (según la hora)" : ""}`;
  if (!r.opciones.length) {
    $("#salida").innerHTML = `<div class="tarjeta sin-opciones aparecer">
      <h2>Ninguna opción cumple todo tu pedido</h2>
      <p>Scala evaluó ${r.generadas} opciones y Prolog no encontró ninguna con tu sabor, en la franja de la ${esc(franja.toLowerCase())}, dentro de ${esc(r.presupuesto)} y del tipo de pedido elegido.</p>
      <p>No cambiamos tu sabor ni superamos tu presupuesto. Prueba con otra franja, un presupuesto mayor o «Solo bebida».</p></div>`;
    return;
  }
  const alternativas = r.opciones[0].tipo === "alternativa";
  const o = r.opciones[estado.seleccion];
  const motivos = o.explicacion.map((f) => {
    let clase = "", texto = f;
    if (f.startsWith("ALTERNATIVA: ")) { clase = "alerta"; texto = f.slice(13); }
    if (f.startsWith("DESTACADA: ")) { clase = "estrella"; texto = "Destacada: " + f.slice(11); }
    return `<li class="${clase}">${esc(texto)}</li>`;
  }).join("");

  $("#salida").innerHTML = `
    <div class="resumen aparecer">
      <h2>${r.opciones.length} ${alternativas ? (r.opciones.length === 1 ? "alternativa" : "alternativas") : (r.opciones.length === 1 ? "opción exacta" : "opciones exactas")} para ${esc(r.cliente)}</h2>
      <p>${r.generadas} evaluadas por Scala · Franja ${esc(franja)} · Presupuesto ${esc(r.presupuesto)}</p>
    </div>
    <article class="tarjeta destacada aparecer">
      ${fotosOpcion(o)}
      <div class="destacada__info">
        <span class="sello">${o.destacada ? "★ Destacada por Prolog" : `Opción ${estado.seleccion + 1} de ${r.opciones.length}`}</span>
        <h3>${esc(o.nombre)}</h3>
        <div class="precio">${esc(o.total)}<small>te sobran ${esc(o.saldo)}</small></div>
        <div class="insignias">
          <span class="insignia insignia--${o.tipo}">${o.tipo === "exacta" ? "Coincidencia exacta" : "Otra temperatura"}</span>
          ${o.acompanamiento ? `<span class="insignia">Maridaje: ${esc(o.maridaje_texto)}</span>` : ""}
          <span class="insignia">${estrellas(o.puntaje)}</span>
        </div>
        <ul class="motivos">${motivos}</ul>
      </div>
    </article>
    ${r.opciones.length > 1 ? `<h3 class="subtitulo">Todas las opciones · de menor a mayor precio</h3>
    <div class="rejilla aparecer">${r.opciones.map((x, i) => `
      <button type="button" class="tarjeta opcion ${i === estado.seleccion ? "seleccionada" : ""}" data-indice="${i}">
        ${fotosOpcion(x)}
        <div class="opcion__cuerpo">
          <span class="opcion__nombre">${x.destacada ? "★ " : ""}${esc(x.nombre)}</span>
          <div class="insignias"><span class="insignia insignia--${x.tipo}">${x.tipo === "exacta" ? "Exacta" : "Otra temperatura"}</span>
            ${x.acompanamiento ? `<span class="insignia">${esc(x.maridaje_texto)}</span>` : ""}</div>
          <div class="opcion__pie"><span class="opcion__precio">${esc(x.total)}</span>${estrellas(x.puntaje)}</div>
        </div>
      </button>`).join("")}</div>` : ""}`;

  document.querySelectorAll(".opcion").forEach((tarjeta) => tarjeta.addEventListener("click", () => {
    estado.seleccion = Number(tarjeta.dataset.indice);
    mostrarResultado();
    $(".destacada").scrollIntoView({ behavior: "smooth", block: "nearest" });
  }));
}

// ------------------------------------------------------------------ carta
function mostrarCarta(filtro = "todo") {
  const c = estado.catalogo;
  const filtros = [["todo", "Todo"], ["bebida", "Bebidas"], ["acompanamiento", "Acompañamientos"], ...c.opciones.sabores.map((s) => [s, et(s)])];
  $("#filtros-carta").innerHTML = filtros.map(([v, t]) => `<button class="filtro ${v === filtro ? "activo" : ""}" data-filtro="${v}">${esc(t)}</button>`).join("");
  const productos = [
    ...c.bebidas.map((b) => ({ ...b, esBebida: true })),
    ...c.acompanamientos.map((a) => ({ ...a, esBebida: false })),
  ].filter((p) => filtro === "todo" || (filtro === "bebida" && p.esBebida) || (filtro === "acompanamiento" && !p.esBebida) || p.sabor === filtro);
  $("#carta").innerHTML = productos.map((p) => `
    <article class="tarjeta producto aparecer">
      <div class="producto__foto">${imagen(p, p.esBebida)}</div>
      <div class="producto__cuerpo">
        <div class="producto__fila"><h3>${esc(p.nombre)}</h3><span class="opcion__precio">${esc(p.precio)}</span></div>
        <div class="insignias">
          <span class="insignia"><span style="color:${PUNTO[p.sabor]}">●</span> ${esc(et(p.sabor))}</span>
          ${p.esBebida ? `<span class="insignia">${p.temperatura === "fria" ? "❄" : "♨"} ${esc(et(p.temperatura))}</span>` : '<span class="insignia">Acompañamiento</span>'}
        </div>
        ${p.esBebida ? `<p class="producto__detalle"><b>Horario:</b> ${p.franjas.map((f) => esc(et(f))).join(", ")}</p>
        <p class="producto__detalle"><b>Combina con:</b> ${p.acompanamientos.map(esc).join(", ")}</p>` : ""}
      </div>
    </article>`).join("");
}

// ------------------------------------------------------------------ historial
async function mostrarHistorial() {
  try {
    const filas = await api("/api/historial");
    $("#historial").innerHTML = filas.length ? filas.map((h) => `<tr>
      <td>${esc((h.fecha || "").replace("T", " "))}</td><td>${esc(h.cliente)}</td>
      <td>${h.modo === "combo" ? "Combo" : "Solo bebida"}</td><td>${esc(et(h.franja))}</td>
      <td>${esc(h.presupuesto)}</td><td>${esc(h.total_opciones)}</td><td>${esc(h.destacada || "Sin opciones")}</td></tr>`).join("")
      : `<tr><td colspan="7">Todavía no hay consultas.</td></tr>`;
  } catch (e) { avisar(e.message); }
}

// ------------------------------------------------------------------ inicio
function cambiarVista(vista) {
  document.querySelectorAll(".pestana").forEach((b) => b.classList.toggle("activa", b.dataset.vista === vista));
  document.querySelectorAll(".vista").forEach((s) => { s.hidden = s.id !== `vista-${vista}`; });
  if (vista === "historial") mostrarHistorial();
}

async function iniciar() {
  try {
    estado.catalogo = await api("/api/catalogo");
  } catch (e) {
    avisar("No se pudo cargar el catálogo: " + e.message);
    return;
  }
  prepararFormulario();
  mostrarCarta();
  $("#filtros-carta").addEventListener("click", (e) => { if (e.target.dataset.filtro) mostrarCarta(e.target.dataset.filtro); });
  document.querySelectorAll(".pestana").forEach((b) => b.addEventListener("click", () => cambiarVista(b.dataset.vista)));
}

iniciar();
