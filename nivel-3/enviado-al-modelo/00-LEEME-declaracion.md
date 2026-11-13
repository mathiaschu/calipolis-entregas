# Declaración de envíos a modelos externos (nivel 3)

En este nivel se usó un modelo externo: el asistente de programación (Claude, de Anthropic) que operó las herramientas locales. Todo lo que ese modelo leyó cuenta como enviado a un modelo externo. Esta carpeta lo declara.

## Qué contiene esta carpeta

- `000-enunciado-y-primeras-salidas.txt`: las instrucciones del usuario en este nivel ("Inténtalo de nuevo" y "El nivel 3"), el listado del ZIP y el enunciado, tal como los recibió el modelo, más la primera consulta de herramientas disponibles.
- `NNN-salida-herramienta.txt`: un archivo por cada comando ejecutado en este intento, con el comando y la salida completa que recibió el modelo. Se generaron automáticamente con un envoltorio (`L`) que guarda la salida antes de mostrarla.
- `intento-anterior/`: el registro que dejó un intento anterior de este mismo nivel, interrumpido antes de terminar. Se copió sin abrirlo. Puede estar incompleto: solo tiene un archivo, numerado 10.

## Qué NO se envió

- Ninguna imagen de los contratos. Los PDF se procesaron solo con herramientas locales (pdfimages, ImageMagick y Tesseract con el modelo `spa` de tessdata_best).
- El texto crudo del OCR no se leyó directamente, con la excepción declarada abajo.

## Incidentes: datos personales que llegaron al modelo

Hay que declararlos porque contradicen la regla del enunciado.

1. **C-301, primera versión de la anonimización** (archivo `015-salida-herramienta.txt`). El OCR pasó muchas iniciales a minúscula, y el filtro v1 solo tapaba palabras capitalizadas. Por eso el modelo recibió nombres, apellidos y domicilios de las partes de C-301, con errores de reconocimiento. Después se pasó a las versiones 2 y 3, más estrictas.
2. **C-302 a C-304, versión 2** (`017-salida-herramienta.txt`) y **C-304 y C-305, versión 3** (`019-salida-herramienta.txt`). Siguen tapados casi todos los datos, pero en C-304 se ve un fragmento de apellido partido por el OCR ("soler an"), y en C-305 algunos fragmentos sueltos de la cabecera.
3. **Revisión de líneas no explicadas** (`021-salida-herramienta.txt`; el modelo leyó la misma salida desde un archivo temporal porque era larga). En C-310 aparecen dos números de documento separados por comas, que el patrón de números no contemplaba, y algunos fragmentos sueltos de apellidos y calles.

Desde ese punto se dejó de leer texto del OCR. La clasificación se hizo en local, contra el catálogo de cláusulas de los niveles anteriores, y el modelo solo recibió claves, puntajes, conteos, fechas y ventanas cortas de texto contractual.

## Contexto previo que también tenía el modelo

La conversación arrastraba los niveles 1 y 2: sus enunciados, las Leyes de Platón, las cláusulas de los contratos C-101 a C-103 y C-201 a C-220, los núcleos de las 120 sentencias y los hallazgos entregados. Ese material no contiene datos del nivel 3. Está publicado en las carpetas `nivel-1/` y `nivel-2/` de este repositorio (los hallazgos y el buscador) y en el material original del ejercicio.

El modelo también recibió la configuración privada del usuario que lo opera (instrucciones generales del entorno y preferencias personales), que no tiene relación con el expediente. No se reproduce acá porque son datos privados del usuario y no contienen información de los contratos.

El último comando, el que publica esta carpeta en el repositorio, no puede incluir su propia salida. Esa salida es la confirmación de `git push`.
