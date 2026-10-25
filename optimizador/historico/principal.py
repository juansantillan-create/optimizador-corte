"""`python -m optimizador historico`: la validación histórica de punta a punta.

    python -m optimizador historico                       # muestra de 50 casos (para empezar)
    python -m optimizador historico --todo                # todos los casos (corre en tandas)
    python -m optimizador historico --datos otra/carpeta  # por defecto, datos/casos
    python -m optimizador historico --todo --docs         # además, actualiza docs/VALIDACION.md
    python -m optimizador historico --todo --publicar     # además, copia la página a docs/validacion/

Lo calculado se guarda en `salida/historico/` (no va a git) a medida que sale: si se corta, se
vuelve a correr el mismo comando y sigue desde donde quedó.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..configuracion import RAIZ, Catalogo
from . import comparar, datos, revision

MARCA_INICIO = "<!-- HISTORICO: lo escribe `python -m optimizador historico --docs` -->"
MARCA_FIN = "<!-- /HISTORICO -->"


def ejecutar(carpeta_datos: Path, salida: Path, opciones: comparar.Opciones, docs: bool = False,
             publicar: bool = False, mostrar=print) -> dict:
    catalogo = Catalogo(usar_locales=False)
    casos = datos.leer(carpeta_datos)
    for d in casos.diferencias:
        mostrar(f"aviso (contrato): {d}")
    if not casos.presupuestos:
        mostrar(f"No hay casos en {carpeta_datos}. Ver docs/CONTRATO_DATOS.md.")
        return {}
    trabajos, cobertura = comparar.preparar(casos, catalogo)
    c = cobertura
    mostrar(f"Presupuestos: {c['presupuestos']} · con pinta de leyenda: {c['con_pinta']} · leídos: {c['leidos']} · "
            f"líneas: {c['lineas']} · relacionadas: {c['relacionadas']} · pasan el control: {c['control_ok']}")
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "cobertura.json").write_text(json.dumps(cobertura, ensure_ascii=False, indent=1), encoding="utf-8")
    filas = comparar.correr(trabajos, salida / f"resultados_{opciones.esfuerzo}.jsonl", opciones, catalogo, mostrar)
    eleccion = comparar.calibrar(filas)
    prueba = comparar.informe_prueba(filas, eleccion)
    texto = comparar.markdown(cobertura, eleccion, prueba, opciones, str(carpeta_datos))
    (salida / "resumen.md").write_text(texto + "\n", encoding="utf-8")
    (salida / "resumen.json").write_text(json.dumps({"eleccion": eleccion, "prueba": prueba},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    montajes = {}
    for f in filas:
        if f["hipotesis"] == eleccion.get(f["grupo"], {}).get("hipotesis", "H0"):
            ruta = salida / "montajes" / comparar.nombre_montajes(f["numero"], f["material"], f["hipotesis"], f["esfuerzo"])
            if ruta.exists():
                montajes[f"{f['numero']}|{f['material']}"] = json.loads(ruta.read_text(encoding="utf-8"))
    pagina = revision.html(filas, eleccion, prueba, cobertura, montajes)
    (salida / "revision.html").write_text(pagina, encoding="utf-8")
    mostrar(f"Página de revisión: {salida / 'revision.html'}")
    if publicar:
        publica = revision.html(filas, eleccion, prueba, cobertura, montajes, publicable=True)
        if len(publica.encode()) < 5_000_000:
            destino = RAIZ / "docs" / "validacion" / "revision.html"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(publica, encoding="utf-8")
            mostrar(f"Copiada a {destino} (sin los textos crudos de las observaciones)")
        else:
            mostrar("La página pesa más de 5 MB: queda solo en salida/historico/ (no va a git)")
    if docs:
        actualizar_validacion(texto)
        mostrar("docs/VALIDACION.md actualizado (sección 1)")
    mostrar(texto)
    return {"cobertura": cobertura, "eleccion": eleccion, "prueba": prueba}


def actualizar_validacion(texto: str, ruta: Path | None = None) -> None:
    ruta = ruta or RAIZ / "docs" / "VALIDACION.md"
    contenido = ruta.read_text(encoding="utf-8")
    bloque = f"{MARCA_INICIO}\n{texto}\n{MARCA_FIN}"
    if MARCA_INICIO in contenido and MARCA_FIN in contenido:
        antes = contenido.split(MARCA_INICIO)[0]
        despues = contenido.split(MARCA_FIN, 1)[1]
        contenido = antes + bloque + despues
    else:
        contenido = contenido.replace("## 1. Contra Corte Certo (casos históricos)\n",
                                      "## 1. Contra Corte Certo (casos históricos)\n\n" + bloque + "\n", 1)
    ruta.write_text(contenido, encoding="utf-8")
