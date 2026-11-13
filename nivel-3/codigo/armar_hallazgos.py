#!/usr/bin/env python3
"""Arma nivel-3/hallazgos.json a partir de la clasificación local (clasif.json).
Cada cláusula del OCR toma el veredicto de la redacción conocida con la que coincide.
Las explicaciones identifican a las partes por su rol y no contienen datos personales."""
import json, sys
from pathlib import Path
from reglas import REGLAS

clasif = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
cat = clasif["catalogo"]
filas = []
for cid, hall in clasif["resultados"].items():
    elegidas = []
    for h in sorted(hall, key=lambda h: -h[3]):
        if all(abs(h[0] - e[0]) > 90 for e in elegidas):
            elegidas.append(h)
    elegidas.sort()
    assert len(elegidas) == 10, (cid, len(elegidas))
    for i, (pos, num, clave, sim, art, ej) in enumerate(elegidas, 1):
        if not art:
            continue
        texto = cat[clave]["texto"]
        regla = next(r for r in REGLAS if texto.startswith(r[0]))
        assert regla[1] == art, (cid, i, regla[1], art)
        filas.append({"contrato": cid, "clausula": f"C{i:02d}", "articulo": art,
                      "explicacion": regla[3], "fallos": regla[2]})
Path(sys.argv[2]).write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(filas), "hallazgos")
for f in filas:
    print(f["contrato"], f["clausula"], f["articulo"], ",".join(f["fallos"]))
