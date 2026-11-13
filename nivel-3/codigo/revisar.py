#!/usr/bin/env python3
"""Segunda pasada local: qué del OCR NO está explicado por textos conocidos.

1. Por cada cláusula ubicada por clasificar.py, compara las cifras (números en dígitos y en letras)
   del OCR con las de la redacción del catálogo y reporta sólo las diferencias.
2. Recorre el texto ANONIMIZADO línea por línea y muestra únicamente las líneas que no se parecen a
   ningún párrafo conocido (cláusulas y anexos de niveles previos sin datos personales): sellos,
   notas, fechas y anexos nuevos. Las fechas no se tapan porque no son datos personales.

Uso:
  python3 revisar.py --ocr ocr/ --anon anon/ --clasif clasif.json --conocidos C-1*.md C-2*.md
"""
import argparse
import difflib
import json
import re
from pathlib import Path

from clasificar import norm

NUM_PAL = set("""cero uno una dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince
dieciseis diecisiete dieciocho diecinueve veinte veintiuno veintidos veintitres veinticuatro veinticinco
veintiseis veintisiete veintiocho veintinueve treinta cuarenta cincuenta sesenta setenta ochenta noventa
cien ciento coma""".split())


def cifras(s: str) -> list[str]:
    return [t for t in s.split() if t in NUM_PAL or t.isdigit()]


def parrafos_conocidos(paths: list[Path]) -> list[str]:
    out = []
    for p in paths:
        for par in p.read_text(encoding="utf-8").split("\n\n"):
            if re.search(r"DNI|CUIT|CBU|garant[íi]a personal de|vivienda habitual disponible|Locador:|Locatario:|Garante:|Contacto", par):
                continue
            out.append(norm(par))
    return out


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--ocr", type=Path, required=True)
    a.add_argument("--anon", type=Path, required=True)
    a.add_argument("--clasif", type=Path, required=True)
    a.add_argument("--conocidos", type=Path, nargs="+", required=True)
    args = a.parse_args()
    data = json.loads(args.clasif.read_text(encoding="utf-8"))
    cat = data["catalogo"]
    conocidos = " | ".join(parrafos_conocidos(args.conocidos))
    for cid, hall in data["resultados"].items():
        doc = norm((args.ocr / f"{cid}.txt").read_text(encoding="utf-8"))
        # deduplicar coincidencias superpuestas: queda la de mayor similitud
        elegidas = []
        for pos, num, clave, r, art, ej in sorted(hall, key=lambda h: -h[3]):
            if all(abs(pos - e[0]) > 90 for e in elegidas):
                elegidas.append((pos, num, clave, r, art, ej))
        elegidas.sort()
        print(f"== {cid}: {len(elegidas)} cláusulas")
        for i, (pos, num, clave, r, art, ej) in enumerate(elegidas, 1):
            ref = norm(cat[clave]["texto"])
            ventana = doc[pos:pos + len(ref) + 10]
            c_ref, c_ocr = cifras(ref), cifras(ventana)
            dif = "" if c_ref == c_ocr else f" | CIFRAS catálogo={' '.join(c_ref)} || ocr={' '.join(c_ocr)}"
            print(f"  C{i:02d} {clave} sim {r:.2f} {'art.' + str(art) if art else 'válida'}{dif}")
        print("  -- líneas no explicadas por textos conocidos (anonimizadas):")
        sm = difflib.SequenceMatcher(autojunk=False)
        sm.set_seq2(conocidos)
        for linea in (args.anon / f"{cid}.txt").read_text(encoding="utf-8").replace("\f", "\n").split("\n"):
            n = norm(linea)
            if len(n) < 4:
                continue
            sm.set_seq1(n)
            m = sm.find_longest_match(0, len(n), 0, len(conocidos))
            if m.size / len(n) < 0.45:
                print("     " + linea.strip())


if __name__ == "__main__":
    main()
