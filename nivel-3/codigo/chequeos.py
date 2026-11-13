#!/usr/bin/env python3
"""Chequeos puntuales sobre el OCR crudo que sólo devuelven cifras, fechas y conteos.

- fechas: todas las fechas dd/mm/aaaa reconocidas (no son datos personales).
- inventario: cantidad de renglones "Bien NN" y si alguno menciona bienes no funcionales.
- cifras: tras un ancla, las palabras que se parecen a números (distancia <= 2) en una ventana.
- frase: si una frase conocida aparece (similitud) y con qué puntaje.

Uso:
  python3 chequeos.py fechas C-302 C-305
  python3 chequeos.py inventario C-301 C-303
  python3 chequeos.py cifras C-310 "podra ajustar" 14
  python3 chequeos.py frase C-310 "ningun hogar de esta unidad tiene constancia de proteccion"
"""
import difflib
import re
import sys
from pathlib import Path

from clasificar import mejores, norm
from revisar import NUM_PAL

OCR = Path(__file__).resolve().parent.parent / "ocr"


def lev(a: str, b: str) -> int:
    return round((1 - difflib.SequenceMatcher(None, a, b).ratio()) * max(len(a), len(b)))


def main() -> None:
    modo, cid, *resto = sys.argv[1:]
    for c in [cid] + ([r for r in resto] if modo in ("fechas", "inventario") else []):
        raw = (OCR / f"{c}.txt").read_text(encoding="utf-8")
        if modo == "fechas":
            print(c, re.findall(r"\b\d{1,2}\s?/\s?\d{1,2}\s?/\s?\d{2,4}", raw))
        elif modo == "inventario":
            items = re.findall(r"(?im)^\W*\w?ien\s*\d{1,2}\b.*$", raw)
            malos = [i for i in items if re.search(r"inutiliz|no funciona|rot[oa]|sin funcionar|averiad", i, re.I)]
            funcionales = [i for i in items if re.search(r"funcional|uncional", i, re.I)]
            print(f"{c}: renglones de bienes={len(items)}, con 'funcional'={len(funcionales)}, con señales de no funcional={len(malos)}")
    if modo == "cifras":
        ancla, n = resto[0], int(resto[1])
        doc = norm((OCR / f"{cid}.txt").read_text(encoding="utf-8"))
        r, pos = mejores(doc, norm(ancla))
        ventana = doc[pos:].split()[: len(ancla.split()) + n]
        salida = []
        for t in ventana:
            if t.isdigit() and len(t) <= 3:
                salida.append(t)
            else:
                cand = min(NUM_PAL | {"por", "ciento", "cada", "ciclos", "dias", "horas", "canones", "base"}, key=lambda w: lev(t, w))
                salida.append(f"≈{cand}" if lev(t, cand) <= 2 and len(t) >= 2 else "·")
        print(f"{cid} ancla '{ancla}' sim {r:.2f}: {' '.join(salida)}")
    if modo == "frase":
        doc = norm((OCR / f"{cid}.txt").read_text(encoding="utf-8"))
        r, pos = mejores(doc, norm(resto[0]), paso=4)
        print(f"{cid} frase '{resto[0]}': similitud máxima {r:.2f}")


if __name__ == "__main__":
    main()
