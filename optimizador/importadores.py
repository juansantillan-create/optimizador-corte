"""Importar piezas: pegar desde Excel, CSV, XLSX y la planilla de la Interfaz de Metrix (.xls).

Todos devuelven lo mismo: `Importacion(piezas, columnas, avisos)`, donde `piezas` es la lista de
renglones en el formato de la entrada de `optimizar()` (ver `docs/API.md`). La interfaz muestra una
vista previa con las columnas detectadas y los avisos **antes** de aceptar.

Columnas: se detectan por encabezado (material, cantidad, ancho, largo, descripción, ítem, clase,
rota). Si no hay encabezado, se toman por posición: material, cantidad, ancho, largo, descripción.
Nunca se inventa: lo que no se entiende queda como aviso y el renglón no se importa.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class Importacion:
    piezas: list[dict] = field(default_factory=list)
    columnas: dict[str, str] = field(default_factory=dict)  # campo -> de dónde salió
    avisos: list[str] = field(default_factory=list)

    def a_dict(self) -> dict:
        return {"piezas": self.piezas, "columnas": self.columnas, "avisos": self.avisos}


SINONIMOS = {
    "item": ["item", "items", "nro", "numero", "n", "renglon", "linea", "pos", "posicion"],
    "material": ["material", "vidrio", "codigo", "cod", "articulo", "art", "producto", "vidrio1"],
    "cantidad": ["cantidad", "cant", "cantid", "q", "unidades", "piezas", "pzas", "ctd"],
    "ancho": ["ancho", "base", "a", "anch"],
    "largo": ["largo", "alto", "altura", "h", "l", "larg"],
    "descripcion": ["descripcion", "detalle", "obs", "observaciones", "observacion", "nota", "notas",
                    "referencia", "ref", "ubicacion"],
    "clase": ["clase", "proceso", "terminacion"],
    "rota": ["rota", "gira", "rotacion", "girar", "rotar"],
}
POSICIONES = ["material", "cantidad", "ancho", "largo", "descripcion"]


def _norm(texto) -> str:
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", t.lower())


def numero_mm(valor) -> float | None:
    """'1200' -> 1200; '1.200' -> 1200 (miles); '1200,5' -> 1200.5; '' -> None."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    t = str(valor).strip().replace(" ", "").replace("mm", "")
    if not t:
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    elif "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _detectar_encabezado(fila: list) -> dict[str, int] | None:
    mapa: dict[str, int] = {}
    for i, celda in enumerate(fila):
        n = _norm(celda)
        if not n:
            continue
        for campo, nombres in SINONIMOS.items():
            if campo not in mapa and n in nombres:
                mapa[campo] = i
                break
    # Es encabezado si trae al menos ancho y largo y otra columna conocida.
    if "ancho" in mapa and "largo" in mapa and len(mapa) >= 3:
        return mapa
    return None


def desde_filas(filas: list[list], origen: str = "tabla") -> Importacion:
    """Filas (listas de celdas) -> piezas, detectando columnas."""
    imp = Importacion()
    filas = [f for f in filas if any(str(c).strip() for c in f if c is not None)]
    if not filas:
        imp.avisos.append("no hay datos")
        return imp
    mapa = _detectar_encabezado(filas[0])
    primera = 2 if mapa is not None else 1
    if mapa is not None:
        datos = filas[1:]
        imp.columnas = {campo: f"columna {i + 1} ({filas[0][i]})" for campo, i in sorted(mapa.items(), key=lambda x: x[1])}
    else:
        datos = filas
        mapa = {campo: i for i, campo in enumerate(POSICIONES)}
        imp.columnas = {campo: f"columna {i + 1} (por posición)" for campo, i in mapa.items()}
        imp.avisos.append("no se encontró encabezado: se toman las columnas por posición "
                          "(material, cantidad, ancho, largo, descripción)")
    for n, fila in enumerate(datos, start=primera):
        def celda(campo):
            i = mapa.get(campo)
            return fila[i] if i is not None and i < len(fila) else None
        material = str(celda("material") or "").strip().upper()
        cantidad, ancho, largo = numero_mm(celda("cantidad")), numero_mm(celda("ancho")), numero_mm(celda("largo"))
        if cantidad is None and "cantidad" not in mapa:
            cantidad = 1
        problemas = []
        if not material:
            problemas.append("sin material")
        if cantidad is None or ancho is None or largo is None:
            problemas.append("cantidad, ancho o largo vacío o no numérico")
        if problemas:
            imp.avisos.append(f"{origen} fila {n}: {', '.join(problemas)}; no se importa")
            continue
        pieza = {"item": str(celda("item") or "").strip() or str(len(imp.piezas) + 1),
                 "material": material, "cantidad": cantidad, "ancho": ancho, "largo": largo}
        for campo in ("cantidad", "ancho", "largo"):
            if pieza[campo] != int(pieza[campo]):
                imp.avisos.append(f"{origen} fila {n}: {campo} {pieza[campo]:g} no es entero (se redondea al calcular)")
            else:
                pieza[campo] = int(pieza[campo])
        if celda("descripcion"):
            pieza["descripcion"] = str(celda("descripcion")).strip()
        if celda("clase"):
            pieza["clase"] = str(celda("clase")).strip()
        if celda("rota") not in (None, ""):
            pieza["rota"] = _norm(celda("rota")) in ("si", "s", "1", "x", "true", "verdadero")
        imp.piezas.append(pieza)
    return imp


def desde_texto(texto: str) -> Importacion:
    """Lo que se copia de Excel y se pega: columnas separadas por tabulación (o ';')."""
    lineas = [l for l in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n") if l.strip()]
    if not lineas:
        return Importacion(avisos=["no hay nada pegado"])
    sep = "\t" if any("\t" in l for l in lineas) else (";" if any(";" in l for l in lineas) else None)
    if sep is None:
        # Separado por espacios: las primeras 4 columnas son una palabra cada una; el resto es la
        # descripción.
        filas = []
        for l in lineas:
            partes = l.split()
            filas.append(partes[:4] + [" ".join(partes[4:])] if len(partes) > 5 else partes)
    else:
        filas = [l.split(sep) for l in lineas]
    return desde_filas(filas, "pegado")


def desde_csv(datos: bytes) -> Importacion:
    for codificacion in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            texto = datos.decode(codificacion)
            break
        except UnicodeDecodeError:
            continue
    muestra = texto[:2000]
    sep = max([";", ",", "\t"], key=muestra.count)
    filas = list(csv.reader(io.StringIO(texto), delimiter=sep))
    return desde_filas(filas, "CSV")


def desde_xlsx(datos: bytes) -> Importacion:
    import openpyxl

    libro = openpyxl.load_workbook(io.BytesIO(datos), data_only=True, read_only=True)
    hoja = libro.worksheets[0]
    filas = [list(f) for f in hoja.iter_rows(values_only=True)]
    imp = desde_filas(filas, f"XLSX hoja '{hoja.title}'")
    if len(libro.worksheets) > 1:
        imp.avisos.append(f"el archivo tiene {len(libro.worksheets)} hojas: se leyó solo la primera ({hoja.title})")
    return imp


# ----------------------------------------------------------- Interfaz de Metrix
# Columnas de la planilla de la Interfaz (A..P). Las del brief §9 son seguras (TIPO, VIDRIO1,
# CAMARA, VIDRIO2, ANCHO, LARGO, …, CLASE, CLASE CARA1, CLASE CARA2, OC); la de CANTIDAD (G) es
# SUPUESTA hasta ver una planilla real (pregunta 13). Si la planilla trae encabezados, mandan ellos.
INTERFAZ_POSICIONES = {"tipo": 0, "vidrio1": 1, "camara": 2, "vidrio2": 3, "ancho": 4, "largo": 5,
                       "cantidad": 6, "clase": 12, "clase_cara1": 13, "clase_cara2": 14, "oc": 15}
INTERFAZ_SINONIMOS = {"tipo": ["tipo"], "vidrio1": ["vidrio1", "vidrio"], "camara": ["camara"],
                      "vidrio2": ["vidrio2"], "ancho": ["ancho"], "largo": ["largo", "alto"],
                      "cantidad": ["cantidad", "cant"], "clase": ["clase"],
                      "clase_cara1": ["clasecara1"], "clase_cara2": ["clasecara2"], "oc": ["oc"],
                      "obs": ["obs", "observaciones"], "item": ["item", "nro"]}


def desde_interfaz(datos: bytes, nombre: str = "") -> Importacion:
    """Planilla de la Interfaz de Metrix (.xls Excel 97, solo Hoja1; también acepta .xlsx).

    - Un DVH son 2 vidrios: una pieza de VIDRIO1 y otra de VIDRIO2.
    - Los herrajes (TIPO = DIST con LARGO = 1) se ignoran, con aviso.
    - La clase con "PR" lleva pulido recto (+3 mm al calcular).
    """
    filas = _leer_excel(datos, nombre)
    imp = Importacion()
    if not filas:
        imp.avisos.append("la planilla está vacía")
        return imp
    mapa = {}
    for i, celda in enumerate(filas[0]):
        n = _norm(celda)
        for campo, nombres in INTERFAZ_SINONIMOS.items():
            if campo not in mapa and n in nombres:
                mapa[campo] = i
    if "ancho" in mapa and "largo" in mapa and ("vidrio1" in mapa or "tipo" in mapa):
        datos_filas = filas[1:]
        primera = 2
        imp.columnas = {c: f"columna {chr(65 + i)} ({filas[0][i]})" for c, i in sorted(mapa.items(), key=lambda x: x[1])}
    else:
        mapa = dict(INTERFAZ_POSICIONES)
        datos_filas = filas
        primera = 1
        imp.columnas = {c: f"columna {chr(65 + i)}" + (" (SUPUESTA)" if c == "cantidad" else "")
                        for c, i in sorted(mapa.items(), key=lambda x: x[1])}
        imp.avisos.append("planilla sin encabezados: se usan las posiciones de la Interfaz; la de la "
                          "CANTIDAD (columna G) es supuesta hasta confirmarla (pregunta 13)")
    herrajes = 0
    for n, fila in enumerate(datos_filas, start=primera):
        def celda(campo):
            i = mapa.get(campo)
            return fila[i] if i is not None and i < len(fila) else None
        tipo = str(celda("tipo") or "").strip().upper()
        v1 = str(celda("vidrio1") or "").strip().upper()
        v2 = str(celda("vidrio2") or "").strip().upper()
        ancho, largo = numero_mm(celda("ancho")), numero_mm(celda("largo"))
        cantidad = numero_mm(celda("cantidad"))
        if not v1 and ancho is None:
            continue  # renglón vacío
        if tipo == "DIST" and largo == 1:
            herrajes += 1
            continue
        if cantidad is None:
            cantidad = 1
            imp.avisos.append(f"Interfaz fila {n}: sin cantidad, se toma 1")
        if not v1 or ancho is None or largo is None:
            imp.avisos.append(f"Interfaz fila {n}: falta el vidrio o la medida; no se importa")
            continue
        clase = str(celda("clase") or "").strip()
        item = str(celda("item") or n)
        es_dvh = "DVH" in tipo or bool(str(celda("camara") or "").strip()) or bool(v2)
        vidrios = [(v1, str(celda("clase_cara1") or "").strip() or clase)]
        if es_dvh:
            if v2:
                vidrios.append((v2, str(celda("clase_cara2") or "").strip() or clase))
            else:
                imp.avisos.append(f"Interfaz fila {n}: es DVH pero no tiene VIDRIO2; se importa solo VIDRIO1")
        for k, (vidrio, cl) in enumerate(vidrios, start=1):
            pieza = {"item": f"{item}" + (f"-{k}" if len(vidrios) > 1 else ""), "material": vidrio,
                     "cantidad": int(cantidad), "ancho": int(round(ancho)), "largo": int(round(largo)),
                     "clase": cl, "origen": {"interfaz_fila": n}}
            desc = []
            if es_dvh:
                desc.append(f"DVH vidrio {k}")
            if celda("oc"):
                desc.append(f"OC {celda('oc')}")
            if desc:
                pieza["descripcion"] = ", ".join(desc)
            imp.piezas.append(pieza)
    if herrajes:
        imp.avisos.append(f"se ignoraron {herrajes} renglón(es) de herrajes (TIPO = DIST, LARGO = 1)")
    return imp


def _leer_excel(datos: bytes, nombre: str) -> list[list]:
    if datos[:4] == b"PK\x03\x04" or nombre.lower().endswith((".xlsx", ".xlsm")):
        import openpyxl
        libro = openpyxl.load_workbook(io.BytesIO(datos), data_only=True, read_only=True)
        return [list(f) for f in libro.worksheets[0].iter_rows(values_only=True)]
    import xlrd
    libro = xlrd.open_workbook(file_contents=datos)
    hoja = libro.sheet_by_index(0)
    return [hoja.row_values(i) for i in range(hoja.nrows)]


def importar_archivo(datos: bytes, nombre: str, interfaz: bool | None = None) -> Importacion:
    """Elige el lector por la extensión. Un .xls se toma como planilla de la Interfaz."""
    n = nombre.lower()
    if interfaz or (interfaz is None and n.endswith(".xls")):
        return desde_interfaz(datos, nombre)
    if n.endswith((".xlsx", ".xlsm")):
        return desde_xlsx(datos)
    return desde_csv(datos)
