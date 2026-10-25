"""Configuración: planchas por material (`config/hojas.csv`), reglas de corte y presets.

Presets (brief §5.3 y §5.4):
- `corte_certo` — "Como Corte Certo hoy" (por defecto): corte banda del Excel, sin separación,
  sin destaque, rotación sí, textura sin, y +3 mm en ancho y largo de las piezas con pulido
  recto (confirmado por Juan el 25/10/2026).
- `lucas` — "Reglas de corte (Lucas, como Optima)": lo mismo más la distancia de
  `reglas_corte.csv` como **destaque mínimo** (Juan, 25/10: las piezas pueden compartir el corte,
  pero si entre dos queda una tira de sobrante, tiene que medir al menos 20/30/50 mm).
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

# Corte banda con que se cotiza en "Como Corte Certo hoy": 20 mm en todos los vidrios (la plancha de
# 3600 queda en 3580), como dijo Juan ("solo se carga la plancha ya achicada"). OJO: los casos
# históricos dicen otra cosa: con el % redondeado, hasta septiembre de 2026 Corte Certo cortaba
# sobre la hoja entera (3600, sin banda); ver docs/VALIDACION.md §1 y la pregunta 28. Con la
# regla de Lucas (30/50) casi nunca cierra.
BANDA_CORTE_CERTO_MM = 20

PRESETS = {
    "corte_certo": {
        "nombre": "Como Corte Certo hoy",
        "descripcion": "Corte banda de 20 mm en todos los vidrios (la plancha de 3600 queda en 3580; "
                       "pregunta 28); sin separación entre piezas ni destaque; +3 mm en ancho y largo de "
                       "las piezas con pulido recto.",
        "separacion": "cero",  # cero | regla
        "como": "sierra",
        "pulido_mm": PULIDO_RECTO_MM,
        "banda_mm": BANDA_CORTE_CERTO_MM,  # None = la de hojas.csv
    },
    "lucas": {
        "nombre": "Reglas de corte (Lucas, como Optima)",
        "descripcion": "Corte banda + destaque mínimo de la regla de Lucas (20/30/50 mm: las piezas "
                       "pueden compartir el corte, pero una tira de sobrante entre piezas tiene que "
                       "medir al menos eso) + 3 mm en las piezas con pulido recto.",
        "separacion": "regla",
        "como": "destaque",
        "pulido_mm": PULIDO_RECTO_MM,
    },
}

# Hipótesis de la validación histórica (brief §5.4). El +3 mm del pulido recto ya no es
# hipótesis (era H3): está en todas.
HIPOTESIS = {
    "H0": {"nombre": "H0: solo corte banda (20 mm, como Corte Certo)", "separacion": "cero",
           "como": "sierra", "pulido_mm": PULIDO_RECTO_MM, "banda_mm": BANDA_CORTE_CERTO_MM},
    # Las tres con la misma plancha útil (la de Corte Certo): solo cambia la separación.
    "H1": {"nombre": "H1: banda + separación como sierra", "separacion": "regla", "como": "sierra",
           "pulido_mm": PULIDO_RECTO_MM, "banda_mm": BANDA_CORTE_CERTO_MM},
    "H2": {"nombre": "H2: banda + separación como destaque", "separacion": "regla",
           "como": "destaque", "pulido_mm": PULIDO_RECTO_MM, "banda_mm": BANDA_CORTE_CERTO_MM},
}

CAMPOS_EDITABLES = {f.name for f in fields(Material)} - {"codigo", "planchas", "avisos"}
# Campos que cada preset pone a su manera: un cambio hecho en esta PC vale solo para ese preset.
CAMPOS_POR_PRESET = {"separacion_piezas_mm", "destaque_min_mm", "sobremedida_pulido_mm"}
# Campos de texto y los valores que aceptan.
TEXTURAS = {"sin": "sin", "sem": "sin", "no": "sin", "ninguna": "sin", "": "sin",
            "horizontal": "horizontal", "h": "horizontal", "vertical": "vertical", "v": "vertical"}


class ConfiguracionInvalida(ValueError):
    """Un valor de la configuración de un material que no se puede usar (negativo, no numérico…)."""


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
        for mat in self.materiales.values():
            elegir_plancha_por_defecto(mat)

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
                que = "separación entre piezas" if conf["como"] == "sierra" else "destaque mínimo"
                mat.avisos.append(f"{que} de {codigo} supuesto ({fuente})")
        else:
            mat, separacion = self._material_supuesto(codigo)
        if conf.get("banda_mm") is not None:
            for p in mat.planchas:
                p.corte_banda = conf["banda_mm"]
        if conf["separacion"] == "regla":
            if conf["como"] == "sierra":
                mat.separacion_piezas_mm = separacion
            else:
                mat.destaque_min_mm = separacion
        mat.sobremedida_pulido_mm = conf["pulido_mm"]
        locales = dict(self.ajustes_locales().get(codigo, {})) if usar_locales else {}
        # La separación, el destaque y el pulido dependen del preset: si se cambiaron en esta PC,
        # se guardaron para ese preset solo (ver `CAMPOS_POR_PRESET`).
        por_preset = locales.pop("por_preset", {}) or {}
        for origen, valores in (("locales", locales),
                                (f"locales del preset {preset}", por_preset.get(preset, {})),
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


# Juan, 25/10/2026 (pregunta 3): "si está la opción de 3600 × 2500, usar siempre esa por defecto;
# si no, la de 3700 × 2500". Las demás medidas quedan, deshabilitadas, para habilitarlas a mano.
PLANCHAS_PREFERIDAS = ((3600, 2500), (3700, 2500))


def elegir_plancha_por_defecto(mat: Material) -> None:
    """Deja habilitada solo la medida preferida si el material la tiene; si no, todas."""
    for medida in PLANCHAS_PREFERIDAS:
        if any((p.ancho, p.largo) == medida for p in mat.planchas):
            for p in mat.planchas:
                p.habilitada = (p.ancho, p.largo) == medida
            return


def _numero(mat: Material, campo: str, valor, origen: str, entero: bool, minimo: float = 0) -> float | int:
    """Un número de la configuración: finito, no negativo; si es entero y vino con decimales, se
    redondea con aviso. Si no se puede usar, `ConfiguracionInvalida`."""
    try:
        if isinstance(valor, (int, float)):
            x = float(valor)
        else:
            texto = str(valor).strip()
            if re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
                texto = texto.replace(".", "")  # "3.600" es 3600 (punto de miles)
            elif "," in texto and "." in texto:
                texto = texto.replace(".", "").replace(",", ".")
            x = float(texto.replace(",", "."))
    except ValueError:
        raise ConfiguracionInvalida(f"{mat.codigo}: {campo} = {valor!r} no es un número ({origen})") from None
    if x != x or x in (float("inf"), float("-inf")):
        raise ConfiguracionInvalida(f"{mat.codigo}: {campo} = {valor!r} no es un número ({origen})")
    if x < minimo:
        raise ConfiguracionInvalida(f"{mat.codigo}: {campo} = {valor!r} no puede ser menor que {minimo:g} ({origen})")
    if not entero:
        return x
    if x != int(x):
        mat.avisos.append(f"{mat.codigo}: {campo} = {valor} no es entero; se usa {round(x)} ({origen})")
    return int(round(x))


def normalizar_textura(valor) -> str | None:
    """'Sem', 'sin', '' -> 'sin'; 'Horizontal' -> 'horizontal'; … Lo que no se entiende, None."""
    return TEXTURAS.get(str(valor or "").strip().lower())


def _aplicar(mat: Material, valores: dict, origen: str) -> None:
    """Pisa campos del material. `planchas` reemplaza la lista entera. Un valor que no se puede usar
    (negativo, no numérico, textura desconocida) es `ConfiguracionInvalida`: no se calcula con él."""
    for campo, valor in valores.items():
        if campo == "planchas":
            planchas = []
            for p in valor:
                try:
                    pl = Plancha(**p) if isinstance(p, dict) else p
                except TypeError:
                    raise ConfiguracionInvalida(f"{mat.codigo}: una plancha tiene que tener ancho, largo y "
                                                f"corte_banda ({origen}): {p!r}") from None
                pl.ancho = _numero(mat, "ancho de plancha", pl.ancho, origen, True, 1)
                pl.largo = _numero(mat, "largo de plancha", pl.largo, origen, True, 1)
                pl.corte_banda = _numero(mat, "corte banda", pl.corte_banda, origen, True)
                if pl.ancho < pl.largo:
                    mat.avisos.append(f"{mat.codigo}: la plancha {pl.ancho} × {pl.largo} venía parada; "
                                      f"se toma {pl.largo} × {pl.ancho} (el ancho es el lado largo)")
                    pl.ancho, pl.largo = pl.largo, pl.ancho
                planchas.append(pl)
            mat.planchas = planchas
        elif campo == "comercial":
            continue  # precios provisorios: se guardan, todavía no se usan en el cálculo
        elif campo == "planchas_habilitadas":
            # {"3600x2500": true, "3600x2200": false}
            claves = {p.clave(): p for p in mat.planchas}
            for clave, habilitada in valor.items():
                normal = str(clave).lower().replace(" ", "").replace("×", "x")
                if normal not in claves:
                    mat.avisos.append(f"{mat.codigo}: no tiene la plancha {clave!r} ({origen}); se ignora "
                                      f"(tiene: {', '.join(claves)})")
                    continue
                claves[normal].habilitada = _booleano(habilitada)
        elif campo == "textura":
            textura = normalizar_textura(valor)
            if textura is None:
                raise ConfiguracionInvalida(f"{mat.codigo}: textura {valor!r} no se entiende ({origen}); "
                                            "tiene que ser sin, horizontal o vertical")
            mat.textura = textura
        elif campo in CAMPOS_EDITABLES:
            actual = getattr(mat, campo)
            if isinstance(actual, bool):
                valor = _booleano(valor)
            elif isinstance(actual, int):
                valor = _numero(mat, campo, valor, origen, True)
            elif isinstance(actual, float):
                valor = _numero(mat, campo, valor, origen, False)
            setattr(mat, campo, valor)
        else:
            mat.avisos.append(f"ajuste desconocido para {mat.codigo} ({origen}): {campo!r}, se ignora")


def _booleano(valor) -> bool:
    """True/False, también desde texto ("false", "no", "0" son falso)."""
    if isinstance(valor, str):
        return valor.strip().lower() in ("true", "si", "sí", "s", "1", "x", "verdadero")
    return bool(valor)


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
