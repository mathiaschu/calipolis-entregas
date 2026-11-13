# Nivel 3

Diez contratos escaneados en PDF (C-301 a C-310). El OCR y la anonimización se hicieron en local.

- [`hallazgos.json`](hallazgos.json): 30 cláusulas incompatibles, tres por contrato, con el mismo formato que el nivel 2.
- [`ocr/`](ocr/): el texto crudo de Tesseract, un archivo por contrato, en orden de páginas y sin correcciones (los saltos de página son el carácter `\f` que emite Tesseract).
- [`enviado-al-modelo/`](enviado-al-modelo/): todo lo que leyó el modelo externo, comando por comando. Hay que leer primero [`00-LEEME-declaracion.md`](enviado-al-modelo/00-LEEME-declaracion.md), **que declara tres incidentes de datos personales que llegaron al modelo**.
- [`codigo/`](codigo/): el proceso completo.

## Proceso

1. **OCR local** (`ocr_local.py`). `pdfimages` extrae cada página. ImageMagick la pasa a gris, la escala x2, la endereza y la normaliza. Tesseract 5 con el modelo `spa` de tessdata_best detecta la orientación (una página de C-307 viene girada 90°) y reconoce en modo bloque (`--psm 6`), porque el análisis automático de diseño no encontraba texto en estos escaneos. La confianza media por página va de 48 a 95.
2. **Anonimización local** (`anonimizar.py`, v3). Omite los renglones con datos de las partes y tapa domicilios, números largos y toda palabra fuera de una lista blanca armada con las Leyes y las cláusulas de niveles previos. Los nombres detectados se tapan en todo el documento.
3. **Clasificación local sin leer el OCR** (`clasificar.py`, `revisar.py`, `chequeos.py`, `ventana.py`). Cada cláusula se ubica, por similitud (difflib), contra el catálogo de 36 redacciones ya analizadas en los niveles 1 y 2. El modelo recibió solo claves, puntajes, diferencias de cifras, conteos, fechas y ventanas cortas de texto contractual. Las 100 cláusulas coincidieron con una redacción conocida, con similitud entre 0,57 y 1,00.
4. **Hallazgos** (`armar_hallazgos.py`, `reglas.py`). Cada cláusula toma el veredicto, el artículo, los fallos y la explicación de su redacción conocida. Las explicaciones nombran a las partes por su rol.

## Verificaciones puntuales hechas en local

- C-310 C03 (cooperativa de 8,9 % cada 4 ciclos): el anexo dice "ningún hogar de esta unidad tiene constancia de protección". Es válida.
- C-310 C05: "treinta días" para reparaciones. Es incompatible (art. 17).
- C-305 C06: se computan treinta noches por tres visitas simultáneas. Es incompatible (art. 20, F-058).
- C-308 C08: el depósito ordinario es de 1,35 más la adhesión de 0,45. Es incompatible (art. 12, F-097).
- Inventarios de las cláusulas de 12 muebles con depósito de 1,65 (C-301, C-303, C-307): tienen 12, 12 y 11 o 12 renglones de bienes, más que los 9 que exige el art. 13. Son válidas.
- Estadías transitorias (C-302, C-305, C-309): la constancia es anterior a la firma y hay otra vivienda habitual. Son válidas.

## Hallazgos

| Contrato | Cláusulas incompatibles (artículo) |
|---|---|
| C-301 | C01 mora 0,25 % (11), C02 plazo de 12 ciclos (5), C10 peso de animales de asistencia (19) |
| C-302 | C01 copia a los 12 días (4), C06 tributo de la propiedad (16), C08 aumento de 12 % cada 3 ciclos (8) |
| C-303 | C02 inspección con 12 h (18), C06 pintura por decoloración (14, F-076), C08 indemnización de 0,90 (22) |
| C-304 | C02 reparaciones en 30 días (17), C03 depósito de 1,90 (12), C05 cuotas de batería (16, F-037) |
| C-305 | C05 corte de agua y cerradura (24), C06 30 noches de visitas (20, F-058), C07 retención de 60 días (14) |
| C-306 | C05 arancel de apertura (37), C09 aumento de 12 % (8), C10 ingreso por alerta aislada (18, F-106) |
| C-307 | C04 plazo de 12 ciclos (5), C06 dos marcas automáticas (26, F-104), C08 peso de animales de asistencia (19) |
| C-308 | C03 indemnización de 0,90 (22), C06 copia a los 12 días (4), C08 Fondo Atenea (12, F-097) |
| C-309 | C01 mora 0,25 % (11), C04 tributo de la propiedad (16), C09 depósito de 1,90 (12) |
| C-310 | C02 inspección con 12 h (18), C05 reparaciones en 30 días (17), C07 corte de agua y cerradura (24) |
