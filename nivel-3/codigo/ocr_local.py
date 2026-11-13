#!/usr/bin/env python3
"""OCR local de los contratos del nivel 3 con Tesseract (modelo spa de tessdata_best).

Todo corre en esta máquina: no se envía ninguna imagen ni texto a servicios externos.
Por cada PDF: extrae las imágenes de página tal como vienen (pdfimages, sin re-muestreo),
preprocesa con ImageMagick, detecta orientación con OSD y reconoce con Tesseract. El texto crudo se guarda en
ocr/<ID>.txt, en orden de páginas, sin corregir errores. Por pantalla sólo imprime
estadísticas numéricas (páginas, palabras, confianza media), nunca el texto.

Uso:
  TESSDATA_PREFIX=ruta/tessdata python3 ocr_local.py --pdfs contratos/ --salida ocr/ --tmp trabajo/
"""
import argparse
import csv
import io
import shutil
import subprocess
from pathlib import Path


def paginas(pdf: Path, tmp: Path) -> list[Path]:
    destino = tmp / pdf.stem
    shutil.rmtree(destino, ignore_errors=True)  # sin restos de corridas anteriores
    destino.mkdir(parents=True)
    subprocess.run(["pdfimages", "-png", str(pdf), str(destino / "p")], check=True)
    return sorted(destino.glob("p-[0-9][0-9][0-9].png"))


def preprocesar(img: Path, tmp: Path) -> Path:
    """Escala de grises, x2, enderezado, normalización, limpieza de motas y niveles (ImageMagick local).
    Se eligió comparando palabras reconocidas y confianza media en una página de prueba."""
    salida = tmp / f"{img.stem}-pre.png"
    subprocess.run(["magick", str(img), "-colorspace", "Gray", "-resize", "200%", "-deskew", "40%",
                    "-normalize", "-despeckle", "-level", "10%,90%", str(salida)], check=True)
    return salida


def rotacion(img: Path) -> int:
    r = subprocess.run(["tesseract", str(img), "-", "--psm", "0", "-l", "osd"],
                       capture_output=True, text=True)
    for linea in r.stdout.splitlines():
        if linea.startswith("Rotate:"):
            return int(linea.split(":")[1])
    return 0


def reconocer(img: Path, grados: int, tmp: Path) -> tuple[str, float, int]:
    fuente = img
    if grados:
        fuente = tmp / f"{img.stem}-rot.png"
        subprocess.run(["magick", str(img), "-rotate", str(grados), str(fuente)], check=True)
    # psm 6 (bloque uniforme): el análisis automático de diseño (psm 1/3) no detecta texto en estos escaneos.
    texto = subprocess.run(["tesseract", str(fuente), "-", "-l", "spa", "--psm", "6"],
                           capture_output=True, text=True, check=True).stdout
    tsv = subprocess.run(["tesseract", str(fuente), "-", "-l", "spa", "--psm", "6", "tsv"],
                         capture_output=True, text=True, check=True).stdout
    confs = [float(r["conf"]) for r in csv.DictReader(io.StringIO(tsv), delimiter="\t")
             if r.get("text", "").strip() and float(r["conf"]) >= 0]
    return texto, (sum(confs) / len(confs) if confs else 0.0), len(confs)


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--pdfs", type=Path, required=True)
    a.add_argument("--salida", type=Path, required=True)
    a.add_argument("--tmp", type=Path, required=True)
    args = a.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(args.pdfs.glob("C-*.pdf")):
        partes = []
        for i, img in enumerate(paginas(pdf, args.tmp), 1):
            pre = preprocesar(img, args.tmp / pdf.stem)
            grados = rotacion(pre)
            texto, conf, palabras = reconocer(pre, grados, args.tmp / pdf.stem)
            partes.append(texto)
            print(f"{pdf.stem} página {i}: rotación {grados}°, {palabras} palabras, confianza media {conf:.1f}")
        # Tesseract ya separa cada página con un salto de página (\f); se concatena tal cual.
        (args.salida / f"{pdf.stem}.txt").write_text("".join(partes), encoding="utf-8")


if __name__ == "__main__":
    main()
