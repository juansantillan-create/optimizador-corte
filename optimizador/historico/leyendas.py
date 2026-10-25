"""Leer la "leyenda" de Corte Certo que quedó en las observaciones del presupuesto.

Formato real (Juan, 25/10/2026; ver `docs/FORMATO_LEYENDAS.md`), una línea por material:

    LISTA 1
    4+4 NLIGHT: 88 HOJAS - 91% ******* L.DIST -10%
    3+3 LOWE: 105 HOJAS - 72% ******* L.DIST -10%
    4+4 LOWE_ 22 HOJAS - 64%******* L.DIST -10%

El lector es tolerante (mayúsculas, espacios, ":" o "_" o "-", "HOJA/HOJAS/PLANCHAS/CHAPAS",
coma decimal en el %), pero no adivina:
- una línea puede traer dos materiales ("… 91% / 3+3 LOWE: 105 HOJAS - 72%", o separados con
  asteriscos): se leen los dos;
- lo que tiene pinta de leyenda y no se entiende queda en `no_leidas` (aunque otras líneas del
  mismo presupuesto se hayan leído), para contar la cobertura y mirar ejemplos;
- si después del % dice "desperdicio" o "pérdida", no es aprovechamiento: no se lee;
- "TOTAL", "SE USAN", "DÓLAR"… no son materiales: van a `ignoradas`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field

_NUM_HOJAS = r"(?<![\d.,])(?P<hojas>\d{1,4})(?![\d.,]\d)"
_PALABRA = r"(?P<palabra>HOJAS?|PLANCHAS?|CHAPAS?|HJS?\.?)"
_APROV = r"(?P<aprov>\d{1,3}(?:[.,]\d{1,2})?)\s*%"
# <material> [:_-]? <n> HOJAS [-–] <p> %   (después puede venir cualquier cosa)
_LINEA = re.compile(
    r"^\s*(?P<material>[A-Z0-9][A-Z0-9 .+/\-]*?)\s*[:_\-=]?\s*" + _NUM_HOJAS + r"\s*" + _PALABRA +
    r"\s*[-–—,;:(]?\s*(?:APROV\.?\s*)?" + _APROV + r"\s*\)?(?P<resto>.*)$")
# Sin material: "88 HOJAS - 91%"
_SOLO_NUMEROS = re.compile(r"^\s*" + _NUM_HOJAS + r"\s*" + _PALABRA + r"\s*[-–—,;:(]?\s*" + _APROV +
                           r"\s*\)?(?P<resto>.*)$")
_FUERTES = re.compile(r"HOJA|PLANCHA|CHAPA|APROV|LAYOUT|MONTAJE")
_PISTAS = re.compile(_FUERTES.pattern + r"|\d\s*%")
_ENCABEZADO_LISTA = re.compile(r"^\s*LISTA\s*\w+\b.*$")
_PREFIJO_LISTA = re.compile(r"^(?P<lista>LISTA\s+\S+)\s+(?=\d)")
_NO_MATERIAL = re.compile(r"^(TOTAL|TOTALES|LISTA|DOLAR|COTIZ|SE USAN|USAN|SON|QUEDAN|APROX)\b")
_PERDIDA = re.compile(r"^\s*(DE\s+)?(DESPERDICIO|PERDIDA|DESP\b|SOBRANTE)")
# Separadores entre dos materiales en una misma línea: " / " (o "/" antes de un número), "***" y "|".
# Un "/" pegado entre letras ("NL/LOWE") es parte del nombre y no separa.
_SEPARAR = re.compile(r"\s+/\s+|/(?=\s*\d)|\s*\*{3,}\s*|\s*\|\s*")


@dataclass
class LineaLeyenda:
    material: str  # tal cual, normalizado a mayúsculas y espacios simples ("4+4 NLIGHT")
    hojas: int
    aprovechamiento: float  # en %
    decimales: int  # cuántos decimales traía el % (para el control)
    cotizacion: str  # lo que viene después (lista y descuento), sin asteriscos
    texto: str  # la línea original


@dataclass
class Leyenda:
    lineas: list[LineaLeyenda] = field(default_factory=list)
    lista: str = ""  # "LISTA 1", si aparece
    no_leidas: list[str] = field(default_factory=list)  # con pinta de leyenda pero no se entendieron
    ignoradas: list[str] = field(default_factory=list)  # se entendieron y no son materiales (TOTAL…)
    columna: str = ""  # de qué columna salió

    @property
    def tiene_pinta(self) -> bool:
        return bool(self.lineas or self.no_leidas)

    def a_dict(self) -> dict:
        return asdict(self)


def _normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[ \t]+", " ", t.upper()).strip()


def _leer_segmento(segmento: str, original: str, leyenda: Leyenda) -> tuple[list[LineaLeyenda], str]:
    """Las líneas de material de un pedazo de texto y qué pasó con lo demás: "" (nada raro),
    "no_leida" (tiene pinta y no se entiende) o "ignorada" (no es un material, como TOTAL)."""
    m = _LINEA.match(segmento) or _SOLO_NUMEROS.match(segmento)
    if not m:
        return [], "no_leida" if _FUERTES.search(segmento) else ""
    resto = m.group("resto")
    if _PERDIDA.match(resto):
        return [], "no_leida"  # el % es de desperdicio, no de aprovechamiento
    material = ""
    if "material" in m.groupdict() and m.group("material"):
        material = re.sub(r"\s+", " ", m.group("material")).strip(" .-_:")
        prefijo = _PREFIJO_LISTA.match(material)
        if prefijo:  # "LISTA 1 5 INC: …"
            leyenda.lista = leyenda.lista or prefijo.group("lista")
            material = material[prefijo.end():]
        if _NO_MATERIAL.match(material):
            return [], "ignorada"
    aprov = m.group("aprov").replace(",", ".")
    linea = LineaLeyenda(material=material, hojas=int(m.group("hojas")), aprovechamiento=float(aprov),
                         decimales=len(aprov.split(".")[1]) if "." in aprov else 0,
                         cotizacion=re.sub(r"\s+", " ", resto.replace("*", " ")).strip(), texto=original)
    if _FUERTES.search(resto):
        # Otro material pegado después del %, sin separador.
        mas, estado = _leer_segmento(resto.strip(" -,;"), original, leyenda)
        if mas:
            linea.cotizacion = ""
            return [linea] + mas, estado
        return [linea], "no_leida"
    return [linea], ""


def leer(texto: str, columna: str = "") -> Leyenda:
    leyenda = Leyenda(columna=columna)
    if not texto:
        return leyenda
    for linea in re.split(r"\r\n|\r|\n|\\n", str(texto)):
        original = linea.strip()
        limpia = _normalizar(original)
        if not limpia:
            continue
        leidas_en_linea = 0
        estados = set()
        for segmento in _SEPARAR.split(limpia):
            if not segmento:
                continue
            if _ENCABEZADO_LISTA.match(segmento) and not _LINEA.match(segmento):
                leyenda.lista = leyenda.lista or segmento
                continue
            leidas, estado = _leer_segmento(segmento, original, leyenda)
            if leidas:
                leyenda.lineas.extend(leidas)
                leidas_en_linea += len(leidas)
            elif leidas_en_linea and not estado and not _FUERTES.search(segmento):
                # Lo que viene después de los asteriscos: la cotización del material anterior.
                anterior = leyenda.lineas[-1]
                anterior.cotizacion = (anterior.cotizacion + " " + segmento).strip()
            elif not leidas_en_linea and not estado and _PISTAS.search(segmento):
                estado = "no_leida"
            if estado:
                estados.add(estado)
        if "no_leida" in estados:
            leyenda.no_leidas.append(original)
        elif "ignorada" in estados:
            leyenda.ignoradas.append(original)
    return leyenda


def buscar(fila: dict, columnas_preferidas=("observaciones", "notas_causa", "tv_descrip", "notas")) -> Leyenda:
    """Busca la leyenda en las columnas de texto de un presupuesto: primero las preferidas, después
    cualquier otra. Devuelve la primera que tenga líneas leídas (o la que tenga pinta)."""
    orden = [c for c in columnas_preferidas if c in fila] + \
            [c for c in fila if c not in columnas_preferidas and c not in ("numero", "fecha")]
    con_pinta = None
    for col in orden:
        ley = leer(fila.get(col) or "", col)
        if ley.lineas:
            return ley
        if ley.tiene_pinta and con_pinta is None:
            con_pinta = ley
    return con_pinta or Leyenda()
