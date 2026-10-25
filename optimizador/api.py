"""La función `optimizar()`: recibe la entrada (dict, el mismo JSON de la CLI) y devuelve el
resultado (dict). Sin estado global, para que el orquestador la pueda importar.

Formato de entrada y salida: `docs/API.md`.
"""

from __future__ import annotations

import datetime as dt
import math
from decimal import ROUND_HALF_UP, Decimal
import re
from collections import OrderedDict

from . import __version__, colores
from .configuracion import Catalogo, todos_los_presets
from .modelo import Material, Pieza
from .motor import arbol
from .motor.calculo import ResultadoMaterial, Stock, Tipo, calcular


# --------------------------------------------------------------------------- entrada
MEDIDA_SOSPECHOSA_MM = 50  # una pieza con un lado de menos de 5 cm probablemente no está en mm
def _entero(valor, campo: str, avisos: list[str], donde: str) -> int | None:
    """Medidas y cantidades: enteros. Un decimal se redondea con aviso; lo que no es número, error."""
    if valor is None or valor == "":
        return None
    texto = str(valor).strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        texto = texto.replace(".", "")  # "1.200" es 1200 (punto de miles), como al pegar desde Excel
    elif "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")  # "1.200,5"
    try:
        x = float(texto.replace(",", "."))
    except ValueError:
        return None
    if not math.isfinite(x):
        return None
    if x != int(x):
        avisos.append(f"{donde}: {campo} {valor} no es entero, se redondea a {round(x)}")
    return int(round(x))


def tiene_pulido_recto(clase: str) -> bool:
    """La clase de Metrix lleva pulido recto si tiene la palabra "PR" (ej. "FLOAT PR TEMP")."""
    return bool(re.search(r"(^|[^A-Z0-9])PR([^A-Z0-9]|$)", (clase or "").upper()))


def leer_piezas(lista: list[dict]) -> tuple[list[Pieza], list[str], list[str]]:
    """Convierte la lista de la entrada en piezas. Devuelve (piezas, errores, avisos)."""
    piezas: list[Pieza] = []
    errores: list[str] = []
    avisos: list[str] = []
    for n, d in enumerate(lista, start=1):
        item = str(d.get("item") or n).strip()
        donde = f"renglón {n} (ítem {item})"
        material = str(d.get("material") or "").strip().upper()
        cantidad = _entero(d.get("cantidad"), "cantidad", avisos, donde)
        ancho = _entero(d.get("ancho"), "ancho", avisos, donde)
        largo = _entero(d.get("largo"), "largo", avisos, donde)
        problemas = []
        if not material:
            problemas.append("falta el material")
        if cantidad is None:
            problemas.append("cantidad vacía o no numérica")
        elif cantidad <= 0:
            problemas.append(f"cantidad {cantidad}")
        for nombre, valor in (("ancho", ancho), ("largo", largo)):
            if valor is None:
                problemas.append(f"{nombre} vacío o no numérico")
            elif valor <= 0:
                problemas.append(f"{nombre} {valor} mm")
        if problemas:
            errores.append(f"{donde}: {', '.join(problemas)}; no se calcula")
            continue
        if min(ancho, largo) < MEDIDA_SOSPECHOSA_MM:
            avisos.append(f"{donde}: medida muy chica ({ancho} × {largo} mm): ¿está en mm?")
        rota = d.get("rota")
        if isinstance(rota, str):
            rota = rota.strip().lower() in ("si", "sí", "s", "true", "1", "x")
        clase = str(d.get("clase") or "")
        pulido = d.get("pulido_recto")
        pulido = tiene_pulido_recto(clase) if pulido is None else bool(pulido)
        sobremedida = _entero(d.get("sobremedida_mm"), "sobremedida", avisos, donde) or 0
        piezas.append(Pieza(item=item, material=material, cantidad=cantidad, ancho=ancho,
                            largo=largo, rota=rota, descripcion=str(d.get("descripcion") or ""),
                            origen=d.get("origen"), sobremedida_mm=sobremedida,
                            pulido_recto=pulido))
    vistos: dict[str, int] = {}
    for pz in piezas:
        vistos[pz.item] = vistos.get(pz.item, 0) + 1
    repetidos = [i for i, n in vistos.items() if n > 1]
    if repetidos:
        avisos.append(f"ítems repetidos: {', '.join(repetidos[:10])}" + (" …" if len(repetidos) > 10 else "")
                      + " (en los dibujos no se van a poder distinguir)")
    return piezas, errores, avisos


# ------------------------------------------------------------------ tipos y planchas
def colocable_sola(dx: int, dy: int, W: int, H: int, s: int, d: int) -> bool:
    """¿Se puede cortar la pieza sola en la plancha útil W × H respetando el destaque? Lo que
    sobra a la derecha (W − dx) y arriba (H − dy) tiene que medir 0 o al menos d."""
    if dx > W or dy > H:
        return False
    if d <= 0:
        return True
    rx, ry = W - dx, H - dy
    if 0 < rx < d or 0 < ry < d:
        return False
    if rx > 0 and ry > 0:
        # Uno de los dos órdenes de corte deja un pedazo del ancho (o alto) de la pieza.
        return dx + s >= d or dy + s >= d
    return True


def armar_tipos(mat: Material, piezas: list[Pieza], stocks: list[Stock]):
    """Junta las piezas iguales en tipos. Devuelve (tipos, errores, avisos)."""
    errores: list[str] = []
    avisos: list[str] = []
    grupos: "OrderedDict[tuple, Tipo]" = OrderedDict()
    for pz in piezas:
        extra = pz.sobremedida_mm + (mat.sobremedida_pulido_mm if pz.pulido_recto else 0)
        a_m2, l_m2 = pz.ancho + extra, pz.largo + extra  # medida "cargada" (cuenta en los m²)
        a_c, l_c = a_m2 + mat.constante_ancho_mm, l_m2 + mat.constante_largo_mm  # se acomoda
        rota = mat.rotacion if pz.rota is None else bool(pz.rota)
        if mat.textura != "sin":
            if pz.rota:
                avisos.append(f"ítem {pz.item}: el material tiene veta ({mat.textura}), la pieza no se gira")
            rota = False
            orients = ((l_c, a_c),) if mat.textura == "horizontal" else ((a_c, l_c),)
        elif rota:
            orients = ((a_c, l_c),) if a_c == l_c else ((a_c, l_c), (l_c, a_c))
        else:
            orients = ((a_c, l_c),)
        entra = [o for o in orients if any(o[0] <= st.ancho and o[1] <= st.largo for st in stocks)]
        cortable = [o for o in entra if any(colocable_sola(o[0], o[1], st.ancho, st.largo,
                                                           mat.separacion_piezas_mm,
                                                           mat.destaque_min_mm) for st in stocks)]
        if entra and not cortable:
            errores.append(f"ítem {pz.item}: {a_c} × {l_c} entra en la plancha de {mat.codigo}, "
                           f"pero quedaría una tira de sobrante de menos de {mat.destaque_min_mm} mm "
                           "(destaque mínimo) que no se puede separar; no se calcula")
            continue
        entra = cortable
        if not entra:
            medidas = ", ".join(f"{st.ancho} × {st.largo}" for st in stocks)
            girada = (l_c, a_c)
            extra_txt = ""
            if not rota and any(girada[0] <= st.ancho and girada[1] <= st.largo for st in stocks):
                extra_txt = " (entraría girada, pero el material no permite girarla)"
            errores.append(f"ítem {pz.item}: no entra en ninguna plancha de {mat.codigo}: "
                           f"{a_c} × {l_c} (plancha útil {medidas}){extra_txt}; no se calcula")
            continue
        if mat.destaque_min_mm > 0 and min(a_c, l_c) < mat.destaque_min_mm:
            avisos.append(f"ítem {pz.item}: mide menos que el destaque mínimo "
                          f"({mat.destaque_min_mm} mm): puede ser difícil de separar")
        clave = (a_m2, l_m2, tuple(sorted(entra)))
        if clave not in grupos:
            grupos[clave] = Tipo(indice=len(grupos), ancho=a_m2, largo=l_m2, ancho_corte=a_c,
                                 largo_corte=l_c, cantidad=0, rota=len(entra) > 1 or rota,
                                 orientaciones=tuple(entra),
                                 medida_presupuesto=(pz.ancho, pz.largo))
        tipo = grupos[clave]
        tipo.cantidad += pz.cantidad
        tipo.items.append((pz.item, pz.cantidad))
        tipo.mm2_presupuesto += pz.ancho * pz.largo * pz.cantidad
    return list(grupos.values()), errores, avisos


def armar_stocks(mat: Material) -> tuple[list[Stock], list[str]]:
    stocks: list[Stock] = []
    errores: list[str] = []
    for i, pl in enumerate(mat.planchas):
        if not pl.habilitada:
            continue
        ancho, largo = mat.util(pl)
        if ancho <= 0 or largo <= 0:
            errores.append(f"{mat.codigo}: la plancha {pl.ancho} × {pl.largo} queda sin medida útil "
                           f"({ancho} × {largo}) con la banda y los márgenes")
            continue
        stocks.append(Stock(i, ancho, largo, ancho * largo / 1e6))
    return stocks, errores


# --------------------------------------------------------------------------- salida
def _redondear(x: float, decimales: int) -> float:
    """Redondeo "de toda la vida" (76,925 → 76,93), no el "al par" de Python, que es el que
    probablemente usa Corte Certo. Se redondea el número tal como se escribe (repr), así 76,925 no
    se vuelve 76,92 por cómo se guarda en binario."""
    paso = Decimal(1).scaleb(-decimales)
    return float(Decimal(repr(x)).quantize(paso, rounding=ROUND_HALF_UP))


def config_material(mat: Material) -> dict:
    return {
        "color": mat.color,
        "separacion_piezas_mm": mat.separacion_piezas_mm,
        "destaque_min_mm": mat.destaque_min_mm,
        "genera_retazo": mat.genera_retazo,
        "retazo_ancho_min_mm": mat.retazo_ancho_min_mm,
        "retazo_largo_min_mm": mat.retazo_largo_min_mm,
        "usar_area_min": mat.usar_area_min,
        "retazo_area_min_m2": mat.retazo_area_min_m2,
        "rotacion": mat.rotacion,
        "textura": mat.textura,
        "constante_ancho_mm": mat.constante_ancho_mm,
        "constante_largo_mm": mat.constante_largo_mm,
        "margen_arriba_mm": mat.margen_arriba_mm,
        "margen_abajo_mm": mat.margen_abajo_mm,
        "margen_izquierda_mm": mat.margen_izquierda_mm,
        "margen_derecha_mm": mat.margen_derecha_mm,
        "corte_max_libre": mat.corte_max_libre,
        "corte_max_mm": mat.corte_max_mm,
        "sobremedida_pulido_mm": mat.sobremedida_pulido_mm,
        "espesor_mm": mat.espesor_mm,
        "peso_kg_m2": mat.peso_kg_m2,
        "planchas": [{"ancho": p.ancho, "largo": p.largo, "corte_banda": p.corte_banda,
                      "habilitada": p.habilitada, "supuesta": p.supuesta, "origen": p.origen}
                     for p in mat.planchas],
    }


def es_retazo(mat: Material, ancho: int, largo: int) -> bool:
    """Un sobrante es retazo si el material "genera retazo" y el sobrante llega a los mínimos.
    Con los mínimos en 0 (como en la captura de Corte Certo) no hay regla: todo es sobrante."""
    if not mat.genera_retazo:
        return False
    if mat.retazo_ancho_min_mm <= 0 and mat.retazo_largo_min_mm <= 0 and not mat.usar_area_min:
        return False
    chico, grande = sorted((ancho, largo))
    min_chico, min_grande = sorted((mat.retazo_ancho_min_mm, mat.retazo_largo_min_mm))
    if chico < min_chico or grande < min_grande:
        return False
    if mat.usar_area_min and ancho * largo / 1e6 < mat.retazo_area_min_m2:
        return False
    return chico > 0


def _montajes(mat: Material, res: ResultadoMaterial) -> list[dict]:
    s = res.separacion
    tipos = res.tipos
    salida = []
    for u in res.solucion.usos:
        st = res.stocks[u.stock]
        pl = mat.planchas[st.indice]
        piezas = []
        sobrantes = []
        area = 0
        for hoja, x, y in arbol.hojas(u.nodo):
            ancho, largo = hoja.ancho - s, hoja.alto - s
            if hoja.tipo == "pieza":
                t = tipos[hoja.pieza]
                # Girada = con el largo donde se cargó el ancho. Con veta la orientación la pone la
                # veta: no es "girada".
                girada = mat.textura == "sin" and (ancho, largo) != (t.ancho_corte, t.largo_corte)
                piezas.append({"tipo": t.indice + 1, "item": t.etiqueta, "x": x, "y": y,
                               "ancho": ancho, "largo": largo, "girada": girada})
                area += t.ancho * t.largo
            else:
                # Lo que sobra fuera de la plancha útil (por la separación) no se muestra.
                ancho = min(ancho, st.ancho - x)
                largo = min(largo, st.largo - y)
                if ancho > 0 and largo > 0:
                    sobrantes.append({"x": x, "y": y, "ancho": ancho, "largo": largo,
                                      "tipo": "retazo" if es_retazo(mat, ancho, largo) else "desperdicio"})
        cortes = [{"nivel": c.nivel, "vertical": c.vertical, "posicion": c.posicion,
                   "desde": c.desde, "hasta": c.hasta} for c in arbol.cortes(u.nodo, s)]
        salida.append({
            "repeticiones": u.repeticiones,
            "plancha": {"ancho": st.ancho, "largo": st.largo, "hoja_ancho": pl.ancho,
                        "hoja_largo": pl.largo, "corte_banda": pl.corte_banda, "supuesta": pl.supuesta},
            "piezas": piezas,
            "sobrantes": sobrantes,
            "cortes": cortes,
            "etapas": arbol.profundidad(u.nodo),
            "m2_piezas": _redondear(area / 1e6, 6),
            "aprovechamiento": _redondear(area / (st.ancho * st.largo) * 100, 2),
        })
    # Las planchas más llenas primero: el sobrante queda junto al final.
    salida.sort(key=lambda m: (-m["aprovechamiento"], -m["repeticiones"]))
    for n, m in enumerate(salida, start=1):
        m["numero"] = n
    return salida


def informe_material(mat: Material, piezas: list[Pieza], res: ResultadoMaterial | None,
                     errores: list[str], avisos: list[str]) -> dict:
    """Los números del informe de cálculo (fórmulas de Corte Certo, brief §7.1)."""
    calculadas = res.tipos if res else []
    n_piezas = sum(t.cantidad for t in calculadas)
    mm2 = sum(t.ancho * t.largo * t.cantidad for t in calculadas)
    mm2_presupuesto = sum(t.mm2_presupuesto for t in calculadas)
    perimetro = sum(2 * (t.ancho + t.largo) * t.cantidad for t in calculadas) / 1000
    salida = {
        "codigo": mat.codigo,
        "descripcion": mat.descripcion,
        "configuracion": config_material(mat),
        "piezas": n_piezas,
        "m2_piezas": _redondear(mm2 / 1e6, 6),
        "m2_piezas_presupuesto": _redondear(mm2_presupuesto / 1e6, 6),
        "perimetro_m": _redondear(perimetro, 2),
        "calculo_especial_perimetro_m": 0.0,
        "tipos": [{"tipo": t.indice + 1, "items": [{"item": i, "cantidad": c} for i, c in t.items],
                   "ancho_presupuesto": t.medida_presupuesto[0], "largo_presupuesto": t.medida_presupuesto[1],
                   "ancho": t.ancho, "largo": t.largo, "ancho_corte": t.ancho_corte,
                   "largo_corte": t.largo_corte, "cantidad": t.cantidad, "rota": t.rota,
                   "color": colores.color_pieza(t.indice + 1)} for t in calculadas],
        "avisos": list(mat.avisos) + avisos,
        "errores": errores,
        "calculado": res is not None and res.solucion is not None,
    }
    if res is None or res.solucion is None:
        salida.update({"layouts": 0, "planchas": 0, "m2_planchas": 0.0, "aprovechamiento": 0.0,
                       "perdida": 0.0, "planchas_usadas": [], "montajes": []})
        if res is not None:
            salida["errores"] = salida["errores"] + res.errores
        return salida
    montajes = _montajes(mat, res)
    if not mat.corte_max_libre:
        # "Máximo tamaño cortado (Limitado)": se controla con aviso (brief §6.1).
        for m in montajes:
            largos = [c["hasta"] - c["desde"] for c in m["cortes"]]
            if largos and max(largos) > mat.corte_max_mm:
                salida["avisos"].append(f"montaje {m['numero']}: tiene un corte de {max(largos)} mm, más "
                                        f"largo que el máximo tamaño cortado ({mat.corte_max_mm} mm)")
    usadas: "OrderedDict[tuple, dict]" = OrderedDict()
    m2_planchas = 0.0
    m2_hoja = 0.0
    for m in montajes:
        pl = m["plancha"]
        clave = (pl["ancho"], pl["largo"], pl["hoja_ancho"], pl["hoja_largo"])
        fila = usadas.setdefault(clave, {"cantidad": 0, "ancho": pl["ancho"], "largo": pl["largo"],
                                         "tipo": "Plancha", "hoja_ancho": pl["hoja_ancho"],
                                         "hoja_largo": pl["hoja_largo"], "supuesta": pl["supuesta"]})
        fila["cantidad"] += m["repeticiones"]
        m2_planchas += m["repeticiones"] * pl["ancho"] * pl["largo"] / 1e6
        m2_hoja += m["repeticiones"] * pl["hoja_ancho"] * pl["hoja_largo"] / 1e6
    planchas = sum(m["repeticiones"] for m in montajes)
    aprov = mm2 / 1e6 / m2_planchas * 100 if m2_planchas else 0.0
    aprov_r = _redondear(aprov, 2)
    salida.update({
        "layouts": len(montajes),
        "planchas": planchas,
        "m2_planchas": _redondear(m2_planchas, 6),
        "aprovechamiento": aprov_r,
        "perdida": _redondear(100 - aprov_r, 2),
        "planchas_usadas": list(usadas.values()),
        "montajes": montajes,
        # Agregados propios (no están en Corte Certo)
        "minimo_teorico_planchas": res.cota_planchas,
        "m2_hoja_entera": _redondear(m2_hoja, 6),
        "peso_piezas_kg": _redondear(mm2 / 1e6 * mat.peso_kg_m2, 1),
        "peso_planchas_kg": _redondear(m2_hoja * mat.peso_kg_m2, 1),
        "calculo": {"segundos": round(res.segundos, 3), "trabajo": res.trabajo,
                    "origen": res.solucion.origen,
                    "relajacion_lineal_m2": (_redondear(res.cota_lp_m2, 6)
                                             if res.cota_lp_m2 is not None else None)},
    })
    salida["avisos"] += res.avisos
    salida["errores"] += res.errores
    return salida


# ------------------------------------------------------------------------- principal
def ajustes_por_material(entrada: dict, piezas: list[Pieza], avisos: list[str]) -> dict:
    """Los ajustes de la entrada ("materiales"), con el código en mayúsculas como las piezas. Un
    ajuste para un material que no está en las piezas se avisa (no se aplica a nada)."""
    salida: dict[str, dict] = {}
    usados = {pz.material for pz in piezas}
    for codigo, valores in (entrada.get("materiales") or {}).items():
        normal = str(codigo).strip().upper()
        if normal in salida:
            avisos.append(f"ajustes de {normal} repetidos (con otra forma de escribir el código): se juntan")
        salida[normal] = {**salida.get(normal, {}), **(valores or {})}
        if normal not in usados:
            avisos.append(f"hay ajustes para {codigo}, pero ninguna pieza es de ese material: no se usan")
    return salida


def optimizar(entrada: dict, progreso=None, cancelar=None, catalogo: Catalogo | None = None,
              validar: bool = True) -> dict:
    """Calcula todos los materiales de la entrada. Ver `docs/API.md`.

    `progreso(**datos)` se llama a medida que avanza; `cancelar()` devuelve True para cortar y
    quedarse con lo mejor encontrado hasta ese momento.
    """
    from .configuracion import ConfiguracionInvalida
    from .validador import validar as validar_resultado

    catalogo = catalogo or Catalogo()
    proyecto = entrada.get("proyecto") or {}
    preset = entrada.get("preset") or "corte_certo"
    presets = todos_los_presets()
    if preset not in presets:
        raise ValueError(f"preset desconocido: {preset!r}")
    opciones = entrada.get("opciones") or {}
    esfuerzo = opciones.get("esfuerzo", "normal")
    piezas, errores_generales, avisos_generales = leer_piezas(entrada.get("piezas") or [])
    ajustes = ajustes_por_material(entrada, piezas, avisos_generales)
    por_material: "OrderedDict[str, list[Pieza]]" = OrderedDict()
    for pz in piezas:
        por_material.setdefault(pz.material, []).append(pz)
    materiales_salida = []
    for n_mat, (codigo, lista) in enumerate(por_material.items()):
        avisos: list[str] = []
        try:
            mat = catalogo.material(codigo, preset, ajustes.get(codigo))
        except ConfiguracionInvalida as exc:
            # No se calcula con un valor que no se puede usar; se muestra el material sin calcular.
            mat = catalogo.material(codigo, preset, usar_locales=False)
            materiales_salida.append(informe_material(mat, lista, None, [f"{exc}; no se calcula este material"],
                                                      avisos))
            continue
        stocks, errores = armar_stocks(mat)
        if not stocks:
            errores.append(f"{codigo}: no tiene planchas habilitadas; no se calcula este material")
            materiales_salida.append(informe_material(mat, lista, None, errores, avisos))
            continue
        tipos, err_t, av_t = armar_tipos(mat, lista, stocks)
        errores += err_t
        avisos += av_t
        res = None
        if tipos:
            def prog(**kw):
                if progreso:
                    progreso(material=codigo, numero_material=n_mat + 1,
                             materiales=len(por_material), **kw)
            res = calcular(tipos, stocks, mat.separacion_piezas_mm, mat.destaque_min_mm,
                           esfuerzo, prog, cancelar)
        materiales_salida.append(informe_material(mat, lista, res, errores, avisos))
    resultado = {
        "version": __version__,
        "fecha": entrada.get("fecha") or dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "proyecto": {"codigo": str(proyecto.get("codigo", "")),
                     "descripcion": str(proyecto.get("descripcion", ""))},
        "preset": preset,
        "preset_nombre": presets[preset]["nombre"],
        "esfuerzo": esfuerzo,
        "piezas": sum(m["piezas"] for m in materiales_salida),
        "materiales": materiales_salida,
        "avisos": avisos_generales,
        "errores": errores_generales,
    }
    # Completo = se calcularon todas las piezas de la entrada. Un resultado verificado pero
    # incompleto (una pieza que no entra, un material sin planchas) no es una cotización entera.
    resultado["completo"] = not errores_generales and all(m["calculado"] and not m["errores"]
                                                          for m in materiales_salida)
    if validar:
        errores_val = validar_resultado(entrada, resultado, catalogo)
        resultado["verificado"] = not errores_val
        resultado["validacion"] = errores_val
    return resultado
