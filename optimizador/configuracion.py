"""Configuración: planchas por material (`config/hojas.csv`), reglas de corte y presets.

Presets (brief §5.3 y §5.4):
- `corte_certo` — "Como Corte Certo hoy" (por defecto): corte banda del Excel, sin separación,
  sin destaque, rotación sí, textura sin, y +3 mm en ancho y largo de las piezas con pulido
  recto (confirmado por Juan el 25/10/2026).
- `lucas` — "Reglas de corte (Lucas)": lo mismo más la separación entre piezas de
  `reglas_corte.csv` como "ancho de la sierra".
- `H0` a `H2`: las hipótesis de la validación histórica (ver `HIPOTESIS`).

Encima del preset se aplican, en este orden: los ajustes locales de la PC
(`config/local/materiales.json`, que no va a git y no se pierde al actualizar) y los ajustes que
vengan en la entrada del cálculo.
"""

from __future__ import annotations

import copy
import csv
import json
import os
import re
from dataclasses import fields
from pathlib import Path

from .modelo import Material, Plancha

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_CONFIG = Path(os.environ.get("OPTIMIZADOR_CONFIG", RAIZ / "config"))

PULIDO_RECTO_MM = 3  # Juan, 25/10/2026: "+3 mm en ancho Y en largo"

PRESETS = {
    "corte_certo": {
        "nombre": "Como Corte Certo hoy",
        "descripcion": "Corte banda del Excel; sin separación entre piezas ni destaque; +3 mm en "
                       "ancho y largo de las piezas con pulido recto.",
        "separacion": "cero",  # cero | regla
        "como": "sierra",
        "pulido_mm": PULIDO_RECTO_MM,
    },
    "lucas": {
        "nombre": "Reglas de corte (Lucas)",
        "descripcion": "Corte banda + separación entre piezas de la regla de Lucas (20/30/50 mm) "
                       "+ 3 mm en las piezas con pulido recto.",
        "separacion": "regla",
        "como": "sierra",
        "pulido_mm": PULIDO_RECTO_MM,
    },
}

# Hipótesis de la validación histórica (brief §5.4). El +3 mm del pulido recto ya no es
# hipótesis (era H3): está en todas.
HIPOTESIS = {
    "H0": {"nombre": "H0: solo corte banda", "separacion": "cero", "como": "sierra",
           "pulido_mm": PULIDO_RECTO_MM},
    "H1": {"nombre": "H1: banda + separación como sierra", "separacion": "regla", "como": "sierra",
           "pulido_mm": PULIDO_RECTO_MM},
    "H2": {"nombre": "H2: banda + separación como destaque", "separacion": "regla",
           "como": "destaque", "pulido_mm": PULIDO_RECTO_MM},
}

CAMPOS_EDITABLES = {f.name for f in fields(Material)} - {"codigo", "planchas", "avisos"}


def todos_los_presets() -> dict[str, dict]:
    return {**PRESETS, **HIPOTESIS}


def _leer_csv(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def leer_reglas(carpeta: Path | None = None) -> dict[str, dict]:
    """composición ('5', '4+4'…) -> fila de `reglas_corte.csv`."""
    reglas: dict[str, dict] = {}
    for fila in _leer_csv((carpeta or CARPETA_CONFIG) / "reglas_corte.csv"):
        for comp in fila["composiciones"].split("|"):
            reglas[comp.strip()] = fila
    return reglas


class Catalogo:
    """Los materiales de `hojas.csv` con sus planchas y la separación de la regla."""

    def __init__(self, carpeta: Path | None = None, usar_locales: bool = True):
        self.carpeta = Path(carpeta or CARPETA_CONFIG)
        self.usar_locales = usar_locales  # False: ignora config/local (tests, banco, validación)
        self.reglas = leer_reglas(self.carpeta)
        self.materiales: dict[str, Material] = {}
        self.separacion_regla: dict[str, int] = {}
        self.fuente_separacion: dict[str, str] = {}
        self.composicion: dict[str, str] = {}
        for fila in _leer_csv(self.carpeta / "hojas.csv"):
            codigo = fila["codigo"].strip()
            mat = self.materiales.get(codigo)
            if mat is None:
                mat = Material(
                    codigo=codigo,
                    descripcion=fila["descripcion"].strip(),
                    espesor_mm=float(fila["espesor_mm"] or 0),
                    peso_kg_m2=float(fila["peso_kg_m2"] or 0),
                )
                self.materiales[codigo] = mat
                self.composicion[codigo] = fila["composicion"]
                if fila["separacion_piezas_mm"]:
                    self.separacion_regla[codigo] = int(fila["separacion_piezas_mm"])
                self.fuente_separacion[codigo] = fila["separacion_fuente"]
            mat.planchas.append(Plancha(
                ancho=int(fila["hoja_ancho_mm"]),
                largo=int(fila["hoja_largo_mm"]),
                corte_banda=int(fila["corte_banda_mm"]),
                origen=f"{fila['hoja_excel']} fila {fila['fila_excel']}",
            ))

    def ajustes_locales(self) -> dict:
        if not self.usar_locales:
            return {}
        ruta = self.carpeta / "local" / "materiales.json"
        if not ruta.exists():
            return {}
        with ruta.open(encoding="utf-8") as f:
            return json.load(f)

    def material(self, codigo: str, preset: str = "corte_certo",
                 ajustes: dict | None = None, usar_locales: bool = True) -> Material:
        """El material listo para calcular, con el preset y los ajustes aplicados.

        Si el código no está en `hojas.csv`, se arma uno con una plancha **supuesta** de
        3600 × 2500 y la banda de su espesor (si se puede leer del código), con aviso.
        """
        conf = todos_los_presets().get(preset)
        if conf is None:
            raise ValueError(f"preset desconocido: {preset!r} (hay: {', '.join(todos_los_presets())})")
        base = self.materiales.get(codigo)
        if base is not None:
            mat = copy.deepcopy(base)
            separacion = self.separacion_regla.get(codigo, 0)
            fuente = self.fuente_separacion.get(codigo, "")
            if conf["separacion"] == "regla" and fuente.startswith("supuesto"):
                mat.avisos.append(f"separación entre piezas de {codigo} supuesta ({fuente})")
        else:
            mat, separacion = self._material_supuesto(codigo)
        if conf["separacion"] == "regla":
            if conf["como"] == "sierra":
                mat.separacion_piezas_mm = separacion
            else:
                mat.destaque_min_mm = separacion
        mat.sobremedida_pulido_mm = conf["pulido_mm"]
        for origen, valores in (("locales", self.ajustes_locales().get(codigo, {}) if usar_locales else {}),
                                ("entrada", (ajustes or {}))):
            _aplicar(mat, valores, origen)
        return mat

    def _material_supuesto(self, codigo: str) -> tuple[Material, int]:
        comp, espesor = composicion_de_codigo(codigo)
        regla = self.reglas.get(comp) if comp else None
        mat = Material(codigo=codigo, descripcion=f"{codigo} (no está en hojas.csv)")
        if regla is None:
            mat.avisos.append(f"{codigo} no está en config/hojas.csv y no se entiende su espesor: "
                              "no tiene planchas")
            return mat, 0
        banda = int(regla["corte_banda_mm"])
        mat.espesor_mm = espesor
        mat.peso_kg_m2 = espesor * 2.5
        mat.planchas.append(Plancha(3600, 2500, banda, supuesta=True,
                                    origen=f"supuesta: 3600 × 2500 con banda {banda} (espesor {comp})"))
        mat.avisos.append(f"{codigo} no está en config/hojas.csv: se usa una plancha SUPUESTA de "
                          f"3600 × 2500 con corte banda {banda} (espesor {comp})")
        return mat, int(regla["separacion_piezas_mm"])

    def lista(self) -> list[Material]:
        return [self.materiales[c] for c in sorted(self.materiales)]


def _aplicar(mat: Material, valores: dict, origen: str) -> None:
    """Pisa campos del material. `planchas` reemplaza la lista entera."""
    for campo, valor in valores.items():
        if campo == "planchas":
            mat.planchas = [Plancha(**p) if isinstance(p, dict) else p for p in valor]
        elif campo == "comercial":
            continue  # precios provisorios: se guardan, todavía no se usan en el cálculo
        elif campo == "planchas_habilitadas":
            # {"3600x2500": true, "3600x2200": false}
            for p in mat.planchas:
                if p.clave() in valor:
                    p.habilitada = bool(valor[p.clave()])
        elif campo in CAMPOS_EDITABLES:
            actual = getattr(mat, campo)
            if isinstance(actual, bool):
                valor = bool(valor)
            elif isinstance(actual, int):
                valor = int(valor)
            elif isinstance(actual, float):
                valor = float(valor)
            setattr(mat, campo, valor)
        else:
            mat.avisos.append(f"ajuste desconocido para {mat.codigo} ({origen}): {campo!r}, se ignora")


def composicion_de_codigo(codigo: str) -> tuple[str | None, float]:
    """'FL8BR' -> ('8', 8); 'LX4+4XX' -> ('4+4', 8). Si no se entiende, (None, 0)."""
    texto = codigo.upper()
    lam = re.search(r"(\d+)\s*\+\s*(\d+)", texto)
    if lam:
        a, b = int(lam.group(1)), int(lam.group(2))
        return f"{a}+{b}", a + b
    mono = re.match(r"^[A-Z]+?(\d+)", texto)
    if mono:
        n = int(mono.group(1))
        return str(n), n
    return None, 0
