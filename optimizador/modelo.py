"""Las cosas con las que trabaja el optimizador: piezas, materiales, planchas.

Convenciones (ver `CLAUDE.md`):
- Todo en milímetros enteros.
- La plancha va acostada: **ancho = eje X = lado largo** (3580), **largo = eje Y = lado corto**
  (2500). Origen abajo a la izquierda.
- Una pieza "sin girar" va con su **ancho** a lo largo del eje X y su **largo** en Y. "Girada" =
  al revés.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TEXTURAS = ("sin", "horizontal", "vertical")


@dataclass
class Plancha:
    """Una medida de plancha de un material, tal como viene del proveedor."""

    ancho: int  # lado largo (X), hoja entera: 3600
    largo: int  # lado corto (Y): 2500
    corte_banda: int = 0  # se le saca al lado largo: 3600 -> 3580
    habilitada: bool = True
    prioridad: int = 0
    supuesta: bool = False  # no estaba en hojas.csv: se usó una por defecto
    origen: str = ""  # de dónde salió (hoja y fila del Excel, o "supuesta …")

    def clave(self) -> str:
        return f"{self.ancho}x{self.largo}"


@dataclass
class Material:
    """Un material con los campos de "Propiedades físicas" de Corte Certo, más lo de Cristalux
    (corte banda en cada plancha, sobremedida de pulido)."""

    codigo: str
    descripcion: str = ""
    color: str = ""
    espesor_mm: float = 0
    peso_kg_m2: float = 0
    # Propiedades físicas de Corte Certo
    separacion_piezas_mm: int = 0  # "Ancho de la sierra"
    destaque_min_mm: int = 0  # "Ancho mínimo de destaque"
    genera_retazo: bool = True
    retazo_ancho_min_mm: int = 0
    retazo_largo_min_mm: int = 0
    usar_area_min: bool = False
    retazo_area_min_m2: float = 0
    rotacion: bool = True
    textura: str = "sin"  # "sin" (Corte Certo: "Sem") | "horizontal" | "vertical"
    constante_ancho_mm: int = 0
    constante_largo_mm: int = 0
    margen_arriba_mm: int = 0
    margen_abajo_mm: int = 0
    margen_izquierda_mm: int = 0
    margen_derecha_mm: int = 0
    corte_max_libre: bool = True
    corte_max_mm: int = 10000
    # Agregados de Cristalux
    sobremedida_pulido_mm: int = 0  # se suma a ancho y largo de las piezas con pulido recto (H3)
    planchas: list[Plancha] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def util(self, plancha: Plancha) -> tuple[int, int]:
        """Plancha útil = plancha − corte banda (lado largo) − márgenes de seguridad."""
        ancho = plancha.ancho - plancha.corte_banda - self.margen_izquierda_mm - self.margen_derecha_mm
        largo = plancha.largo - self.margen_arriba_mm - self.margen_abajo_mm
        return ancho, largo


@dataclass
class Pieza:
    """Un renglón del proyecto: `cantidad` piezas iguales."""

    item: str
    material: str
    cantidad: int
    ancho: int
    largo: int
    rota: bool | None = None  # None = lo que diga el material
    descripcion: str = ""
    origen: dict | None = None
    sobremedida_mm: int = 0  # además de la del material (por ejemplo, pulido recto)
    pulido_recto: bool = False


@dataclass
class Proyecto:
    codigo: str
    descripcion: str
    piezas: list[Pieza]
