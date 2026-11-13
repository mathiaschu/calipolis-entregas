#!/usr/bin/env python3
"""Muestra una ventana corta del OCR normalizado alrededor de una frase de cláusula (texto contractual,
sin datos personales). Antes de imprimir pasa la ventana por el filtro de números largos."""
import re, sys
from pathlib import Path
from clasificar import mejores, norm
OCR = Path(__file__).resolve().parent.parent / "ocr"
cid, frase, antes, despues = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
doc = norm((OCR / f"{cid}.txt").read_text(encoding="utf-8"))
r, pos = mejores(doc, norm(frase), paso=4)
w = doc[max(0, pos - antes):pos + len(norm(frase)) + despues]
w = re.sub(r"\d[\d ]{3,}\d", "[N]", w)
print(f"{cid} sim {r:.2f}: ...{w}...")
