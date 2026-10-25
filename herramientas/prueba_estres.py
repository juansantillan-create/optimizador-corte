"""Prueba de estrés: muchos casos al azar (con semilla fija) y todos tienen que pasar el validador.

    python herramientas/prueba_estres.py                 # 500 casos, semilla 1
    python herramientas/prueba_estres.py --casos 100 --semilla 7

Mezcla dos clases de casos:
- chicos: planchas chicas, pocas piezas, configuraciones raras (separación, destaque, veta,
  márgenes, constante), como `tests/test_aleatorio.py`;
- de tamaño real: plancha 3600 × 2500, de 20 a 400 piezas, de 3 a 60 medidas, con pulido recto.

Los que fallan se guardan en `salida/estres/` (la entrada, para repetirlos con
`python -m optimizador calcular`). Al final dice cuántos fallaron y el tiempo de cada clase.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from optimizador.api import optimizar  # noqa: E402


def caso_chico(r: random.Random) -> dict:
    piezas = [{"item": str(i + 1), "material": "FL5IN", "cantidad": r.randint(1, 6),
               "ancho": r.randint(30, 700), "largo": r.randint(30, 600),
               "rota": r.choice([None, None, True, False]),
               "clase": r.choice(["", "FLOAT PR TEMP", "FLOAT TEMP"])} for i in range(r.randint(1, 8))]
    ajustes = {"separacion_piezas_mm": r.choice([0, 0, 5, 20]), "destaque_min_mm": r.choice([0, 0, 10, 25]),
               "rotacion": r.random() < 0.5, "textura": r.choice(["sin", "sin", "sin", "horizontal", "vertical"]),
               "constante_ancho_mm": r.choice([0, 0, 2]), "margen_arriba_mm": r.choice([0, 0, 10]),
               "margen_izquierda_mm": r.choice([0, 0, 15]),
               "planchas": [{"ancho": r.randint(700, 1200), "largo": r.randint(500, 700),
                             "corte_banda": r.choice([0, 20, 30])} for _ in range(r.randint(1, 2))]}
    return {"piezas": piezas, "materiales": {"FL5IN": ajustes}, "opciones": {"esfuerzo": r.choice(["rapido", "normal"])}}


def caso_real(r: random.Random) -> dict:
    medidas = [(r.randrange(200, 2400, 10), r.randrange(200, 2200, 10)) for _ in range(r.randint(3, 60))]
    total = r.randint(20, 400)
    piezas = []
    puestas = 0
    i = 0
    while puestas < total:
        a, l = medidas[i % len(medidas)]
        c = min(total - puestas, r.randint(1, 20))
        piezas.append({"item": str(i + 1), "material": "FL4IN", "cantidad": c, "ancho": a, "largo": l,
                       "clase": r.choice(["", "", "FLOAT PR TEMP"])})
        puestas += c
        i += 1
    preset = r.choice(["corte_certo", "corte_certo", "lucas"])
    return {"preset": preset, "piezas": piezas, "opciones": {"esfuerzo": r.choice(["rapido", "rapido", "normal"])}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--casos", type=int, default=500)
    parser.add_argument("--semilla", type=int, default=1)
    args = parser.parse_args(argv)
    r = random.Random(args.semilla)
    salida = RAIZ / "salida" / "estres"
    fallas = 0
    tiempos = {"chico": [], "real": []}
    for n in range(1, args.casos + 1):
        clase = "real" if r.random() < 0.25 else "chico"
        entrada = caso_real(r) if clase == "real" else caso_chico(r)
        entrada.update({"proyecto": {"codigo": f"ESTRES-{args.semilla}-{n}"}, "fecha": "2026-10-25 00:00:00"})
        t0 = time.perf_counter()
        res = optimizar(entrada)
        tiempos[clase].append(time.perf_counter() - t0)
        if not res["verificado"]:
            fallas += 1
            salida.mkdir(parents=True, exist_ok=True)
            ruta = salida / f"falla_{args.semilla}_{n}.json"
            ruta.write_text(json.dumps(entrada, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"caso {n} ({clase}): FALLÓ EL VALIDADOR — {res['validacion'][:2]} — guardado en {ruta}")
        elif n % 50 == 0:
            print(f"{n} casos, {fallas} fallas")
    for clase, ts in tiempos.items():
        if ts:
            print(f"{clase}: {len(ts)} casos, promedio {sum(ts) / len(ts):.2f} s, máximo {max(ts):.2f} s")
    print(f"Listo: {args.casos} casos, {fallas} fallaron el validador")
    return 1 if fallas else 0


if __name__ == "__main__":
    raise SystemExit(main())
