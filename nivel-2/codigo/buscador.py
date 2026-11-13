#!/usr/bin/env python3
"""Buscador de sentencias del Tribunal de Locaciones de Calípolis.

Motor: SQLite FTS5 (código abierto, dominio público), ranking BM25.
Se usa desde la biblioteca estándar de Python (módulo sqlite3), sin dependencias externas.

Tres etapas, cada una en su propia función:
  1. cargar_archivo()  lee fallos/F-NNN.md y separa cada sentencia en fragmentos por sección.
  2. indexar()         crea el índice FTS5 con metadatos (número, órgano, fecha, artículos).
  3. consultar()       recupera fragmentos por BM25 y devuelve el número de sentencia de cada uno,
                       marcando si su doctrina fue revocada por un plenario a la fecha de corte (art. 32).

Uso:
  python3 buscador.py indexar  --fallos RUTA/fallos --db indice.sqlite
  python3 buscador.py consultar --db indice.sqlite "depósito restitución once días" [--articulo 14] [--hasta 30/09/2026] [--nucleo] [-n 10]
  python3 buscador.py ficha     --db indice.sqlite F-034
  python3 buscador.py tabla     --db indice.sqlite [--hasta 30/09/2026]
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

# Secciones fijas de cada sentencia publicada.
SECCIONES = {
    "I": "vistos",
    "II": "antecedentes",
    "III": "tramitacion",
    "IV": "consideraciones",
    "V": "deliberacion",
    "VI": "resolutiva",
}
# Las secciones que contienen la razón decisoria y la decisión. El resto es prueba accesoria.
NUCLEO = ("encabezado", "vistos", "antecedentes", "consideraciones", "deliberacion", "resolutiva")

RE_ENCABEZADO = re.compile(
    r"Sentencia (F-\d{3})\. (Plenario|Sala Primera|Sala Segunda)\. Publicación: (\d{2})/(\d{2})/(\d{4})"
)
RE_SECCION = re.compile(r"^(I|II|III|IV|V|VI)\. (.+)$")
RE_ARTICULOS = re.compile(r"artículos? ([\d ,y]+)")
RE_ANEXO = re.compile(r"^Anexo de actuaciones incorporadas")
# Artículo 32: un plenario puede revocar expresamente la doctrina de un fallo identificado.
RE_REVOCA = re.compile(r"Se revoca expresamente la doctrina de (F-\d{3})")


@dataclass
class Fragmento:
    seccion: str
    orden: int
    texto: str


@dataclass
class Sentencia:
    numero: str
    organo: str
    fecha: date
    articulos: list[int]
    revoca: list[str] = field(default_factory=list)
    fragmentos: list[Fragmento] = field(default_factory=list)


# ---------------------------------------------------------------- 1. carga

def _parsear(ruta: Path) -> Sentencia:
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    texto = "\n".join(lineas)
    m = RE_ENCABEZADO.search(texto)
    if not m:
        raise ValueError(f"{ruta.name}: encabezado no reconocido")
    numero, organo, d, mes, a = m.groups()
    sent = Sentencia(numero, organo, date(int(a), int(mes), int(d)), [])

    seccion, buffer, orden = "encabezado", [], 0

    def volcar():
        nonlocal orden
        cuerpo = "\n".join(l for l in buffer if l.strip()).strip()
        if cuerpo:
            sent.fragmentos.append(Fragmento(seccion, orden, cuerpo))
            orden += 1
        buffer.clear()

    for linea in lineas:
        ms = RE_SECCION.match(linea)
        if ms:
            volcar()
            seccion = SECCIONES[ms.group(1)]
            continue
        if RE_ANEXO.match(linea):
            volcar()
            seccion = "anexo"
            continue
        # Cada actuación de prueba es un fragmento propio, para no mezclarla con el núcleo.
        if linea.startswith("Actuación ") or (seccion == "anexo" and not linea.strip()):
            volcar()
            continue
        buffer.append(linea)
    volcar()

    vistos = next((f.texto for f in sent.fragmentos if f.seccion == "vistos"), "")
    ma = RE_ARTICULOS.search(vistos)
    if ma:
        sent.articulos = sorted({int(x) for x in re.findall(r"\d+", ma.group(1))})
    if sent.organo == "Plenario":
        resolutiva = " ".join(f.texto for f in sent.fragmentos if f.seccion == "resolutiva")
        sent.revoca = RE_REVOCA.findall(resolutiva)
    return sent


def cargar_archivo(carpeta: Path) -> list[Sentencia]:
    archivos = sorted(carpeta.glob("F-*.md"))
    if not archivos:
        raise FileNotFoundError(f"No hay F-*.md en {carpeta}")
    return [_parsear(p) for p in archivos]


# ---------------------------------------------------------------- 2. indexación

ESQUEMA = """
DROP TABLE IF EXISTS sentencias;
DROP TABLE IF EXISTS fragmentos;
CREATE TABLE sentencias (
    numero TEXT PRIMARY KEY,
    organo TEXT NOT NULL,
    fecha TEXT NOT NULL,          -- ISO AAAA-MM-DD
    articulos TEXT NOT NULL       -- lista separada por comas, con comas en los extremos: ",10,11,"
);
DROP TABLE IF EXISTS revocaciones;
CREATE TABLE revocaciones (
    revocado TEXT NOT NULL,       -- fallo cuya doctrina deja de ser autoridad
    plenario TEXT NOT NULL,       -- plenario que la revoca
    eficacia TEXT NOT NULL        -- tercer día desde la publicación del plenario (art. 31)
);
CREATE VIRTUAL TABLE fragmentos USING fts5(
    numero UNINDEXED,
    seccion UNINDEXED,
    orden UNINDEXED,
    texto,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""


def indexar(sentencias: list[Sentencia], db: Path) -> None:
    con = sqlite3.connect(db)
    con.executescript(ESQUEMA)
    for s in sentencias:
        con.execute(
            "INSERT INTO sentencias VALUES (?,?,?,?)",
            (s.numero, s.organo, s.fecha.isoformat(), "," + ",".join(map(str, s.articulos)) + ","),
        )
        for revocado in s.revoca:
            con.execute("INSERT INTO revocaciones VALUES (?,?,?)",
                        (revocado, s.numero, (s.fecha + timedelta(days=3)).isoformat()))
        con.executemany(
            "INSERT INTO fragmentos (numero, seccion, orden, texto) VALUES (?,?,?,?)",
            [(s.numero, f.seccion, f.orden, f.texto) for f in s.fragmentos],
        )
    con.commit()
    total = con.execute("SELECT count(*) FROM fragmentos").fetchone()[0]
    con.close()
    print(f"Indexadas {len(sentencias)} sentencias en {total} fragmentos -> {db}")


# ---------------------------------------------------------------- 3. consulta

def _fecha_iso(ddmmaaaa: str) -> str:
    d, m, a = ddmmaaaa.split("/")
    return f"{a}-{m}-{d}"


def _a_match(consulta: str) -> str:
    """Convierte texto libre en una expresión FTS5 OR de términos (los tokens entre comillas se respetan)."""
    frases = re.findall(r'"([^"]+)"', consulta)
    resto = re.sub(r'"[^"]+"', " ", consulta)
    terminos = [t for t in re.findall(r"\w+", resto, flags=re.UNICODE) if len(t) > 2]
    partes = [f'"{f}"' for f in frases] + [f'"{t}"' for t in terminos]
    return " OR ".join(partes) if partes else '""'


def consultar(db: Path, consulta: str, n: int = 10, articulo: int | None = None,
              hasta: str | None = None, nucleo: bool = False) -> list[dict]:
    con = sqlite3.connect(db)
    sql = [
        "SELECT f.numero, s.organo, s.fecha, s.articulos, f.seccion, bm25(fragmentos) AS score,",
        "       snippet(fragmentos, 3, '[', ']', ' … ', 40) AS fragmento,",
        "       (SELECT r.plenario FROM revocaciones r WHERE r.revocado = f.numero",
        "          AND (? IS NULL OR r.eficacia <= ?)) AS revocado_por",
        "FROM fragmentos f JOIN sentencias s ON s.numero = f.numero",
        "WHERE fragmentos MATCH ?",
    ]
    corte = _fecha_iso(hasta) if hasta else None
    params: list = [corte, corte, _a_match(consulta)]
    if articulo is not None:
        sql.append("AND s.articulos LIKE ?")
        params.append(f"%,{articulo},%")
    if hasta:
        sql.append("AND s.fecha <= ?")
        params.append(_fecha_iso(hasta))
    if nucleo:
        sql.append(f"AND f.seccion IN ({','.join('?' * len(NUCLEO))})")
        params.extend(NUCLEO)
    sql.append("ORDER BY score LIMIT ?")
    params.append(n)
    filas = con.execute("\n".join(sql), params).fetchall()
    con.close()
    cols = ("numero", "organo", "fecha", "articulos", "seccion", "score", "fragmento", "revocado_por")
    return [dict(zip(cols, f)) for f in filas]


def ficha(db: Path, numero: str) -> str:
    """Devuelve el núcleo de una sentencia (sin las actuaciones de prueba)."""
    con = sqlite3.connect(db)
    meta = con.execute("SELECT * FROM sentencias WHERE numero = ?", (numero,)).fetchone()
    if not meta:
        raise SystemExit(f"{numero} no está en el índice")
    frags = con.execute(
        f"SELECT seccion, texto FROM fragmentos WHERE numero = ? AND seccion IN ({','.join('?' * len(NUCLEO))}) ORDER BY orden",
        (numero, *NUCLEO),
    ).fetchall()
    con.close()
    salida = [f"{meta[0]} | {meta[1]} | {meta[2]} | arts. {meta[3].strip(',')}"]
    salida += [f"[{s}] {t}" for s, t in frags]
    return "\n".join(salida)


def tabla(db: Path, hasta: str | None = None) -> str:
    con = sqlite3.connect(db)
    q = "SELECT s.numero, s.organo, s.fecha, s.articulos, f.texto FROM sentencias s JOIN fragmentos f ON f.numero = s.numero AND f.seccion = 'resolutiva'"
    params: list = []
    if hasta:
        q += " WHERE s.fecha <= ?"
        params.append(_fecha_iso(hasta))
    filas = con.execute(q + " ORDER BY s.numero", params).fetchall()
    con.close()
    return "\n".join(f"{n} | {o} | {f} | arts. {a.strip(',')} | {t.splitlines()[0][:220]}" for n, o, f, a, t in filas)


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("indexar", help="Carga fallos/ y construye el índice")
    pi.add_argument("--fallos", type=Path, required=True)
    pi.add_argument("--db", type=Path, default=Path("indice.sqlite"))

    pc = sub.add_parser("consultar", help="Busca fragmentos por BM25")
    pc.add_argument("consulta")
    pc.add_argument("--db", type=Path, default=Path("indice.sqlite"))
    pc.add_argument("-n", type=int, default=10)
    pc.add_argument("--articulo", type=int)
    pc.add_argument("--hasta", help="Fecha de corte DD/MM/AAAA (excluye publicaciones posteriores)")
    pc.add_argument("--nucleo", action="store_true", help="Sólo secciones decisorias, sin actuaciones de prueba")

    pf = sub.add_parser("ficha", help="Muestra el núcleo de una sentencia")
    pf.add_argument("numero")
    pf.add_argument("--db", type=Path, default=Path("indice.sqlite"))

    pt = sub.add_parser("tabla", help="Lista sentencias con órgano, fecha, artículos y resolutiva")
    pt.add_argument("--db", type=Path, default=Path("indice.sqlite"))
    pt.add_argument("--hasta")

    a = p.parse_args(argv)
    if a.cmd == "indexar":
        indexar(cargar_archivo(a.fallos), a.db)
    elif a.cmd == "consultar":
        for r in consultar(a.db, a.consulta, a.n, a.articulo, a.hasta, a.nucleo):
            estado = f"REVOCADA por {r['revocado_por']}" if r["revocado_por"] else "vigente"
            print(f"{r['numero']} | {r['organo']} | {r['fecha']} | arts. {r['articulos'].strip(',')} | {r['seccion']} | {estado} | {r['score']:.2f}")
            print(f"    {r['fragmento']}")
    elif a.cmd == "ficha":
        print(ficha(a.db, a.numero))
    elif a.cmd == "tabla":
        print(tabla(a.db, a.hasta))


if __name__ == "__main__":
    sys.exit(main())
