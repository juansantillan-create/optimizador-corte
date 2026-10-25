"""Línea de comandos.

    python -m optimizador calcular proyecto.json [-o resultado.json] [--preset lucas] [--esfuerzo rapido]
    python -m optimizador servidor [--puerto 8520] [--no-abrir]
    python -m optimizador materiales [CODIGO]
    python -m optimizador banco [--esfuerzo rapido] [--filtro CP-] [--guardar]
    python -m optimizador historico [--todo] [--datos datos/casos] [--docs] [--publicar]
    python -m optimizador --version

`calcular` lee la entrada (JSON de `docs/API.md`), calcula y escribe el resultado en JSON. Al final
muestra un resumen por material. Devuelve 0 si el resultado pasó el validador, 1 si no, y 2 si la
entrada no se pudo leer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def _resumen(res: dict) -> str:
    lineas = [f"Proyecto {res['proyecto']['codigo']} {res['proyecto']['descripcion']} — "
              f"preset: {res['preset_nombre']}"]
    for m in res["materiales"]:
        lineas.append(
            f"  {m['codigo']:<10} {m['piezas']:>5} piezas  {m['m2_piezas']:.6f} m²  "
            f"{m['layouts']:>3} montajes  {m['planchas']:>4} planchas  {m['m2_planchas']:g} m²  "
            f"aprov. {m['aprovechamiento']:.2f} %  (mínimo teórico {m.get('minimo_teorico_planchas', '-')})")
        for e in m["errores"]:
            lineas.append(f"     ERROR: {e}")
        for a in m["avisos"]:
            lineas.append(f"     aviso: {a}")
    for e in res.get("errores", []):
        lineas.append(f"  ERROR: {e}")
    for a in res.get("avisos", []):
        lineas.append(f"  aviso: {a}")
    if res.get("completo") is False:
        lineas.append("RESULTADO INCOMPLETO: hay piezas que no se calcularon (ver los errores de arriba)")
    if res.get("verificado"):
        lineas.append("Validador: OK")
    else:
        lineas.append("Validador: FALLÓ")
        lineas += [f"  - {e}" for e in res.get("validacion", [])]
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m optimizador",
                                     description="Optimizador de corte de vidrio (Cristalux)")
    parser.add_argument("--version", action="version", version=f"optimizador-corte {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)
    c = sub.add_parser("calcular", help="calcular un proyecto (JSON)")
    c.add_argument("entrada", type=Path)
    c.add_argument("-o", "--salida", type=Path, help="dónde guardar el resultado (JSON)")
    c.add_argument("--html", type=Path, help="guardar también el informe y los montajes (HTML)")
    c.add_argument("--coma", action="store_true", help="en el HTML, coma decimal en lugar de punto")
    c.add_argument("--preset", help="corte_certo (por defecto), lucas, H0, H1, H2")
    c.add_argument("--esfuerzo", choices=["rapido", "normal", "maximo"])
    c.add_argument("--silencioso", action="store_true", help="no mostrar el progreso")
    m = sub.add_parser("materiales", help="listar los materiales configurados")
    m.add_argument("codigo", nargs="?")
    s = sub.add_parser("servidor", help="abrir la interfaz en el navegador (127.0.0.1:8520)")
    s.add_argument("--puerto", type=int, default=8520)
    s.add_argument("--no-abrir", action="store_true", help="no abrir el navegador")
    h = sub.add_parser("historico", help="validación contra los casos viejos de Corte Certo")
    h.add_argument("--datos", type=Path, help="carpeta o zip de casos (por defecto datos/casos)")
    h.add_argument("--salida", type=Path, help="dónde guardar (por defecto salida/historico)")
    h.add_argument("--muestra", type=int, default=50, help="cuántos casos (por defecto 50)")
    h.add_argument("--todo", action="store_true", help="todos los casos")
    h.add_argument("--esfuerzo", choices=["rapido", "normal", "maximo"], default="normal")
    h.add_argument("--docs", action="store_true", help="actualizar docs/VALIDACION.md")
    h.add_argument("--publicar", action="store_true", help="copiar la página a docs/validacion/")
    b = sub.add_parser("banco", help="correr el banco de pruebas sintético (sirve de benchmark)")
    b.add_argument("--esfuerzo", choices=["rapido", "normal", "maximo"], default="normal")
    b.add_argument("--filtro", default="", help="solo los casos cuyo nombre contiene esto")
    b.add_argument("--generar", action="store_true", help="volver a generar los casos")
    b.add_argument("--guardar", action="store_true", help="guardar los resultados como esperados")
    b.add_argument("--salida", type=Path, help="guardar los resultados en este JSON")
    args = parser.parse_args(argv)

    if args.comando == "servidor":
        from .servidor import servir
        servir(args.puerto, abrir=not args.no_abrir)
        return 0

    if args.comando == "historico":
        from .configuracion import RAIZ
        from .historico import comparar, principal
        opciones = comparar.Opciones(esfuerzo=args.esfuerzo, muestra=None if args.todo else args.muestra)
        res = principal.ejecutar(args.datos or RAIZ / "datos" / "casos", args.salida or RAIZ / "salida" / "historico",
                                 opciones, docs=args.docs, publicar=args.publicar)
        return 0 if res else 2

    if args.comando == "banco":
        from . import banco
        if args.generar:
            rutas = banco.generar()
            print(f"{len(rutas)} casos generados en {banco.CARPETA}")
        datos = banco.correr(esfuerzo=args.esfuerzo, filtro=args.filtro)
        datos["resumen"] = banco.resumen(datos)
        print(json.dumps(datos["resumen"], ensure_ascii=False, indent=1))
        print(f"Máquina: {datos['maquina']}")
        peores = banco.comparar_con_esperado(datos)
        for linea in peores:
            print(f"EMPEORÓ: {linea}")
        if args.salida:
            args.salida.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        if args.guardar:
            (banco.CARPETA / "esperado.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1),
                                                         encoding="utf-8")
            print("Resultados guardados como esperados.")
        return 1 if peores else 0

    if args.comando == "materiales":
        from .configuracion import Catalogo
        cat = Catalogo()
        for mat in cat.lista():
            if args.codigo and mat.codigo != args.codigo.upper():
                continue
            medidas = ", ".join(f"{p.ancho}×{p.largo} (banda {p.corte_banda})" for p in mat.planchas)
            print(f"{mat.codigo:<12} {mat.descripcion:<42} {medidas}")
        return 0

    from .api import optimizar
    try:
        entrada = json.loads(args.entrada.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"No se pudo leer {args.entrada}: {exc}", file=sys.stderr)
        return 2
    if args.preset:
        entrada["preset"] = args.preset
    if args.esfuerzo:
        entrada.setdefault("opciones", {})["esfuerzo"] = args.esfuerzo

    def progreso(**kw):
        if not args.silencioso:
            fase = kw.get("fase", "")
            extra = ""
            if "iteracion" in kw:
                extra = f" {kw['iteracion']}/{kw['de']}"
            elif "planchas" in kw:
                extra = f" — mejor hasta ahora: {kw['planchas']} planchas, {kw['montajes']} montajes"
            print(f"\r[{kw.get('material', '')}] {fase}{extra}".ljust(90), end="", file=sys.stderr)

    try:
        res = optimizar(entrada, progreso=progreso)
    except ValueError as exc:
        print(f"\nError en la entrada: {exc}", file=sys.stderr)
        return 2
    if not args.silencioso:
        print(file=sys.stderr)
    texto = json.dumps(res, ensure_ascii=False, indent=1)
    if args.salida:
        args.salida.write_text(texto, encoding="utf-8")
        print(f"Resultado guardado en {args.salida}")
    if args.html:
        from .informe import html_resultado
        args.html.write_text(html_resultado(res, coma=args.coma), encoding="utf-8")
        print(f"Informe guardado en {args.html} (abrilo con el navegador; se imprime en A4 apaisada)")
    print(_resumen(res))
    if not res.get("verificado"):
        return 1
    return 0 if res.get("completo", True) else 2


if __name__ == "__main__":
    sys.exit(main())
