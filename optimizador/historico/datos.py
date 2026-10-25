"""Leer los casos históricos: el zip `casos_historicos_AAAA-MM-DD.zip` o una carpeta con los mismos
archivos (ver `docs/CONTRATO_DATOS.md`, versión 2). CSV con `;`, UTF-8, punto decimal.

Verifica que estén los archivos y las columnas del contrato y anota las diferencias en vez de
fallar: la sesión se adapta (regla: nunca inventar en silencio).
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

CONTRATO = {
    "presupuestos.csv": ["numero", "fecha", "estado_pres", "tipopresup"],
    "renglones.csv": ["numero", "v_codart", "familia", "art1", "art2", "art3", "clase", "largo",
                      "ancho", "v_canti", "v_cantialt"],
    "piezas.csv": ["numero", "v_codart", "clase", "largo", "ancho", "v_canti", "v_cantialt"],
    "articulos.csv": ["codigo", "descripcion", "familia", "espesor"],
    "familias.csv": ["familia", "medidas", "perimetro"],
}
OPCIONALES = {"familias.csv", "articulos.csv"}


@dataclass
class Casos:
    origen: str
    presupuestos: dict[str, dict] = field(default_factory=dict)  # numero -> fila
    renglones: dict[str, list[dict]] = field(default_factory=dict)
    piezas: dict[str, list[dict]] = field(default_factory=dict)
    articulos: dict[str, dict] = field(default_factory=dict)
    familias: dict[str, dict] = field(default_factory=dict)
    leeme: str = ""
    diferencias: list[str] = field(default_factory=list)  # contra el contrato


def _leer_csv(texto: str) -> list[dict]:
    lector = csv.DictReader(io.StringIO(texto), delimiter=";")
    filas = []
    for fila in lector:
        filas.append({(k or "").strip().lower(): (v or "").strip() if isinstance(v, str) else v
                      for k, v in fila.items()})
    return filas


def _decodificar(datos: bytes) -> str:
    for cod in ("utf-8-sig", "cp1252"):
        try:
            return datos.decode(cod)
        except UnicodeDecodeError:
            continue
    return datos.decode("latin-1")


def _archivos(origen: Path) -> dict[str, bytes]:
    """Nombre (en minúsculas, sin carpetas) -> contenido, de un zip o de una carpeta con los CSV."""
    salida: dict[str, bytes] = {}
    if origen.is_file() and origen.suffix.lower() == ".zip":
        with zipfile.ZipFile(origen) as z:
            for nombre in z.namelist():
                if not nombre.endswith("/"):
                    salida[Path(nombre).name.lower()] = z.read(nombre)
        return salida
    if origen.is_dir():
        for ruta in origen.iterdir():
            if ruta.is_file() and ruta.suffix.lower() != ".zip":
                salida[ruta.name.lower()] = ruta.read_bytes()
    return salida


def leer(origen: Path) -> Casos:
    """Lee un zip, una carpeta con los CSV o una carpeta con varios zips `casos_historicos_*.zip`
    (por ejemplo, uno por año): en ese caso los junta, y si un presupuesto está en dos zips se
    queda con el del zip más nuevo (por nombre) y lo avisa."""
    origen = Path(origen)
    zips = sorted(origen.glob("casos_historicos_*.zip")) if origen.is_dir() else []
    if zips and not (origen / "presupuestos.csv").exists():
        if len(zips) == 1:
            casos = _leer_uno(zips[0])
            casos.origen = str(origen)
            return casos
        return _juntar([_leer_uno(z) for z in zips], origen)
    return _leer_uno(origen)


def _juntar(partes: list["Casos"], origen: Path) -> "Casos":
    casos = Casos(origen=str(origen))
    casos.leeme = "\n\n".join(p.leeme for p in partes if p.leeme)
    repetidos = 0
    for parte in partes:  # de la más vieja a la más nueva: la nueva pisa
        casos.diferencias += [f"{Path(parte.origen).name}: {d}" for d in parte.diferencias]
        for numero, fila in parte.presupuestos.items():
            if numero in casos.presupuestos:
                repetidos += 1
            casos.presupuestos[numero] = fila
            casos.renglones[numero] = parte.renglones.get(numero, [])
            casos.piezas[numero] = parte.piezas.get(numero, [])
        casos.articulos.update(parte.articulos)
        casos.familias.update(parte.familias)
    casos.diferencias.append(f"se juntaron {len(partes)} zips: " + ", ".join(Path(p.origen).name for p in partes))
    if repetidos:
        casos.diferencias.append(f"{repetidos} presupuestos estaban en más de un zip: se usó el del zip más nuevo")
    return casos


def _leer_uno(origen: Path) -> Casos:
    archivos = _archivos(origen)
    casos = Casos(origen=str(origen))
    casos.leeme = _decodificar(archivos.get("leeme.txt", b""))
    tablas: dict[str, list[dict]] = {}
    for nombre, columnas in CONTRATO.items():
        if nombre not in archivos:
            if nombre not in OPCIONALES:
                casos.diferencias.append(f"falta {nombre}")
            tablas[nombre] = []
            continue
        filas = _leer_csv(_decodificar(archivos[nombre]))
        tablas[nombre] = filas
        if filas:
            faltan = [c for c in columnas if c not in filas[0]]
            if faltan:
                casos.diferencias.append(f"{nombre}: faltan columnas {', '.join(faltan)}")
    for f in tablas["presupuestos.csv"]:
        casos.presupuestos[str(f.get("numero"))] = f
    for clave, destino in (("renglones.csv", casos.renglones), ("piezas.csv", casos.piezas)):
        for f in tablas[clave]:
            destino.setdefault(str(f.get("numero")), []).append(f)
    for f in tablas["articulos.csv"]:
        casos.articulos[(f.get("codigo") or "").upper()] = f
    for f in tablas["familias.csv"]:
        casos.familias[(f.get("familia") or "").upper()] = f
    if "observaciones" not in (tablas["presupuestos.csv"][0] if tablas["presupuestos.csv"] else {}):
        if tablas["presupuestos.csv"]:
            casos.diferencias.append("presupuestos.csv: no tiene la columna 'observaciones' (contrato v2); "
                                     "se busca la leyenda en todas las columnas de texto")
    return casos


def numero(valor) -> float | None:
    if valor in (None, ""):
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None
