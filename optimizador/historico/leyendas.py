"""Leer la "leyenda" de Corte Certo que quedó en las observaciones del presupuesto.

Formato real (Juan, 25/10/2026; ver `docs/FORMATO_LEYENDAS.md`), una línea por material:

    LISTA 1
    4+4 NLIGHT: 88 HOJAS - 91% ******* L.DIST -10%
    3+3 LOWE: 105 HOJAS - 72% ******* L.DIST -10%
    4+4 LOWE_ 22 HOJAS - 64%******* L.DIST -10%

El lector es tolerante (mayúsculas, espacios, ":" o "_" o "-", "HOJA/HOJAS/PLANCHAS/CHAPAS",
coma decimal en el %), pero no adivina: lo que no matchea queda como "no leído", con el texto, para
contar la cobertura y mirar ejemplos.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

# <material> [:_-]? <n> HOJAS [-–] <p> %   (después puede venir cualquier cosa)
_LINEA = re.compile(
    r"^\s*(?P<material>[A-Z0-9][A-Z0-9 .+/\-]*?)\s*[:_\-=]?\s*"
    r"(?P<hojas>\d{1,4})\s*(?P<palabra>HOJAS?|PLANCHAS?|CHAPAS?|HJS?\.?)\s*"
    r"[-–—,;:]?\s*(?:APROV\.?\s*)?(?P<aprov>\d{1,3}(?:[.,]\d{1,2})?)\s*%"
    r"(?P<resto>.*)$",
    re.IGNORECASE)
# Sin material: "88 HOJAS - 91%"
_SOLO_NUMEROS = re.compile(
    r"^\s*(?P<hojas>\d{1,4})\s*(?:HOJAS?|PLANCHAS?|CHAPAS?)\s*[-–—,;:]?\s*(?P<aprov>\d{1,3}(?:[.,]\d{1,2})?)\s*%",
    re.IGNORECASE)
_PISTAS = re.compile(r"HOJA|PLANCHA|CHAPA|APROV|LAYOUT|MONTAJE|\d\s*%", re.IGNORECASE)
_ENCABEZADO_LISTA = re.compile(r"^\s*LISTA\s*\w+\s*$", re.IGNORECASE)


@dataclass
class LineaLeyenda:
    material: str  # tal cual, normalizado a mayúsculas y espacios simples ("4+4 NLIGHT")
    hojas: int
    aprovechamiento: float  # en %
    cotizacion: str  # lo que viene después (lista y descuento), sin asteriscos
    texto: str  # la línea original


@dataclass
class Leyenda:
    lineas: list[LineaLeyenda] = field(default_factory=list)
    lista: str = ""  # "LISTA 1", si aparece
    no_leidas: list[str] = field(default_factory=list)  # líneas con pinta de leyenda que no se entendieron
    columna: str = ""  # de qué columna salió

    @property
    def tiene_pinta(self) -> bool:
        return bool(self.lineas or self.no_leidas)

    def a_dict(self) -> dict:
        return asdict(self)


def leer(texto: str, columna: str = "") -> Leyenda:
    leyenda = Leyenda(columna=columna)
    if not texto:
        return leyenda
    for linea in re.split(r"\r\n|\r|\n|\\n", str(texto)):
        limpia = linea.strip()
        if not limpia:
            continue
        if _ENCABEZADO_LISTA.match(limpia):
            leyenda.lista = re.sub(r"\s+", " ", limpia.upper())
            continue
        m = _LINEA.match(limpia)
        if m:
            material = re.sub(r"\s+", " ", m.group("material").upper()).strip(" .-_:")
            resto = m.group("resto").replace("*", " ")
            leyenda.lineas.append(LineaLeyenda(
                material=material, hojas=int(m.group("hojas")),
                aprovechamiento=float(m.group("aprov").replace(",", ".")),
                cotizacion=re.sub(r"\s+", " ", resto).strip(), texto=limpia))
            continue
        m = _SOLO_NUMEROS.match(limpia)
        if m:
            leyenda.lineas.append(LineaLeyenda(material="", hojas=int(m.group("hojas")),
                                               aprovechamiento=float(m.group("aprov").replace(",", ".")),
                                               cotizacion="", texto=limpia))
            continue
        if _PISTAS.search(limpia):
            leyenda.no_leidas.append(limpia)
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
