"""Convierte config/fuentes/Medidas_hojas.xlsx en config/hojas.csv.

Uso (desde la raíz del repo):

    python herramientas/importar_medidas_hojas.py
    python herramientas/importar_medidas_hojas.py <otro.xlsx> <salida.csv>

Qué hace:
- Lee todas las hojas del Excel que tengan las columnas Descripción, Código, Largo,
  Ancho y CORTE BANDA (hoy: MONOLITICO y LAMINADO).
- Si en una hoja vienen invertidas Descripción y Código (pasa en LAMINADO), lo
  detecta y lo corrige con aviso.
- Plancha útil: al lado largo (columna "Ancho" del Excel) se le resta el CORTE
  BANDA. Es lo mismo que hacen las columnas LARGO NUEVO / ANCHO NUEVO del Excel y
  lo que está cargado en Corte Certo (3600 x 2500 -> 3580 x 2500).
- Saca la composición (5, 10, 3+3, 4+4...) de la descripción y le pone la
  separación entre piezas según config/reglas_corte.csv.
- No adivina: lo que no entiende o no coincide con la regla queda en la columna
  "avisos" y se imprime al final.

Solo necesita openpyxl. No toca el Excel original.
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parents[1]
XLSX_DEFECTO = RAIZ / "config" / "fuentes" / "Medidas_hojas.xlsx"
CSV_DEFECTO = RAIZ / "config" / "hojas.csv"
REGLAS = RAIZ / "config" / "reglas_corte.csv"

# Densidad del vidrio: 2,5 kg por m² y por mm de espesor (para el "peso específico"
# de Corte Certo). Es un valor calculado, no viene del Excel.
KG_M2_POR_MM = 2.5

COLUMNAS_SALIDA = [
    "codigo", "descripcion", "hoja_excel", "fila_excel", "composicion", "espesor_mm",
    "laminado", "hoja_ancho_mm", "hoja_largo_mm", "corte_banda_mm", "util_ancho_mm",
    "util_largo_mm", "separacion_piezas_mm", "separacion_fuente", "grupo_regla",
    "peso_kg_m2", "avisos",
]


def _normalizar(texto) -> str:
    """'Descripción ' -> 'descripcion' (sin tildes, minúsculas, espacios simples)."""
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().lower()


def _leer_reglas(ruta: Path) -> dict[str, dict]:
    """composición ('5', '4+4'...) -> fila de reglas_corte.csv."""
    reglas = {}
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            for comp in fila["composiciones"].split("|"):
                reglas[comp.strip()] = fila
    return reglas


def _composicion(descripcion: str, codigo: str) -> tuple[str | None, int | None, bool]:
    """Devuelve (composición, espesor total en mm, es_laminado) o (None, None, False)."""
    for texto in (descripcion.upper(), codigo.upper()):
        lam = re.search(r"(\d+)\s*\+\s*(\d+)", texto)
        if lam:
            a, b = int(lam.group(1)), int(lam.group(2))
            return f"{a}+{b}", a + b, True
    mono = re.search(r"(\d+)\s*MM", descripcion.upper())
    if mono:
        n = int(mono.group(1))
        return str(n), n, False
    cod = re.match(r"^[A-Z]+?(\d+)", codigo.upper())  # FL10IN -> 10, CA4M1 -> 4
    if cod:
        n = int(cod.group(1))
        return str(n), n, False
    return None, None, False


def _es_confirmado(codigo: str, composicion: str, laminado: bool, estado_regla: str) -> bool:
    """La regla de Lucas habla de float (FL) y de laminados (Lamilux, LX)."""
    if estado_regla != "confirmado":
        return False
    return codigo.upper().startswith("LX") if laminado else codigo.upper().startswith("FL")


def importar(xlsx: Path, salida: Path) -> list[dict]:
    reglas = _leer_reglas(REGLAS)
    libro = openpyxl.load_workbook(xlsx, data_only=True, read_only=True)
    filas_salida: list[dict] = []
    vistos: dict[tuple, int] = {}

    for hoja in libro.worksheets:
        filas = list(hoja.iter_rows(values_only=True))
        if not filas:
            continue
        encabezado = [_normalizar(c) for c in filas[0]]
        try:
            i_desc = encabezado.index("descripcion")
            i_cod = encabezado.index("codigo")
            i_largo = encabezado.index("largo")
            i_ancho = encabezado.index("ancho")
            i_banda = encabezado.index("corte banda")
        except ValueError:
            print(f"[aviso] hoja '{hoja.title}': no tiene las columnas esperadas, se saltea")
            continue

        # ¿Vienen invertidas Descripción y Código? El código no tiene espacios
        # (FL10IN, LX3+3IN); la descripción sí.
        datos = [f for f in filas[1:] if f and f[i_cod] not in (None, "")]
        cod_con_espacio = sum(" " in str(f[i_cod]).strip() for f in datos)
        desc_con_espacio = sum(" " in str(f[i_desc]).strip() for f in datos)
        invertidas = cod_con_espacio > len(datos) / 2 and desc_con_espacio < len(datos) / 2
        if invertidas:
            i_desc, i_cod = i_cod, i_desc
            print(f"[aviso] hoja '{hoja.title}': Descripción y Código vienen invertidas; "
                  "se leen al revés")

        for n_fila, f in enumerate(filas[1:], start=2):
            if not f or f[i_cod] in (None, ""):
                continue
            avisos = []
            codigo = str(f[i_cod]).strip()
            descripcion = re.sub(r"\s+", " ", str(f[i_desc] or "")).strip()
            try:
                largo, ancho, banda = int(f[i_largo]), int(f[i_ancho]), int(f[i_banda])
            except (TypeError, ValueError):
                print(f"[aviso] {hoja.title} fila {n_fila} ({codigo}): medidas no numéricas, "
                      "se saltea")
                continue
            if invertidas:
                avisos.append("Descripción/Código invertidas en el Excel")

            # El corte banda va siempre del lado más largo.
            lado_largo, lado_corto = max(largo, ancho), min(largo, ancho)
            if ancho < largo:
                avisos.append("en el Excel el lado largo está en 'Largo' (se toma el mayor)")

            comp, espesor, laminado = _composicion(descripcion, codigo)
            regla = reglas.get(comp) if comp else None
            if comp is None:
                avisos.append("no se entiende el espesor: falta separación")
                separacion, fuente, grupo = "", "", ""
            elif regla is None:
                avisos.append(f"composición {comp} sin regla: falta separación")
                separacion, fuente, grupo = "", "", ""
            else:
                separacion = int(regla["separacion_piezas_mm"])
                grupo = regla["grupo"]
                if _es_confirmado(codigo, comp, laminado, regla["estado"]):
                    fuente = regla["fuente"]
                elif regla["estado"] == "confirmado":
                    fuente = "supuesto por espesor (la regla es de float/Lamilux)"
                else:
                    fuente = f"supuesto ({regla['nota']})"
                if int(regla["corte_banda_mm"]) != banda:
                    avisos.append(f"banda del Excel ({banda}) distinta a la regla "
                                  f"({regla['corte_banda_mm']}): vale la del Excel")

            clave = (codigo, lado_largo, lado_corto)
            if clave in vistos:
                avisos.append(f"repetida (igual que la fila {vistos[clave]})")
            vistos[clave] = n_fila

            filas_salida.append({
                "codigo": codigo,
                "descripcion": descripcion,
                "hoja_excel": hoja.title,
                "fila_excel": n_fila,
                "composicion": comp or "",
                "espesor_mm": espesor or "",
                "laminado": "SI" if laminado else "NO",
                "hoja_ancho_mm": lado_largo,
                "hoja_largo_mm": lado_corto,
                "corte_banda_mm": banda,
                "util_ancho_mm": lado_largo - banda,
                "util_largo_mm": lado_corto,
                "separacion_piezas_mm": separacion,
                "separacion_fuente": fuente,
                "grupo_regla": grupo,
                "peso_kg_m2": f"{espesor * KG_M2_POR_MM:g}" if espesor else "",
                "avisos": " | ".join(avisos),
            })

    salida.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: Excel en Windows abre bien las tildes.
    with salida.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS_SALIDA, delimiter=";")
        w.writeheader()
        w.writerows(filas_salida)
    return filas_salida


def main() -> None:
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else XLSX_DEFECTO
    salida = Path(sys.argv[2]) if len(sys.argv) > 2 else CSV_DEFECTO
    filas = importar(xlsx, salida)
    codigos = {f["codigo"] for f in filas}
    varias = sorted(c for c in codigos if sum(f["codigo"] == c for f in filas) > 1)
    con_aviso = [f for f in filas if f["avisos"]
                 and f["avisos"] != "Descripción/Código invertidas en el Excel"]
    print(f"{len(filas)} medidas de plancha, {len(codigos)} materiales -> {salida}")
    print(f"Materiales con más de una medida ({len(varias)}): {', '.join(varias)}")
    supuestas = sorted({f["codigo"] for f in filas if f["separacion_fuente"].startswith("supuesto")})
    print(f"Separación supuesta (no está en la regla de Lucas) ({len(supuestas)}): "
          f"{', '.join(supuestas)}")
    for f in con_aviso:
        print(f"[aviso] {f['hoja_excel']} fila {f['fila_excel']} {f['codigo']}: {f['avisos']}")


if __name__ == "__main__":
    main()
