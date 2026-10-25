"""Reconstruir las piezas que se optimizaron en un presupuesto viejo (brief §10.2).

Reglas (`contexto/fabrica/DATA_DICTIONARY.md` y `docs/CONTRATO_DATOS.md`):
- Las piezas salen de `DETPRES2` (`piezas.csv`): `V_CANTIALT` = piezas (`V_CANTI` ya son m²).
- Si un renglón de vidrio no tiene piezas en `DETPRES2`, se usa el renglón de `DETPRES`
  (`renglones.csv`): ahí `V_CANTI` son m² y `V_CANTIALT` las piezas.
- Un **DVH** (familia `X…`, con `ART1`/`ART3`) son **2 vidrios**: una pieza de `ART1` y otra de
  `ART3` con la misma medida. En `DETPRES` del DVH, `V_CANTI` son unidades.
- **No se optimizan**: herrajes, fletes, perforaciones, consumibles, cámaras, nada que no sea
  vidrio. Se reconoce el vidrio porque su código está en `config/hojas.csv` o porque el artículo
  tiene espesor y no es de una familia excluida. Lo que se deja afuera se cuenta, con el motivo.
- Pulido recto: la clase con "PR" (la regla la aplica `optimizar()`, +3 mm).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .datos import Casos, numero

EXCLUIR = re.compile(r"HERRAJ|FLETE|PERFOR|CONSUM|CAMARA|SILIC|PERFIL|BURLET|INSTAL|SERVIC|MANO DE OBRA|"
                     r"TORNILL|ACCESOR|EMBALAJ|ENVIO|TRASLAD|DESCUENTO|SELLADOR", re.IGNORECASE)


@dataclass
class Reconstruccion:
    numero: str
    piezas: list[dict] = field(default_factory=list)  # en el formato de entrada de optimizar()
    excluidos: list[dict] = field(default_factory=list)  # {codigo, motivo, cantidad}
    avisos: list[str] = field(default_factory=list)

    def materiales(self) -> list[str]:
        vistos: list[str] = []
        for p in self.piezas:
            if p["material"] not in vistos:
                vistos.append(p["material"])
        return vistos


def _es_unidad_armada(renglon: dict, articulo: dict) -> bool:
    familia = (renglon.get("familia") or articulo.get("familia") or "").upper()
    return familia.startswith("X") and bool((renglon.get("art1") or "").strip()) and \
        bool((renglon.get("art3") or "").strip())


def _es_vidrio(codigo: str, casos: Casos, catalogo_codigos: set[str]) -> tuple[bool, str]:
    codigo = codigo.upper()
    if codigo in catalogo_codigos:
        return True, ""
    art = casos.articulos.get(codigo, {})
    familia = (art.get("familia") or "").upper()
    texto = f"{familia} {art.get('descripcion', '')} {codigo}"
    if EXCLUIR.search(texto):
        return False, f"no es vidrio ({familia or 'sin familia'})"
    fam = casos.familias.get(familia, {})
    if (fam.get("perimetro") or "").upper() == "SI":
        return False, f"familia {familia} se cobra por perímetro"
    espesor = numero(art.get("espesor"))
    if espesor and espesor > 0:
        return True, ""
    if not art:
        return False, "artículo desconocido (no está en articulos.csv ni en hojas.csv)"
    return False, f"artículo sin espesor ({familia or 'sin familia'})"


def _cantidad(fila: dict, largo: float, ancho: float, avisos: list[str], donde: str,
              campo_piezas: str = "v_cantialt", campo_m2: str = "v_canti") -> int | None:
    piezas = numero(fila.get(campo_piezas))
    if piezas and piezas > 0:
        if piezas != int(piezas):
            avisos.append(f"{donde}: {piezas} piezas no es entero")
        return int(round(piezas))
    m2 = numero(fila.get(campo_m2))
    if m2 and largo and ancho:
        calc = m2 / (largo * ancho / 1e6)
        if abs(calc - round(calc)) < 0.02 and round(calc) > 0:
            avisos.append(f"{donde}: sin cantidad de piezas, se sacó de los m² ({m2} m² → {round(calc)})")
            return int(round(calc))
    avisos.append(f"{donde}: no se pudo saber la cantidad de piezas; se deja afuera")
    return None


def reconstruir(casos: Casos, numero_presupuesto: str, catalogo_codigos: set[str]) -> Reconstruccion:
    """Piezas por material de un presupuesto.

    Por cada artículo: si tiene piezas en DETPRES2, se usan **todas una sola vez** (aunque el
    artículo aparezca en varios renglones de DETPRES); si no, los renglones de DETPRES. Así una
    pieza nunca se cuenta dos veces. Se avisa si los m² de DETPRES2 no cierran con los de DETPRES.
    """
    rec = Reconstruccion(numero_presupuesto)
    renglones = casos.renglones.get(numero_presupuesto, [])
    por_articulo_d2: dict[str, list[dict]] = {}
    for p in casos.piezas.get(numero_presupuesto, []):
        por_articulo_d2.setdefault((p.get("v_codart") or "").upper(), []).append(p)
    item = 0

    def agregar(material, largo, ancho, cantidad, clase, origen):
        nonlocal item
        item += 1
        rec.piezas.append({"item": str(item), "material": material.upper(), "cantidad": cantidad,
                           "ancho": int(round(ancho)), "largo": int(round(largo)), "clase": clase,
                           "origen": origen})

    vistos: set[str] = set()
    for n_r, r in enumerate(renglones, start=1):
        codigo = (r.get("v_codart") or "").upper()
        art = casos.articulos.get(codigo, {})
        donde = f"presupuesto {numero_presupuesto} renglón {r.get('orden') or n_r} ({codigo})"
        armada = _es_unidad_armada(r, art)
        if armada:
            vidrios = []
            for v, clase in (((r.get("art1") or "").upper(), r.get("claseart1") or r.get("clase") or ""),
                             ((r.get("art3") or "").upper(), r.get("claseart3") or r.get("clase") or "")):
                ok, motivo = _es_vidrio(v, casos, catalogo_codigos)
                if ok:
                    vidrios.append((v, clase))
                else:
                    rec.avisos.append(f"{donde}: el vidrio {v} de la unidad armada: {motivo}")
        else:
            ok, motivo = _es_vidrio(codigo, casos, catalogo_codigos)
            if not ok:
                rec.excluidos.append({"codigo": codigo, "motivo": motivo,
                                      "cantidad": numero(r.get("v_canti")) or 0})
                continue
            vidrios = [(codigo, r.get("clase") or "")]
        if not vidrios:
            continue
        origen = {"presupuesto": numero_presupuesto, "renglon": r.get("orden") or n_r}
        if codigo in por_articulo_d2:
            if codigo in vistos:
                continue  # las piezas de DETPRES2 de este artículo ya se usaron
            vistos.add(codigo)
            m2_d2 = 0.0
            for p in por_articulo_d2[codigo]:
                largo, ancho = numero(p.get("largo")) or 0, numero(p.get("ancho")) or 0
                if largo <= 0 or ancho <= 0:
                    rec.avisos.append(f"{donde}: pieza de DETPRES2 con medida {largo} × {ancho}; se deja afuera")
                    continue
                cant = _cantidad(p, largo, ancho, rec.avisos, donde + " (DETPRES2)")
                if cant is None:
                    continue
                m2_d2 += cant * largo * ancho / 1e6
                for k, (v, clase) in enumerate(vidrios, start=1):
                    agregar(v, largo, ancho, cant, p.get("clase") or clase,
                            {**origen, "fuente": "DETPRES2", "vidrio": k if armada else None})
            if not armada:
                m2_d1 = sum(numero(x.get("v_canti")) or 0 for x in renglones
                            if (x.get("v_codart") or "").upper() == codigo)
                if m2_d1 and abs(m2_d1 - m2_d2) > max(0.01, 0.005 * m2_d1):
                    rec.avisos.append(f"presupuesto {numero_presupuesto} ({codigo}): los m² de las piezas "
                                      f"({m2_d2:.3f}) no cierran con los del renglón ({m2_d1:.3f})")
            continue
        largo, ancho = numero(r.get("largo")) or 0, numero(r.get("ancho")) or 0
        if largo <= 0 or ancho <= 0:
            rec.avisos.append(f"{donde}: sin piezas en DETPRES2 y sin medida en el renglón; se deja afuera")
            continue
        if armada:
            cant = numero(r.get("v_canti"))  # en DVH, unidades
            cant = int(round(cant)) if cant and cant > 0 else None
            if cant is None:
                rec.avisos.append(f"{donde}: unidad armada sin cantidad; se deja afuera")
                continue
        else:
            cant = _cantidad(r, largo, ancho, rec.avisos, donde)
            if cant is None:
                continue
        for k, (v, clase) in enumerate(vidrios, start=1):
            agregar(v, largo, ancho, cant, clase, {**origen, "fuente": "DETPRES", "vidrio": k if armada else None})
    # Piezas de DETPRES2 de artículos que no tienen renglón en DETPRES.
    for codigo, lista in por_articulo_d2.items():
        if codigo in vistos or any((r.get("v_codart") or "").upper() == codigo for r in renglones):
            continue
        ok, motivo = _es_vidrio(codigo, casos, catalogo_codigos)
        if not ok:
            rec.excluidos.append({"codigo": codigo, "motivo": motivo, "cantidad": len(lista)})
            continue
        rec.avisos.append(f"presupuesto {numero_presupuesto}: piezas de DETPRES2 de {codigo} sin renglón en DETPRES")
        for p in lista:
            largo, ancho = numero(p.get("largo")) or 0, numero(p.get("ancho")) or 0
            cant = _cantidad(p, largo, ancho, rec.avisos, f"presupuesto {numero_presupuesto} ({codigo})") \
                if largo > 0 and ancho > 0 else None
            if cant:
                agregar(codigo, largo, ancho, cant, p.get("clase") or "",
                        {"presupuesto": numero_presupuesto, "fuente": "DETPRES2 sin renglón"})
    return rec
