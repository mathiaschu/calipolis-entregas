#!/usr/bin/env python3
"""Anonimización local del OCR antes de que un modelo externo lea cualquier texto.

Lee ocr/<ID>.txt (texto crudo, nunca se imprime) y escribe anon/<ID>.txt.
Criterio conservador: ante la duda se tapa.
  1. Números de identificación, teléfonos y cuentas (secuencias de 6 o más dígitos,
     con o sin puntos, guiones o espacios) -> [NÚMERO].
  2. Domicilios (Calle/Avenida/Pasaje ... hasta "Calípolis" o fin de línea) -> [DOMICILIO].
  3. Nombres tras los rótulos de las partes (Locador, Locatario, Garante, Contacto técnico,
     garantía personal de, Firma, etc.) -> [NOMBRE], y esos mismos tokens en todo el documento.
  Versión 2 (después de detectar fugas en la v1 con C-301): se omite el bloque de partes entero,
  se tapan domicilios sin importar mayúsculas, números de 4 o más dígitos que no sean importes en
  calines y CUALQUIER palabra (no sólo capitalizada) que no esté en el vocabulario de referencia.
  Versión 3 (la que se usa): en lugar de recortar el bloque de partes, se omite cada renglón con
  marcas personales (rótulos de partes, DNI, CUIT, CBU, teléfono, domicilio, garantía personal);
  los tokens no comunes de esos renglones forman una lista local de nombres sensibles que se tapan
  en todo el documento (también con un error de OCR). El resto pasa por la lista blanca, aceptando
  palabras a distancia 1 del vocabulario para tolerar errores de reconocimiento.
  4. Lista blanca (v1): toda palabra con mayúscula inicial o en mayúsculas cuya forma en minúsculas
     no figure en el vocabulario de referencia (Leyes de Platón y cláusulas de los contratos de
     niveles anteriores, sin sus datos personales) ni aparezca en minúsculas en los propios OCR
     -> [?]. Así un nombre propio mal reconocido también queda tapado.
Por pantalla sólo se imprimen conteos.

Uso:
  python3 anonimizar.py --ocr ocr/ --salida anon/ --vocabulario ref1.md ref2.md ...
"""
import argparse
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROTULOS = r"(?:Locador(?:a)?|Locatari[oa]|Garante|Contacto t[ée]cnico designado|Contacto t[ée]cnico|garant[íi]a personal de|Firma|Firmado por|Aclaraci[óo]n|Recibido por|Testigo|Escribano|Certifica|Apoderad[oa])"
RE_NUM = re.compile(r"(?<![\w])(?:\+?\d[\d.\-/ ]{4,}\d)(?![\w])")
RE_DOM = re.compile(r"\b(?:Calle|Avenida|Av\.|Pasaje|Pje\.|Boulevard|Bv\.)\b[^\n]*?(?:Cal[íi]polis|$)", re.M)
RE_ROTULO = re.compile(ROTULOS + r"\s*[:.,]?\s*((?:[A-ZÁÉÍÓÚÑ][\wáéíóúñü'’-]*\.?\s*){1,4})")
RE_DOM2 = re.compile(r"\b(?:calle|avenida|av\.|pasaje|pasale|pje\.)\b.*?(?:cal[íi]polis|$)", re.I | re.M)
RE_NUM4 = re.compile(r"\d[\d.,\-/ ]{2,}\d|\d{4,}")  # con comas: corrige la fuga de C-310
RE_CABECERA_FIN = re.compile(r"c[lI1i]?[áa]?u?s?u?l?a\s*c[o0O]?[0-9oO]{1,2}", re.I)
RE_TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü][\wÁÉÍÓÚÑÜáéíóúñü'’-]*")

# Nombres sintéticos vistos en niveles anteriores: se tapan siempre, aunque coincidan con palabras.
POOL = """Nerea Bautista Iria Simón Malena Dante Alina Ciro Vera Lisandro Maia Tobías Amira Tadeo
Ardemar Caldorén Silvoria Almavec Belterra Areniel Montevia Dalmora Noveral Solerán Talvieso Selvarín
Brisanto Belmisa Veloria Mirval Olivarte Seredal Cerován Lumeras Verdeluz Feraldi""".split()


def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def vocabulario(refs: list[Path], ocr_textos: list[str]) -> set[str]:
    vocab = set()
    for r in refs:
        for linea in r.read_text(encoding="utf-8").splitlines():
            if re.search(r"DNI|CUIT|CBU|Tel[ée]fono|garant[íi]a personal de|vivienda habitual disponible en|Sentencia F-|contra ", linea):
                continue  # líneas con datos personales de los materiales de referencia
            vocab.update(sin_tildes(t.lower()) for t in RE_TOKEN.findall(linea) if not t[0].isupper())
            # palabras capitalizadas sólo al comienzo de oración del texto normativo
            vocab.update(sin_tildes(t.lower()) for t in re.findall(r"(?:^|[.:;]\s+)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)", linea))
    # Versión 2: NO se toma vocabulario de los propios OCR. El reconocimiento pasa muchas
    # iniciales a minúscula y así nombres y calles entraban como palabras comunes.
    vocab.update({"calipolis", "platon", "leyes", "oficina", "locaciones", "tribunal", "anexo", "clausula",
                  "contrato", "locacion", "inventario", "constancia", "acta", "entrega", "folio", "sello"})
    vocab -= {sin_tildes(p.lower()) for p in POOL}
    return vocab


def anonimizar(texto: str, vocab: set[str], c: Counter) -> str:
    """Versión 2 (estricta)."""
    salida = []
    for pagina in texto.split("\f"):
        # a) El bloque de partes (desde el inicio de página hasta la primera cláusula) se omite entero,
        #    salvo la línea del canon, de la que sólo se conserva el importe.
        lineas = pagina.split("\n")
        corte = next((i for i, l in enumerate(lineas) if re.search(r"^\W*c\S{0,3}usula|cl[áa]usula", l, re.I)), None)
        if corte is not None and any(re.search(r"ocador|ocatario|arante|DNI|pNI|cBU|CBU", l) for l in lineas[:corte]):
            canon = next((m.group(1) for l in lineas[:corte] for m in [re.search(r"(\d{3,5})\s*cal[i1l]nes", l)] if m), "?")
            c["bloque_partes"] += 1
            lineas = [f"[BLOQUE DE PARTES OMITIDO: datos personales] [canon reconocido: {canon} calines]"] + lineas[corte:]
        pagina = "\n".join(lineas)
        # b) domicilios en cualquier caja
        pagina, n = RE_DOM2.subn("[DOMICILIO]", pagina)
        c["domicilio"] += n
        # c) números de 4 o más dígitos salvo importes en calines
        def num(m):
            resto = pagina[m.end():m.end() + 9].lower()
            if "cal" in resto:
                return m.group(0)
            c["numero"] += 1
            return "[N]"
        pagina = RE_NUM4.sub(num, pagina)
        # d) toda palabra (en cualquier caja) fuera del vocabulario de referencia
        def tok(m):
            t = m.group(0)
            base = sin_tildes(t.strip("'’-").lower())
            if base in {sin_tildes(x.lower()) for x in POOL}:
                c["nombre"] += 1
                return "[NOMBRE]"
            if len(base) > 2 and base not in vocab:
                c["desconocida"] += 1
                return "[?]"
            return t
        salida.append(RE_TOKEN.sub(tok, pagina))
    return "\f".join(salida)


def anonimizar_v1(texto: str, vocab: set[str], c: Counter) -> str:
    nombres = set(POOL)
    for m in RE_ROTULO.finditer(texto):
        nombres.update(t for t in RE_TOKEN.findall(m.group(1)) if len(t) > 2)

    def num(m):
        if len(re.sub(r"\D", "", m.group(0))) >= 6:
            c["numero"] += 1
            return "[NÚMERO]"
        return m.group(0)

    texto = RE_NUM.sub(num, texto)
    texto, n = RE_DOM.subn("[DOMICILIO]", texto)
    c["domicilio"] += n

    def tok(m):
        t = m.group(0)
        base = t.strip("'’-")
        if base in nombres or sin_tildes(base) in {sin_tildes(x) for x in nombres}:
            c["nombre"] += 1
            return "[NOMBRE]"
        if (base[:1].isupper()) and len(base) > 1 and sin_tildes(base.lower()) not in vocab:
            c["desconocida"] += 1
            return "[?]"
        return t

    return RE_TOKEN.sub(tok, texto)

# Rótulos de partes sólo al comienzo del renglón (en el cuerpo de las cláusulas "el locador" es común).
MARCAS_PERSONALES = re.compile(r"^\W{0,4}\S{0,4}(?:ocador|ocatari|arante|ontacto)\S*\s*[:”\"'.,;-]|DNI|pNI|D N I|CUIT|CUIL|¡cu|cBU|CBU|eléfono|elefono|omicilio|reintegro", re.I)
RE_FECHA = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")


def _borrados(w: str) -> set[str]:
    return {w} | {w[:i] + w[i + 1:] for i in range(len(w))}


class Vocab:
    """Vocabulario con tolerancia a un error de OCR (distancia de borrado 1, estilo SymSpell)."""
    def __init__(self, palabras: set[str]):
        self.exactas = palabras
        self.indice = set()
        for w in palabras:
            if len(w) >= 5:
                self.indice |= _borrados(w)

    def contiene(self, w: str) -> bool:
        return w in self.exactas or (len(w) >= 5 and bool(_borrados(w) & self.indice))


def anonimizar_v3(texto: str, vocab: set[str], c: Counter, V: "Vocab") -> str:
    """Versión 3: tapa líneas con marcas personales (y sus continuaciones), recolecta localmente los
    tokens no comunes de esas líneas como nombres sensibles y los tapa en todo el documento; el resto
    del texto pasa por la lista blanca con tolerancia a un error de OCR."""
    lineas = texto.split("\n")
    sensibles = {sin_tildes(x.lower()) for x in POOL}
    marcadas = set()
    for i, l in enumerate(lineas):
        if MARCAS_PERSONALES.search(l) or re.search(r"garant\S{0,3}\s+persona\S*\s+de", l, re.I):
            marcadas.add(i)
            # continuación de un renglón personal: la línea siguiente si tiene piso/unidad/dígitos largos
            if i + 1 < len(lineas) and re.search(r"piso|unidad|\d{3,}", lineas[i + 1], re.I):
                marcadas.add(i + 1)
    for i in marcadas:
        for t in RE_TOKEN.findall(lineas[i]):
            b = sin_tildes(t.lower())
            if len(b) > 2 and b not in vocab:
                sensibles.add(b)
    for i in marcadas:
        if re.search(r"garant\S{0,3}\s+persona", lineas[i], re.I):
            lineas[i] = "[RENGLÓN CON DATOS PERSONALES OMITIDO: garantía personal]"
        else:
            canon = re.search(r"(\d{3,5})\s*cal[i1l]nes", lineas[i])
            lineas[i] = "[RENGLÓN CON DATOS PERSONALES OMITIDO]" + (f" [importe: {canon.group(1)} calines]" if canon else "")
        c["renglones_omitidos"] += 1
    texto = "\n".join(lineas)
    texto, n = RE_DOM2.subn("[DOMICILIO]", texto)
    c["domicilio"] += n

    def num(m):
        resto = texto_ref[m.end():m.end() + 10].lower()
        if RE_FECHA.match(m.group(0).strip()):
            c["fecha_conservada"] += 1
            return m.group(0)  # las fechas no son datos personales
        if "cal" in resto:
            return m.group(0)
        c["numero"] += 1
        return "[N]"
    texto_ref = texto
    texto = RE_NUM4.sub(num, texto)

    sens_idx = set()
    for w in sensibles:
        sens_idx |= _borrados(w)

    def tok(m):
        t = m.group(0)
        b = sin_tildes(t.strip("'’-").lower())
        if len(b) <= 2:
            return t
        if b in sensibles or (len(b) >= 4 and _borrados(b) & sens_idx and not b in vocab):
            c["nombre"] += 1
            return "[NOMBRE]"
        if V.contiene(b):
            return t
        c["desconocida"] += 1
        return "[?]"
    return RE_TOKEN.sub(tok, texto)


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--ocr", type=Path, required=True)
    a.add_argument("--salida", type=Path, required=True)
    a.add_argument("--vocabulario", type=Path, nargs="+", required=True)
    args = a.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    archivos = sorted(args.ocr.glob("C-*.txt"))
    textos = [p.read_text(encoding="utf-8") for p in archivos]
    vocab = vocabulario(args.vocabulario, textos)
    V = Vocab(vocab)
    for p, t in zip(archivos, textos):
        c = Counter()
        (args.salida / p.name).write_text(anonimizar_v3(t, vocab, c, V), encoding="utf-8")
        print(p.stem, dict(c))


if __name__ == "__main__":
    main()
