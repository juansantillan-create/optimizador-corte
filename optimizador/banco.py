"""Banco de pruebas sintético (brief §11).

Dos familias de casos, generados con semilla fija y guardados como archivos en `tests/banco/`:

- **Corte perfecto**: se parten k planchas en piezas con cortes de guillotina al azar (con y sin
  separación entre piezas). Las piezas llenan exacto las k planchas, así que el óptimo es k: el
  motor tiene que encontrar k (o decir a cuánto quedó).
- **Realistas**: medidas típicas de templados y DVH (de 300 a 2500 mm, muchas repetidas) y casos
  como el 413 (piezas grandes, ~3 por plancha). Se comparan contra el mínimo teórico.

Uso:
    python -m optimizador banco                 # corre todo y compara con lo esperado
    python -m optimizador banco --generar       # vuelve a generar los archivos (no hace falta)
    python -m optimizador banco --guardar       # guarda los resultados como "esperados"
"""

from __future__ import annotations

import json
import platform
import random
import time
from pathlib import Path

from .api import optimizar

CARPETA = Path(__file__).resolve().parents[1] / "tests" / "banco"
FECHA_FIJA = "2026-10-25 00:00:00"
UTIL = (3580, 2500)  # FL5IN: plancha útil de 3600 × 2500 con banda 20


# ----------------------------------------------------------------- generadores
def _partir(r: random.Random, x: int, y: int, w: int, h: int, minimo: int, paso: int,
            objetivo_area: float, salida: list):
    """Parte el rectángulo (agrandado) con cortes de guillotina al azar."""
    area = w * h
    puede_x = w >= 2 * minimo
    puede_y = h >= 2 * minimo
    if (not puede_x and not puede_y) or area < 0.6 * objetivo_area or (
            area <= 1.3 * objetivo_area and r.random() < 0.8):
        salida.append((w, h))
        return
    if puede_x and puede_y:
        eje = "x" if r.random() < w / (w + h) else "y"
    else:
        eje = "x" if puede_x else "y"
    largo = w if eje == "x" else h
    opciones = list(range(minimo, largo - minimo + 1, paso))
    if not opciones:
        salida.append((w, h))
        return
    c = r.choice(opciones)
    if eje == "x":
        _partir(r, x, y, c, h, minimo, paso, objetivo_area, salida)
        _partir(r, x + c, y, w - c, h, minimo, paso, objetivo_area, salida)
    else:
        _partir(r, x, y, w, c, minimo, paso, objetivo_area, salida)
        _partir(r, x, y + c, w, h - c, minimo, paso, objetivo_area, salida)


def _partir_3_etapas(r: random.Random, W: int, H: int, minimo: int, paso: int,
                     piezas_por_plancha: int) -> list[tuple[int, int]]:
    """Como corta una mesa: tiras verticales, renglones horizontales y piezas (3 etapas)."""
    def trozos(largo: int, cuantos: int) -> list[int]:
        cuantos = max(1, min(cuantos, largo // (2 * minimo)))
        cortes: set[int] = set()
        intentos = 0
        while len(cortes) < cuantos - 1 and intentos < 1000:
            intentos += 1
            c = r.randrange(minimo, largo - minimo + 1, paso)
            if all(abs(c - x) >= minimo for x in cortes):
                cortes.add(c)
        puntos = [0] + sorted(cortes) + [largo]
        return [b - a for a, b in zip(puntos, puntos[1:])]
    n_tiras = r.randint(1, 4)
    por_tira = max(1, round(piezas_por_plancha / n_tiras))
    salida = []
    for ancho in trozos(W, n_tiras):
        n_renglones = r.randint(1, max(1, por_tira))
        for alto in trozos(H, n_renglones):
            por_renglon = max(1, round(por_tira / n_renglones)) if r.random() < 0.5 else 1
            for a in trozos(ancho, por_renglon):
                salida.append((a, alto))
    return salida


def caso_corte_perfecto(semilla: int, planchas: int, piezas_por_plancha: int, separacion: int,
                        paso: int, etapas: str = "libre") -> dict:
    r = random.Random(semilla)
    W, H = UTIL
    s = separacion
    medidas: list[tuple[int, int]] = []
    objetivo = (W + s) * (H + s) / piezas_por_plancha
    for _ in range(planchas):
        partes: list[tuple[int, int]] = []
        if etapas == "3":
            partes = _partir_3_etapas(r, W + s, H + s, 250 + s, paso, piezas_por_plancha)
        else:
            _partir(r, 0, 0, W + s, H + s, 250 + s, paso, objetivo, partes)
        medidas += [(a - s, b - s) for a, b in partes]
    cuenta: dict[tuple[int, int], int] = {}
    for a, b in medidas:
        cuenta[(a, b)] = cuenta.get((a, b), 0) + 1
    piezas = [{"item": str(i + 1), "material": "FL5IN", "cantidad": n, "ancho": a, "largo": b}
              for i, ((a, b), n) in enumerate(sorted(cuenta.items()))]
    return {
        "proyecto": {"codigo": f"CP{etapas[0].upper()}-{semilla}",
                     "descripcion": f"corte perfecto ({'3 etapas' if etapas == '3' else 'guillotina libre'}): "
                                    f"{planchas} planchas"},
        "preset": "lucas" if s else "corte_certo",
        "piezas": piezas,
        "fecha": FECHA_FIJA,
        "banco": {"familia": "corte_perfecto", "etapas": etapas, "optimo": planchas,
                  "separacion": s, "piezas": len(medidas)},
    }


def caso_realista(semilla: int, tipos: int, piezas: int, minimo: int, maximo: int,
                  material: str = "FL5IN") -> dict:
    r = random.Random(semilla)
    medidas = set()
    while len(medidas) < tipos:
        a = r.randint(minimo, maximo) // 5 * 5
        b = r.randint(minimo, min(maximo, 2500)) // 5 * 5
        medidas.add((a, b))
    medidas = sorted(medidas)
    cantidades = [1] * tipos
    for _ in range(piezas - tipos):
        # muchas repetidas: unas pocas medidas se llevan casi todo
        cantidades[min(int(r.expovariate(4.0 / tipos)), tipos - 1)] += 1
    lista = [{"item": str(i + 1), "material": material, "cantidad": n, "ancho": a, "largo": b}
             for i, ((a, b), n) in enumerate(zip(medidas, cantidades))]
    return {
        "proyecto": {"codigo": f"RE-{semilla}", "descripcion": f"realista: {piezas} piezas, {tipos} medidas"},
        "preset": "corte_certo",
        "piezas": lista,
        "fecha": FECHA_FIJA,
        "banco": {"familia": "realista", "piezas": piezas},
    }


def caso_tipo_413(semilla: int) -> dict:
    """Como el proyecto 413: 252 piezas grandes (unas 3 por plancha) de pocas medidas."""
    r = random.Random(semilla)
    base = [(1000, 2380), (1130, 2385), (1880, 1000), (1590, 790), (1400, 1000), (1155, 1290)]
    medidas = [(a + r.randint(-60, 60) // 5 * 5, b + r.randint(-40, 40) // 5 * 5) for a, b in base]
    medidas += [(r.randint(900, 1300) // 5 * 5, r.randint(2000, 2450) // 5 * 5) for _ in range(6)]
    cantidades = [1] * len(medidas)
    for _ in range(252 - len(medidas)):
        cantidades[r.randrange(len(medidas))] += 1
    lista = [{"item": str(i + 1), "material": "FL5IN", "cantidad": n, "ancho": a, "largo": b}
             for i, ((a, b), n) in enumerate(zip(medidas, cantidades))]
    return {
        "proyecto": {"codigo": f"T413-{semilla}", "descripcion": "parecido al 413 (inventado)"},
        "preset": "corte_certo",
        "piezas": lista,
        "fecha": FECHA_FIJA,
        "banco": {"familia": "tipo_413", "piezas": 252},
    }


def generar(carpeta: Path = CARPETA) -> list[Path]:
    """Escribe los casos del banco (siempre los mismos: semillas fijas)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    casos = []
    semilla = 1000
    for etapas in ("3", "libre"):
        for separacion in (0, 20):
            for paso in (10, 1):
                for planchas, por_plancha in ((1, 4), (1, 8), (2, 6), (3, 5), (4, 8), (6, 6),
                                              (8, 10), (10, 8), (5, 15)):
                    semilla += 1
                    casos.append(caso_corte_perfecto(semilla, planchas, por_plancha, separacion,
                                                     paso, etapas))
    for i, (tipos, piezas, mn, mx) in enumerate([(5, 20, 300, 1500), (10, 50, 300, 2400),
                                                 (15, 80, 300, 1800), (20, 120, 300, 2500),
                                                 (30, 300, 300, 2400), (30, 300, 300, 1200),
                                                 (8, 40, 600, 2500), (25, 200, 400, 2000),
                                                 (12, 60, 300, 900), (30, 250, 500, 2500)]):
        casos.append(caso_realista(2000 + i, tipos, piezas, mn, mx))
    for i in range(3):
        casos.append(caso_tipo_413(3000 + i))
    rutas = []
    for caso in casos:
        ruta = carpeta / f"{caso['proyecto']['codigo']}.json"
        ruta.write_text(json.dumps(caso, ensure_ascii=False, indent=1), encoding="utf-8")
        rutas.append(ruta)
    return rutas


# --------------------------------------------------------------------- correr
def correr(carpeta: Path = CARPETA, esfuerzo: str = "normal", filtro: str = "",
           mostrar=print) -> dict:
    resultados = []
    for ruta in sorted(carpeta.glob("*.json")):
        if ruta.name == "esperado.json" or (filtro and filtro not in ruta.stem):
            continue
        caso = json.loads(ruta.read_text(encoding="utf-8"))
        caso["opciones"] = {"esfuerzo": esfuerzo}
        t0 = time.perf_counter()
        res = optimizar(caso)
        segundos = time.perf_counter() - t0
        m = res["materiales"][0]
        fila = {
            "caso": ruta.stem,
            "familia": caso["banco"]["familia"],
            "etapas": caso["banco"].get("etapas"),
            "piezas": caso["banco"]["piezas"],
            "optimo": caso["banco"].get("optimo"),
            "planchas": m["planchas"],
            "minimo_teorico": m.get("minimo_teorico_planchas"),
            "montajes": m["layouts"],
            "aprovechamiento": m["aprovechamiento"],
            "verificado": res["verificado"],
            "segundos": round(segundos, 2),
        }
        resultados.append(fila)
        mostrar(f"{fila['caso']:<10} {fila['familia']:<15} {fila['piezas']:>4} piezas  "
                f"{fila['planchas']:>4} planchas (óptimo {fila['optimo'] or '-'}, mínimo teórico "
                f"{fila['minimo_teorico']})  {fila['montajes']:>3} montajes  "
                f"{fila['segundos']:6.2f} s  {'OK' if fila['verificado'] else 'FALLÓ VALIDADOR'}")
    return {"esfuerzo": esfuerzo, "maquina": maquina(), "casos": resultados}


def maquina() -> str:
    import os
    procesador = platform.processor() or platform.machine()
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("model name"):
                    procesador = linea.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return (f"{platform.system()} {platform.release()}, Python {platform.python_version()}, "
            f"{procesador}, {os.cpu_count()} núcleos")


def resumen(datos: dict) -> dict:
    casos = datos["casos"]
    perfectos = [c for c in casos if c["familia"] == "corte_perfecto"]
    hasta_100 = [c for c in perfectos if c["piezas"] <= 100]
    otros = [c for c in casos if c["familia"] != "corte_perfecto"]
    return {
        "casos": len(casos),
        "validados": sum(c["verificado"] for c in casos),
        "perfectos": len(perfectos),
        "perfectos_3_etapas_hasta_100": sum(1 for c in hasta_100 if c.get("etapas") == "3"),
        "perfectos_3_etapas_hasta_100_optimos": sum(1 for c in hasta_100 if c.get("etapas") == "3"
                                                    and c["planchas"] == c["optimo"]),
        "perfectos_optimos": sum(c["planchas"] == c["optimo"] for c in perfectos),
        "perfectos_hasta_100": len(hasta_100),
        "perfectos_hasta_100_optimos": sum(c["planchas"] == c["optimo"] for c in hasta_100),
        "perfectos_planchas_de_mas": sum(c["planchas"] - c["optimo"] for c in perfectos),
        "otros": len(otros),
        "otros_en_minimo": sum(c["planchas"] == c["minimo_teorico"] for c in otros),
        "otros_dif_minimo": sum(c["planchas"] - c["minimo_teorico"] for c in otros),
        "segundos_max": max((c["segundos"] for c in casos), default=0),
        "segundos_total": round(sum(c["segundos"] for c in casos), 1),
    }


def comparar_con_esperado(datos: dict, carpeta: Path = CARPETA) -> list[str]:
    """Casos donde ahora da más planchas que lo guardado como esperado (empeoró)."""
    ruta = carpeta / "esperado.json"
    if not ruta.exists():
        return []
    esperado = {c["caso"]: c for c in json.loads(ruta.read_text(encoding="utf-8"))["casos"]}
    peores = []
    for c in datos["casos"]:
        e = esperado.get(c["caso"])
        if e and c["planchas"] > e["planchas"]:
            peores.append(f"{c['caso']}: {c['planchas']} planchas (antes {e['planchas']})")
        if not c["verificado"]:
            peores.append(f"{c['caso']}: no pasó el validador")
    return peores
