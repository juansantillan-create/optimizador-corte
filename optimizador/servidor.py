"""La interfaz local: un servidor en 127.0.0.1 (puerto 8520 o el siguiente libre) que sirve la
página del optimizador y su API. Nada sale de la PC; no usa internet.

    python -m optimizador servidor [--puerto 8520] [--no-abrir]

Lo arranca `Abrir_Optimizador.bat`. Cerrar esa ventana apaga el programa.
"""

from __future__ import annotations

import base64
import json
import re
import socket
import threading
import time
import uuid
import webbrowser
from collections import OrderedDict
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import __version__, exportar, importadores, informe
from .api import armar_stocks, armar_tipos, leer_piezas, optimizar
from .configuracion import CAMPOS_EDITABLES, CARPETA_CONFIG, Catalogo, RAIZ, todos_los_presets

WEB = Path(__file__).resolve().parent / "web"
CARPETA_PROYECTOS = RAIZ / "proyectos"
PUERTO = 8520
OCUPADOS = {8080, 8090, 8501, 8502}  # ya usados en la PC de la oficina (CLAUDE.md)
MAX_RESULTADOS = 15


# ------------------------------------------------------------------ cálculos en curso
class Calculo:
    def __init__(self, entrada: dict):
        self.id = uuid.uuid4().hex[:12]
        self.entrada = entrada
        self.estado = "calculando"
        self.progreso: dict = {}
        self.resultado: dict | None = None
        self.error: str | None = None
        self.inicio = time.time()
        self.fin: float | None = None
        self.cancelado = threading.Event()

    def correr(self, catalogo: Catalogo) -> None:
        def progreso(**datos):
            self.progreso = {k: v for k, v in datos.items() if isinstance(v, (int, float, str))}

        try:
            self.resultado = optimizar(self.entrada, progreso=progreso,
                                       cancelar=self.cancelado.is_set, catalogo=catalogo)
            self.estado = "cancelado" if self.cancelado.is_set() else "listo"
        except Exception as exc:  # se muestra en la pantalla, no se pierde
            self.error = f"{type(exc).__name__}: {exc}"
            self.estado = "error"
        self.fin = time.time()

    def avance(self) -> float:
        """Avance total (0 a 1): materiales terminados + lo que va del actual."""
        p = self.progreso
        if self.estado != "calculando":
            return 1.0
        total = max(int(p.get("materiales", 1)), 1)
        actual = max(int(p.get("numero_material", 1)), 1)
        return min(0.99, ((actual - 1) + float(p.get("avance", 0.0))) / total)

    def a_dict(self) -> dict:
        ahora = self.fin or time.time()
        transcurrido = ahora - self.inicio
        avance = self.avance()
        estimado = transcurrido / avance if avance > 0.03 else None
        datos = {"id": self.id, "estado": self.estado, "progreso": self.progreso,
                 "avance": round(avance, 3), "segundos": round(transcurrido, 1),
                 "estimado": round(estimado, 1) if estimado else None, "error": self.error}
        if self.resultado is not None:
            datos["resumen"] = [{k: m.get(k) for k in ("codigo", "descripcion", "piezas", "planchas",
                                                       "layouts", "aprovechamiento", "perdida")}
                                for m in self.resultado["materiales"]]
            datos["verificado"] = self.resultado.get("verificado")
        return datos


def puerto_libre(desde: int = PUERTO, hasta: int = PUERTO + 30) -> int:
    for puerto in range(desde, hasta):
        if puerto in OCUPADOS:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", puerto))
                return puerto
            except OSError:
                continue
    raise RuntimeError(f"no hay ningún puerto libre entre {desde} y {hasta}")


def _nombre_archivo(texto: str) -> str:
    limpio = re.sub(r"[^A-Za-z0-9_.+-]+", "_", texto.strip())[:60].strip("._")
    return limpio or "proyecto"


# ------------------------------------------------------------------------- la app
def crear_app(carpeta_config: Path | None = None, carpeta_proyectos: Path | None = None) -> FastAPI:
    app = FastAPI(title="Optimizador de corte Cristalux", version=__version__, docs_url=None, redoc_url=None)
    catalogo = Catalogo(carpeta_config or CARPETA_CONFIG)
    proyectos = Path(carpeta_proyectos or CARPETA_PROYECTOS)
    calculos: "OrderedDict[str, Calculo]" = OrderedDict()
    cerrojo = threading.Lock()

    def ruta_locales() -> Path:
        return catalogo.carpeta / "local" / "materiales.json"

    def leer_locales() -> dict:
        return catalogo.ajustes_locales()

    def guardar_locales(datos: dict) -> None:
        ruta = ruta_locales()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        tmp = ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(ruta)

    def calculo(id_: str) -> Calculo:
        c = calculos.get(id_)
        if c is None:
            raise HTTPException(404, "ese cálculo ya no está (se guardan los últimos 15)")
        return c

    app.mount("/web", StaticFiles(directory=WEB), name="web")

    @app.get("/", response_class=HTMLResponse)
    def inicio():
        return FileResponse(WEB / "index.html")

    @app.get("/api/estado")
    def estado():
        return {"version": __version__,
                "presets": {k: {"nombre": v["nombre"], "descripcion": v.get("descripcion", "")}
                            for k, v in todos_los_presets().items()}}

    # ---------------------------------------------------------------- materiales
    @app.get("/api/materiales")
    def materiales():
        locales = leer_locales()
        return [{"codigo": m.codigo, "descripcion": m.descripcion, "color": m.color,
                 "espesor_mm": m.espesor_mm,
                 "planchas": [f"{p.ancho}×{p.largo}" for p in m.planchas],
                 "ajustado": m.codigo in locales} for m in catalogo.lista()]

    @app.get("/api/materiales/{codigo}")
    def material(codigo: str, preset: str = "corte_certo"):
        codigo = codigo.upper()
        try:
            base = catalogo.material(codigo, preset, usar_locales=False)
            actual = catalogo.material(codigo, preset)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        from .api import config_material
        datos = config_material(actual)
        datos.update({"codigo": actual.codigo, "descripcion": actual.descripcion, "color": actual.color,
                      "avisos": actual.avisos,
                      "base": {**config_material(base), "descripcion": base.descripcion, "color": base.color},
                      "locales": leer_locales().get(codigo, {}),
                      "en_hojas_csv": codigo in catalogo.materiales})
        return datos

    @app.put("/api/materiales/{codigo}")
    def guardar_material(codigo: str, cambios: dict = Body(...)):
        """Guarda ajustes de un material en esta PC (`config/local/materiales.json`)."""
        codigo = codigo.upper()
        permitidos = CAMPOS_EDITABLES | {"planchas_habilitadas", "comercial"}
        desconocidos = set(cambios) - permitidos
        if desconocidos:
            raise HTTPException(400, f"campos desconocidos: {', '.join(sorted(desconocidos))}")
        with cerrojo:
            datos = leer_locales()
            datos[codigo] = {**datos.get(codigo, {}), **cambios}
            guardar_locales(datos)
        return {"ok": True, "locales": datos[codigo]}

    @app.delete("/api/materiales/{codigo}/locales")
    def borrar_ajustes(codigo: str):
        codigo = codigo.upper()
        with cerrojo:
            datos = leer_locales()
            quitado = datos.pop(codigo, None)
            guardar_locales(datos)
        return {"ok": True, "habia": quitado is not None}

    # ------------------------------------------------------------------ importar
    @app.post("/api/importar/texto")
    def importar_texto(cuerpo: dict = Body(...)):
        return importadores.desde_texto(cuerpo.get("texto", "")).a_dict()

    @app.post("/api/importar/archivo")
    def importar_archivo(cuerpo: dict = Body(...)):
        try:
            datos = base64.b64decode(cuerpo.get("datos", ""))
            imp = importadores.importar_archivo(datos, cuerpo.get("nombre", ""), cuerpo.get("interfaz"))
        except Exception as exc:
            raise HTTPException(400, f"no se pudo leer el archivo: {exc}")
        return imp.a_dict()

    # ------------------------------------------------------------ revisar y calcular
    @app.post("/api/revisar")
    def revisar(entrada: dict = Body(...)):
        """Lo que conviene mirar antes de calcular: materiales que no están en la configuración,
        planchas supuestas, piezas que no entran o con medidas raras."""
        preset = entrada.get("preset") or "corte_certo"
        piezas, errores, avisos = leer_piezas(entrada.get("piezas") or [])
        por_material: dict[str, list] = {}
        for pz in piezas:
            por_material.setdefault(pz.material, []).append(pz)
        for codigo, lista in por_material.items():
            mat = catalogo.material(codigo, preset, (entrada.get("materiales") or {}).get(codigo))
            avisos += mat.avisos
            stocks, err = armar_stocks(mat)
            errores += err
            if not stocks:
                errores.append(f"{codigo}: no tiene planchas; no se va a calcular")
                continue
            _, err, av = armar_tipos(mat, lista, stocks)
            errores += err
            avisos += av
            for pz in lista:
                if min(pz.ancho, pz.largo) < 50:
                    avisos.append(f"ítem {pz.item}: medida muy chica ({pz.ancho} × {pz.largo} mm): ¿está en mm?")
        vistos: dict[str, int] = {}
        for pz in piezas:
            vistos[pz.item] = vistos.get(pz.item, 0) + 1
        repetidos = [i for i, n in vistos.items() if n > 1]
        if repetidos:
            avisos.append(f"ítems repetidos: {', '.join(repetidos[:10])}")
        return {"errores": errores, "avisos": avisos, "piezas": sum(p.cantidad for p in piezas),
                "materiales": list(por_material)}

    @app.post("/api/calcular")
    def calcular(entrada: dict = Body(...)):
        c = Calculo(entrada)
        with cerrojo:
            calculos[c.id] = c
            while len(calculos) > MAX_RESULTADOS:
                calculos.popitem(last=False)
        threading.Thread(target=c.correr, args=(catalogo,), daemon=True).start()
        return c.a_dict()

    @app.get("/api/calculo/{id_}")
    def estado_calculo(id_: str):
        return calculo(id_).a_dict()

    @app.post("/api/calculo/{id_}/cancelar")
    def cancelar(id_: str):
        c = calculo(id_)
        c.cancelado.set()
        return c.a_dict()

    def resultado(id_: str) -> dict:
        c = calculo(id_)
        if c.resultado is None:
            raise HTTPException(409, "el cálculo todavía no terminó" if c.estado == "calculando"
                                else f"el cálculo no dio resultado: {c.error}")
        return c.resultado

    @app.get("/api/calculo/{id_}/resultado.json")
    def resultado_json(id_: str):
        r = resultado(id_)
        nombre = _nombre_archivo(f"resultado_{r['proyecto']['codigo']}") + ".json"
        return JSONResponse(r, headers={"Content-Disposition": f'inline; filename="{nombre}"'})

    @app.get("/api/calculo/{id_}/informe.html", response_class=HTMLResponse)
    def informe_html(id_: str, modo: str = "detalle", coma: int = 0):
        if modo not in ("informe", "miniaturas", "detalle"):
            raise HTTPException(400, "modo: informe, miniaturas o detalle")
        return HTMLResponse(informe.html_resultado(resultado(id_), modo_impresion=modo, coma=bool(coma)))

    @app.get("/api/calculo/{id_}/consumo.csv")
    def consumo_csv(id_: str, coma: int = 0):
        r = resultado(id_)
        nombre = _nombre_archivo(f"consumo_{r['proyecto']['codigo']}") + ".csv"
        return Response(exportar.a_csv(r, coma=bool(coma)), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{nombre}"'})

    @app.get("/api/calculo/{id_}/consumo.xlsx")
    def consumo_xlsx(id_: str):
        r = resultado(id_)
        nombre = _nombre_archivo(f"consumo_{r['proyecto']['codigo']}") + ".xlsx"
        return Response(exportar.a_xlsx(r),
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f'attachment; filename="{nombre}"'})

    # ---------------------------------------------------------------- proyectos
    @app.get("/api/proyectos")
    def lista_proyectos():
        if not proyectos.exists():
            return []
        salida = []
        for ruta in sorted(proyectos.glob("*.json"), key=lambda r: r.stat().st_mtime, reverse=True):
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            salida.append({"archivo": ruta.name, "codigo": datos.get("proyecto", {}).get("codigo", ""),
                           "descripcion": datos.get("proyecto", {}).get("descripcion", ""),
                           "renglones": len(datos.get("piezas", [])),
                           "modificado": time.strftime("%d/%m/%Y %H:%M", time.localtime(ruta.stat().st_mtime))})
        return salida

    @app.get("/api/proyectos/{archivo}")
    def abrir_proyecto(archivo: str):
        ruta = proyectos / _nombre_archivo(archivo)
        if not ruta.exists():
            raise HTTPException(404, "no existe ese proyecto")
        return json.loads(ruta.read_text(encoding="utf-8"))

    @app.post("/api/proyectos")
    def guardar_proyecto(datos: dict = Body(...)):
        codigo = str((datos.get("proyecto") or {}).get("codigo") or "").strip()
        if not codigo:
            raise HTTPException(400, "el proyecto necesita un código para guardarlo")
        proyectos.mkdir(parents=True, exist_ok=True)
        ruta = proyectos / (_nombre_archivo(codigo) + ".json")
        tmp = ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(ruta)
        return {"ok": True, "archivo": ruta.name}

    return app


def servir(puerto: int | None = None, abrir: bool = True) -> None:
    import uvicorn

    puerto = puerto_libre(puerto or PUERTO)
    url = f"http://127.0.0.1:{puerto}/"
    print(f"Optimizador de corte {__version__} andando en {url}")
    print("Para apagarlo, cerrá esta ventana.")
    if abrir:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(crear_app(), host="127.0.0.1", port=puerto, log_level="warning")
