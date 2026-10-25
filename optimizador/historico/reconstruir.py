"""Reconstruir las piezas que se optimizaron en un presupuesto viejo (brief §10.2).

Reglas (`contexto/fabrica/DATA_DICTIONARY.md` y `docs/CONTRATO_DATOS.md`):
- Las piezas salen de `DETPRES2` (`piezas.csv`): `V_CANTIALT` = piezas (`V_CANTI` ya son m²).
- Si un renglón de vidrio no tiene piezas en `DETPRES2`, se usa el renglón de `DETPRES`
  (`renglones.csv`): `V_CANTIALT` las piezas. Si `V_CANTIALT` está vacío, se saca de `V_CANTI`
  como m², **con aviso** (no está confirmado que ahí sean m²).
- Un **DVH** (familia `X…`, con `ART1`/`ART3`) son **2 vidrios**: una pieza de `ART1` y otra de
  `ART3` con la misma medida. En `DETPRES` del DVH, `V_CANTI` son unidades. La clase de cada vidrio
  es `CLASEART1`/`CLASEART3` (ahí está el pulido recto); si está vacía, la del renglón o la pieza.
- **No se optimizan**: herrajes, fletes, perforaciones, consumibles, cámaras, láminas (PVB/EVA),
  nada que no sea vidrio. Se reconoce el vidrio porque su código está en `config/hojas.csv` o
  porque el artículo tiene espesor de 2 mm o más y no es de una familia excluida. Lo que se deja
  afuera se cuenta, con el motivo.
- Pulido recto: la clase con "PR" (la regla la aplica `optimizar()`, +3 mm).

Todo lo dudoso queda en `avisos` y, por material, en `avisos_material`: la comparación los
muestra al lado del caso (regla: nunca inventar en silencio).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .datos import Casos, numero

EXCLUIR = re.compile(r"HERRAJ|FLETE|PERFOR|CONSUM|CAMARA|SILIC|PERFIL|BURLET|INSTAL|SERVIC|MANO DE OBRA|"
                     r"TORNILL|ACCESOR|EMBALAJ|ENVIO|TRASLAD|DESCUENTO|SELLADOR|LAMINAS?\b|\bPVB\b|"
                     r"^MP\b|\bFILM\b", re.IGNORECASE)
ESPESOR_MINIMO = 2.0  # mm: menos que eso no es una plancha de vidrio (láminas, films)


@dataclass
class Reconstruccion:
    numero: str
    piezas: list[dict] = field(default_factory=list)  # en el formato de entrada de optimizar()
    excluidos: list[dict] = field(default_factory=list)  # {codigo, motivo, cantidad}
    avisos: list[str] = field(default_factory=list)
    avisos_material: dict[str, list[str]] = field(default_factory=dict)  # código -> avisos

    def materiales(self) -> list[str]:
        vistos: list[str] = []
        for p in self.piezas:
            if p["material"] not in vistos:
                vistos.append(p["material"])
        return vistos

    def avisar(self, texto: str, *materiales: str) -> None:
        self.avisos.append(texto)
        for m in materiales:
            if m:
                self.avisos_material.setdefault(m.upper(), []).append(texto)


def _sin_tildes(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().upper()


def _familia(renglon: dict, articulo: dict) -> str:
    return (renglon.get("familia") or articulo.get("familia") or "").upper()


def _es_vidrio(codigo: str, casos: Casos, catalogo_codigos: set[str]) -> tuple[bool, str]:
    codigo = codigo.upper()
    if codigo in catalogo_codigos:
        return True, ""
    art = casos.articulos.get(codigo, {})
    familia = (art.get("familia") or "").upper()
    texto = _sin_tildes(f"{familia} | {art.get('descripcion', '')} | {codigo}")
    if any(EXCLUIR.search(parte.strip()) for parte in texto.split("|")):
        return False, f"no es vidrio ({familia or 'sin familia'})"
    fam = casos.familias.get(familia, {})
    if (fam.get("perimetro") or "").upper() == "SI":
        return False, f"familia {familia} se cobra por perímetro"
    espesor = numero(art.get("espesor"))
    if espesor and espesor >= ESPESOR_MINIMO:
        return True, ""
    if not art:
        return False, "artículo desconocido (no está en articulos.csv ni en hojas.csv)"
    if espesor:
        return False, f"espesor {espesor:g} mm: no es una plancha de vidrio ({familia or 'sin familia'})"
    return False, f"artículo sin espesor ({familia or 'sin familia'})"


def _cantidad(fila: dict, largo: float, ancho: float, rec: Reconstruccion, donde: str,
              materiales: tuple[str, ...]) -> int | None:
    piezas = numero(fila.get("v_cantialt"))
    if piezas and piezas > 0:
        if piezas != int(piezas):
            rec.avisar(f"{donde}: {piezas} piezas no es entero", *materiales)
        return int(round(piezas))
    m2 = numero(fila.get("v_canti"))
    if m2 and largo and ancho:
        calc = m2 / (largo * ancho / 1e6)
        if abs(calc - round(calc)) < 0.02 and round(calc) > 0:
            rec.avisar(f"{donde}: sin cantidad de piezas (V_CANTIALT); se tomó V_CANTI={m2:g} como m² → "
                       f"{round(calc)} piezas (si fueran unidades serían {m2:g})", *materiales)
            return int(round(calc))
    rec.avisar(f"{donde}: no se pudo saber la cantidad de piezas; se deja afuera", *materiales)
    return None


def reconstruir(casos: Casos, numero_presupuesto: str, catalogo_codigos: set[str]) -> Reconstruccion:
    """Piezas por material de un presupuesto.

    Por cada artículo: si tiene piezas en DETPRES2, se usan **todas una sola vez** (aunque el
    artículo aparezca en varios renglones de DETPRES); si no, los renglones de DETPRES. Así una
    pieza nunca se cuenta dos veces. Si DETPRES2 no cierra con DETPRES (m² en un vidrio, unidades
    en un DVH), se avisa: puede faltar algún renglón.
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

    # Vidrios que forman parte de una unidad armada (para no contarlos otra vez sueltos).
    vidrios_de_armadas: set[str] = set()
    vistos: set[str] = set()
    for n_r, r in enumerate(renglones, start=1):
        codigo = (r.get("v_codart") or "").upper()
        art = casos.articulos.get(codigo, {})
        donde = f"presupuesto {numero_presupuesto} renglón {r.get('orden') or n_r} ({codigo})"
        familia = _familia(r, art)
        armada = familia.startswith("X")
        if armada:
            a1, a3 = (r.get("art1") or "").strip().upper(), (r.get("art3") or "").strip().upper()
            if not a1 or not a3:
                rec.excluidos.append({"codigo": codigo, "motivo": f"unidad armada ({familia}) sin ART1/ART3",
                                      "cantidad": numero(r.get("v_canti")) or 0})
                rec.avisar(f"{donde}: unidad armada sin los dos vidrios (ART1={a1 or '—'}, ART3={a3 or '—'}); "
                           f"se deja afuera", a1, a3)
                continue
            vidrios = []
            for v, clase_v in ((a1, r.get("claseart1") or ""), (a3, r.get("claseart3") or "")):
                ok, motivo = _es_vidrio(v, casos, catalogo_codigos)
                if ok:
                    vidrios.append((v, clase_v))
                    vidrios_de_armadas.add(v)
                else:
                    rec.avisar(f"{donde}: el vidrio {v} de la unidad armada: {motivo}", v)
            texto = _sin_tildes(f"{r.get('clase', '')} {r.get('detalle', '')} {art.get('descripcion', '')}")
            if "ESCALON" in texto:
                rec.avisar(f"{donde}: DVH escalonado; los dos vidrios se toman con la misma medida y "
                           f"puede no ser así", *(v for v, _ in vidrios))
        else:
            ok, motivo = _es_vidrio(codigo, casos, catalogo_codigos)
            if not ok:
                rec.excluidos.append({"codigo": codigo, "motivo": motivo,
                                      "cantidad": numero(r.get("v_canti")) or 0})
                continue
            vidrios = [(codigo, "")]
        if not vidrios:
            continue
        mats = tuple(v for v, _ in vidrios)
        origen = {"presupuesto": numero_presupuesto, "renglon": r.get("orden") or n_r}

        def clase_de(clase_vidrio: str, *otras: str) -> str:
            # En un DVH manda la clase de cada vidrio (CLASEART1/3); si no hay, la de la pieza o el renglón.
            for c in (clase_vidrio, *otras):
                if (c or "").strip():
                    return c
            return ""

        if codigo in por_articulo_d2:
            if codigo in vistos:
                continue  # las piezas de DETPRES2 de este artículo ya se usaron
            vistos.add(codigo)
            mismos = [x for x in renglones if (x.get("v_codart") or "").upper() == codigo]
            # Si la pieza no trae clase, la del renglón solo vale si todos los renglones del artículo
            # tienen la misma (si no, no se sabe de cuál es la pieza).
            clases = {(x.get("clase") or "").strip() for x in mismos}
            clase_renglon = clases.pop() if len(clases) == 1 else ""
            m2_d2 = 0.0
            unidades_d2 = 0
            for p in por_articulo_d2[codigo]:
                largo, ancho = numero(p.get("largo")) or 0, numero(p.get("ancho")) or 0
                if largo <= 0 or ancho <= 0:
                    rec.avisar(f"{donde}: pieza de DETPRES2 con medida {largo} × {ancho}; se deja afuera", *mats)
                    continue
                cant = _cantidad(p, largo, ancho, rec, donde + " (DETPRES2)", mats)
                if cant is None:
                    continue
                m2_d2 += cant * largo * ancho / 1e6
                unidades_d2 += cant
                for k, (v, clase_v) in enumerate(vidrios, start=1):
                    agregar(v, largo, ancho, cant,
                            clase_de(clase_v, p.get("clase"), clase_renglon) if armada
                            else clase_de(p.get("clase"), clase_renglon),
                            {**origen, "fuente": "DETPRES2", "vidrio": k if armada else None})
            if armada:
                unidades_d1 = sum(numero(x.get("v_canti")) or 0 for x in mismos)
                if unidades_d1 and round(unidades_d1) != unidades_d2:
                    rec.avisar(f"presupuesto {numero_presupuesto} ({codigo}): DETPRES2 tiene {unidades_d2} "
                               f"unidades y los renglones suman {unidades_d1:g}; puede faltar algún renglón", *mats)
            else:
                m2_d1 = sum(numero(x.get("v_canti")) or 0 for x in mismos)
                if m2_d1 and abs(m2_d1 - m2_d2) > max(0.01, 0.005 * m2_d1):
                    rec.avisar(f"presupuesto {numero_presupuesto} ({codigo}): los m² de las piezas de DETPRES2 "
                               f"({m2_d2:.3f}) no cierran con los de los renglones ({m2_d1:.3f}); puede "
                               f"faltar algún renglón", *mats)
            continue
        largo, ancho = numero(r.get("largo")) or 0, numero(r.get("ancho")) or 0
        if largo <= 0 or ancho <= 0:
            rec.avisar(f"{donde}: sin piezas en DETPRES2 y sin medida en el renglón; se deja afuera", *mats)
            continue
        if armada:
            cant = numero(r.get("v_canti"))  # en DVH, unidades
            cant = int(round(cant)) if cant and cant > 0 else None
            if cant is None:
                rec.avisar(f"{donde}: unidad armada sin cantidad; se deja afuera", *mats)
                continue
        else:
            cant = _cantidad(r, largo, ancho, rec, donde, mats)
            if cant is None:
                continue
        for k, (v, clase_v) in enumerate(vidrios, start=1):
            agregar(v, largo, ancho, cant, clase_de(clase_v, r.get("clase")) if armada else (r.get("clase") or ""),
                    {**origen, "fuente": "DETPRES", "vidrio": k if armada else None})
    # Piezas de DETPRES2 de artículos que no tienen renglón en DETPRES.
    for codigo, lista in por_articulo_d2.items():
        if codigo in vistos or any((r.get("v_codart") or "").upper() == codigo for r in renglones):
            continue
        ok, motivo = _es_vidrio(codigo, casos, catalogo_codigos)
        if not ok:
            rec.excluidos.append({"codigo": codigo, "motivo": motivo, "cantidad": len(lista)})
            continue
        if codigo in vidrios_de_armadas:
            # Probablemente son las piezas del DVH, que ya se contaron desde su renglón.
            rec.avisar(f"presupuesto {numero_presupuesto}: hay piezas de DETPRES2 con el código {codigo}, que es "
                       f"un vidrio de una unidad armada; no se suman para no contarlas dos veces", codigo)
            continue
        rec.avisar(f"presupuesto {numero_presupuesto}: piezas de DETPRES2 de {codigo} sin renglón en DETPRES",
                   codigo)
        for p in lista:
            largo, ancho = numero(p.get("largo")) or 0, numero(p.get("ancho")) or 0
            cant = _cantidad(p, largo, ancho, rec, f"presupuesto {numero_presupuesto} ({codigo})", (codigo,)) \
                if largo > 0 and ancho > 0 else None
            if cant:
                agregar(codigo, largo, ancho, cant, p.get("clase") or "",
                        {"presupuesto": numero_presupuesto, "fuente": "DETPRES2 sin renglón"})
    return rec
