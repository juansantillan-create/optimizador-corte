# Glossary — glass-industry and Metrix vocabulary

For anyone (or any future Claude session) who isn't from the glass industry.
Terms are mapped Spanish ↔ English, with the field/flag in the data where
relevant. See `DATA_DICTIONARY.md` for the full field-level detail.

| Español | English | What it means |
|---|---|---|
| **Templado** | Tempering | Heat treatment that hardens glass (controlled thermal shock). The most quality-critical process — highest error rate among high-volume processes. `CAJAS.TP` flag. |
| **DVH** | IGU (Insulated Glass Unit) / double-glazed unit | "Doble Vidriado Hermético" — two (or more) glass panes assembled with a sealed air/gas gap between them. `CAJAS.DV` flag. |
| **Laminado (EVA)** | Laminating (EVA interlayer) | Bonding two glass panes with an EVA (ethylene-vinyl acetate) interlayer sheet between them. `CAJAS.LM` flag. Other interlayers seen in this data: PVB, SGP, IPL. |
| **Canteado** | Edging | General term for work done on the glass edge/border (edge-polishing family of processes). |
| **Pulido recto** | Straight-edge polishing | Polishing a flat/straight edge. `CAJAS.BD` flag. Billed separately (`PR_PRETO`) except on tempered glass, where it's already included in the tempering price. |
| **Pulido matado de filo** | Chamfered-edge polishing | Polishing a beveled/chamfered edge. `CAJAS.MF` flag. Second-highest error volume in the whole system. |
| **PDV** ("Piel De Vidrio" / glass skin) | — | **Not a process flag.** A piece *class* value (`CAJAS.NOMCLASE` / `PEDIDO3.CLASE`, e.g. `"PDV DVH"`, `"LAM PR PDV"`). Easy to confuse with "% Sellado estructural" (the `HER` flag) — a mix-up that actually happened in a prior version of the team's dashboard and was corrected 2026-07-10. |
| **TEMPLUX** | (in-house product line) | The shop's tempered-glass product line — a business category (`TIPO`/`Proceso Final` in the team's own spreadsheet), not a Metrix field itself. |
| **LAMILUX** | (in-house product line, name confirmed by the user) | Selling a glass sheet that went through Autoclave **without being cut**, to another glass processor — B2B sale of semi-finished raw material, not a finished piece for an end client. `CAJAS.LUX` flag. |
| **Autoclave** | Autoclave | Pressure-lamination process (pressure oven). `CAJAS.AUT` flag. |
| **m²** | m² (square meters) | Glass surface area. Metrix's real formula: `LARGO*ANCHO*0.000001*FACTOR` (mm → m², with an `ARTICULO.FACTOR` multiplier, or 1 if that's 0). |
| **ml** (metros lineales) | Linear meters (perimeter) | Piece perimeter, used for edging/polishing/sealing pricing: `((LARGO*2)+(ANCHO*2))*0.001*FACTOR`. |
| **Cotización / Presupuesto** | Quote / budget | The commercial document before an order exists. Table `PRESUP` + detail in `DETPRES`/`DETPRES2`/`DETPRESCONS`/`DETPRESINS`. |
| **Pedido** | Order | The real production order. Table `PEDIDO1` + detail in `PEDIDO2`/`PEDIDO3`, and physical pieces in `CAJAS`. |
| **Fasón** | Custom/shaped cut (fasoned glass) | Glass cut to a non-rectangular / custom shape. Appears in class names `FASON1`...`FASON12` and as `TIPO=FASON` in the team's spreadsheet. |
| **Aplicar clase** | "Apply class" | An action in Metrix's own interface that recalculates a quote line's real price from its process combination (`CLASE`), replacing a generic import price with the correct one from `LISTA`/`PRECIOS`, plus the -2%/+2% `DESCUENTO` adjustment. Confirmed with a live experiment (~1.95–2× factor). |
| **Parejas / emparejado** | Pairing/matching | Selecting two compatible glass panes to assemble into a DVH unit. `CAJAS.HJ` flag. |
| **Sellado estructural** | Structural sealing/glazing | Sealing with structural silicone, typically after a DVH assembly. `CAJAS.HER` flag — confirmed via Metrix's own report #198, "Proceso de Sellado Estructural." |
| **Pegado a bastidor** | Frame gluing/mounting | Fixing a piece to a frame/mount. `CAJAS.PEG` flag. |
| **Entrecalles** | Cutting spacing/margin | Technical cutting value: the margin/spacing left between pieces on the glass sheet being cut. |
| **Optimización (de corte)** | Cutting optimization (nesting) | A cutting plan that groups pieces from different orders onto the same sheet to minimize waste (typical industry tools: Optima/Optiway). `CAJAS.OPTIMIZACION` / `PEDIDO1.OPTIMIZACION`. Not automated by this project. |
| **WIP** | Work In Progress | Pieces with genuinely active work right now (not finished, not cancelled). See the "backlog zombie" caveat in `DATA_DICTIONARY.md` — a naive WIP count is badly distorted by stale data. |
| **Backlog** | Backlog | Active orders not yet delivered. |
| **Backlog zombie** | "Zombie" backlog | Pieces with no recent movement (>90 days) belonging to orders never formally closed — a data-quality finding, not an operational metric to act on directly. |
| **Lead time** | Lead time | Time between order date and real delivery date. |
| **Rotura / reproceso / retrabajo** | Breakage / rework | A piece that had an error recorded (`<PROC>_ERR>0`) at some stage — doesn't distinguish the cause (physical breakage, mis-cut, client complaint). |
| **Stock de paquetes** | Package stock | Stock system for supplies/sheets tracked by "package" (`NUMPAQUETE`), recomputed by summing movements (adjustments + receipts − Lamilux consumption) from a fixed cutoff date. |
| **Consumibles** | Consumables | Materials sold by m²/linear-meter/weight (silicone, gaskets, profiles) — not glass itself. `DETPRESCONS`. |
| **Instalación** | Installation | Installation service on a quote. `DETPRESINS`. |
| **Nave / depósito** | Warehouse / storage bay | Physical stock location, catalog `SUCURSAL`. |
| **Remito de entrada** | Supplier delivery note / goods receipt | Document for receiving supplier goods. `RENTRADA`/`DETENT`/`DETENT2`. |
| **PVB / SGP / IPL** | PVB / SGP / ionoplast interlayer | Types of laminating interlayer sheet, seen as `Proceso Final` categories in the team's own spreadsheet (alongside EVA). |
| **Interfaz** | — | Name of a *separate*, older tool (an Excel-import utility, `interfaz/interfaz.exe`) some staff use to bulk-load orders directly into Metrix — unrelated to this project. Shows up in the data as Metrix user `INTERFAZ`. Don't confuse with this codebase's `pipeline/api.py`. |
