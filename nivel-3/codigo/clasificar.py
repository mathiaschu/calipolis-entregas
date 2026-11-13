#!/usr/bin/env python3
"""Clasificación local de cláusulas: compara el OCR crudo con un catálogo de redacciones ya
analizadas en los niveles 1 y 2, sin mostrar el texto del OCR.

Catálogo: cada redacción distinta de cláusula de los contratos C-1xx y C-2xx (sin datos personales:
las cláusulas no los contienen) con su veredicto previo, tomado de los hallazgos entregados
(artículo si fue incompatible, "válida" si no figuraba).

Para cada contrato busca, con ventanas deslizantes y difflib, dónde aparece cada redacción del
catálogo en el OCR normalizado, lee el número de cláusula de los caracteres previos y reporta sólo:
contrato, número de cláusula leído, clave del catálogo, puntaje de similitud y veredicto.

Uso:
  python3 clasificar.py --ocr ocr/ --contratos-previos C-1*.md C-2*.md --hallazgos-previos n1.json n2.json
"""
import argparse
import difflib
import json
import re
import unicodedata
from pathlib import Path


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def catalogo(contratos: list[Path], hallazgos: list[Path]) -> dict[str, dict]:
    veredictos = {}
    for h in hallazgos:
        for r in json.loads(h.read_text(encoding="utf-8")):
            veredictos[(r["contrato"], r["clausula"])] = r["articulo"]
    cat = {}
    for p in contratos:
        t = p.read_text(encoding="utf-8")
        for cl, texto in re.findall(r"^Cláusula (C\d\d)\. (.+)$", t, re.M):
            k = norm(texto)
            if k not in cat:
                cat[k] = {"clave": f"K{len(cat) + 1:02d}", "ejemplo": f"{p.stem}/{cl}",
                          "articulo": veredictos.get((p.stem, cl)), "texto": texto}
    return cat


def mejores(doc: str, frase: str, paso: int = 8) -> tuple[float, int]:
    n = len(frase)
    best, pos = 0.0, -1
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(frase)
    for i in range(0, max(1, len(doc) - n // 2), paso):
        sm.set_seq1(doc[i:i + n])
        if sm.real_quick_ratio() < best or sm.quick_ratio() < best:
            continue
        r = sm.ratio()
        if r > best:
            best, pos = r, i
    return best, pos


RE_NUM_CLAUSULA = re.compile(r"c\s?([0o]?\s?[0-9o]{1,2})\s*$")


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--ocr", type=Path, required=True)
    a.add_argument("--contratos-previos", type=Path, nargs="+", required=True)
    a.add_argument("--hallazgos-previos", type=Path, nargs="+", required=True)
    a.add_argument("--umbral", type=float, default=0.55)
    a.add_argument("--json", type=Path, help="guardar resultados para el armado de hallazgos")
    args = a.parse_args()
    cat = catalogo(args.contratos_previos, args.hallazgos_previos)
    print(f"Catálogo: {len(cat)} redacciones distintas")
    resultados = {}
    for p in sorted(args.ocr.glob("C-*.txt")):
        doc = norm(p.read_text(encoding="utf-8"))
        hall = []
        for k, info in cat.items():
            r, pos = mejores(doc, k)
            if r >= args.umbral:
                previo = doc[max(0, pos - 14):pos]
                m = RE_NUM_CLAUSULA.search(previo)
                num = m.group(1).replace(" ", "").replace("o", "0") if m else "?"
                hall.append((pos, num, info["clave"], round(r, 2), info["articulo"], info["ejemplo"]))
        hall.sort()
        resultados[p.stem] = hall
        print(f"== {p.stem}: {len(hall)} coincidencias")
        for pos, num, clave, r, art, ej in hall:
            print(f"   pos {pos:5d} | cláusula leída c{num:>2} | {clave} ({ej}) | sim {r:.2f} | "
                  f"{'art. ' + str(art) if art else 'válida en niveles previos'}")
    if args.json:
        args.json.write_text(json.dumps({"catalogo": {v["clave"]: {k2: v[k2] for k2 in ("ejemplo", "articulo", "texto")} for v in cat.values()},
                                         "resultados": resultados}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
