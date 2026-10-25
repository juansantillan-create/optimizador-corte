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
import re
import unicodedata
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
    inventado = es_inventado(casos)
    if inventado:
        mostrar("aviso: estos datos dicen ser INVENTADOS (caso de juguete); los números no valen como validación")
    trabajos, cobertura = comparar.preparar(casos, catalogo)
    c = cobertura
    mostrar(f"Presupuestos: {c['presupuestos']} · con pinta de leyenda: {c['con_pinta']} · leídos: {c['leidos']} · "
            f"líneas: {c['lineas']} · relacionadas: {c['relacionadas']} · pasan el control: {c['control_ok']}")
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "cobertura.json").write_text(json.dumps(cobertura, ensure_ascii=False, indent=1), encoding="utf-8")
    filas = comparar.correr(trabajos, salida / f"resultados_{opciones.esfuerzo}.jsonl", opciones, catalogo, mostrar)
    eleccion = comparar.calibrar(filas)
    prueba = comparar.informe_prueba(filas, eleccion)
    texto = comparar.markdown(cobertura, eleccion, prueba, opciones, str(carpeta_datos), inventado)
    (salida / "resumen.md").write_text(texto + "\n", encoding="utf-8")
    (salida / "resumen.json").write_text(json.dumps({"eleccion": eleccion, "prueba": prueba},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    montajes = {}
    for f in filas:
        if f["hipotesis"] == eleccion.get(f["grupo"], {}).get("hipotesis", "H0"):
            ruta = salida / "montajes" / comparar.nombre_montajes(f["numero"], f["material"], f["hipotesis"], f["esfuerzo"])
            if ruta.exists():
                montajes[f"{f['numero']}|{f['material']}"] = json.loads(ruta.read_text(encoding="utf-8"))
    corrida = f"{Path(casos.origen).name}|{opciones.esfuerzo}"
    pagina = revision.html(filas, eleccion, prueba, cobertura, montajes, corrida=corrida)
    (salida / "revision.html").write_text(pagina, encoding="utf-8")
    mostrar(f"Página de revisión: {salida / 'revision.html'}")
    if publicar and inventado:
        mostrar("No se copia la página a docs/validacion/: los datos son inventados")
    elif publicar:
        publica = revision.html(filas, eleccion, prueba, cobertura, montajes, publicable=True, corrida=corrida)
        sospechosas = palabras_sospechosas(publica, casos)
        if sospechosas:
            mostrar(f"No se copia la página a docs/validacion/: tiene {len(sospechosas)} palabras que salen de los "
                    f"textos libres del zip y podrían ser nombres (queda solo en salida/historico/)")
        elif len(publica.encode()) >= 5_000_000:
            mostrar("La página pesa más de 5 MB: queda solo en salida/historico/ (no va a git)")
        else:
            destino = RAIZ / "docs" / "validacion" / "revision.html"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(publica, encoding="utf-8")
            mostrar(f"Copiada a {destino} (sin los textos de las observaciones)")
    if docs and inventado:
        mostrar("No se actualiza docs/VALIDACION.md: los datos son inventados")
    elif docs:
        actualizar_validacion(texto)
        mostrar("docs/VALIDACION.md actualizado (sección 1)")
    mostrar(texto)
    return {"cobertura": cobertura, "eleccion": eleccion, "prueba": prueba}


def es_inventado(casos: datos.Casos) -> bool:
    """El caso de juguete (y cualquier dato de prueba) lo dice en su LEEME."""
    return bool(re.search(r"TODO INVENTADO|CASO DE JUGUETE", casos.leeme.upper()))


def _palabras(texto: str) -> set[str]:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().upper()
    return {p for p in re.findall(r"[A-Z]{4,}", t)}


def palabras_sospechosas(pagina: str, casos: datos.Casos) -> set[str]:
    """Control de nombres antes de publicar (brief §10.3): palabras de la página que también están en
    los textos libres del zip (observaciones, detalles) y que no son nuestras (no aparecen en el
    código del programa ni en las descripciones de los artículos). Tiene que dar vacío."""
    libres: set[str] = set()
    for fila in casos.presupuestos.values():
        for k, v in fila.items():
            if k not in ("numero", "fecha") and isinstance(v, str):
                libres |= _palabras(v)
    for lista in casos.renglones.values():
        for r in lista:
            libres |= _palabras(r.get("detalle") or "")
    for lista in casos.piezas.values():
        for p in lista:
            libres |= _palabras(p.get("detalle") or "")
    nuestras: set[str] = set()
    for fuente in (Path(__file__).parent.parent).rglob("*.py"):
        nuestras |= _palabras(fuente.read_text(encoding="utf-8"))
    for art in casos.articulos.values():
        nuestras |= _palabras(f"{art.get('codigo', '')} {art.get('descripcion', '')} {art.get('familia', '')}")
    for mat in Catalogo(usar_locales=False).materiales.values():
        nuestras |= _palabras(f"{mat.codigo} {mat.descripcion}")
    texto = re.sub(r"<[^>]+>", " ", pagina)
    return (_palabras(texto) & libres) - nuestras


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
