# Buscador de sentencias (nivel 2)

Buscador de texto completo sobre el archivo del Tribunal de Locaciones de Calípolis (120 sentencias), usado para encontrar la doctrina que fundamenta cada hallazgo.

**Motor:** SQLite FTS5, buscador de texto completo de código abierto (dominio público), con ranking BM25. Se usa a través del módulo `sqlite3` de la biblioteca estándar de Python, así que no hay dependencias que instalar.

## Entradas

- `fallos/F-NNN.md`: las 120 sentencias del enunciado (no se incluyen en el repo).
- Fecha de corte del expediente: 30/09/2026 (parámetro `--hasta`).

## Instalación

Requiere Python 3.9 o superior con SQLite compilado con FTS5 (es el caso de las distribuciones oficiales de Python en macOS, Linux y Windows).

```bash
python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(x)')" && echo FTS5 OK
```

## Cómo está armado (`buscador.py`)

| Etapa | Función | Qué hace |
|---|---|---|
| Carga | `cargar_archivo()` / `_parsear()` | Lee cada `F-NNN.md`, extrae número, órgano (Sala Primera, Sala Segunda o Plenario), fecha de publicación y artículos tratados, y separa el texto en fragmentos por sección (vistos, antecedentes, consideraciones, deliberación, parte resolutiva). Cada actuación de prueba y del anexo queda como fragmento aparte, para que no tape la razón decisoria. En los plenarios detecta las revocaciones expresas (`Se revoca expresamente la doctrina de F-NNN`). |
| Indexación | `indexar()` | Crea la tabla virtual FTS5 `fragmentos` (tokenizador `unicode61` sin diacríticos, así "deposito" encuentra "depósito"), la tabla `sentencias` con los metadatos y la tabla `revocaciones` con la eficacia de cada revocación (tercer día desde la publicación, artículo 31). |
| Consulta | `consultar()` | Recupera fragmentos por BM25 y devuelve el número de sentencia, órgano, fecha, artículos, sección, un extracto con los términos marcados y si la doctrina está **vigente** o **revocada** a la fecha de corte (artículo 32). Filtros: `--articulo`, `--hasta`, `--nucleo` (sólo secciones decisorias). |

Comandos auxiliares: `ficha` muestra el núcleo de una sentencia sin las actuaciones de prueba y `tabla` lista todas con su parte resolutiva.

## Comandos

```bash
# 1. Indexar
python3 buscador.py indexar --fallos ../../material/nivel-2/fallos --db indice.sqlite

# 2. Consultar
python3 buscador.py consultar --db indice.sqlite --nucleo --hasta 30/09/2026 -n 5 "noches coincidentes invitados"

# 3. Leer el núcleo de una sentencia
python3 buscador.py ficha --db indice.sqlite F-058
```

Salida de ejemplo de la consulta:

```
F-058 | Plenario | 2026-05-26 | arts. 20 | resolutiva | vigente | -32.10
    Se cuentan las noches efectivas de ocupación de [invitados] en el ciclo; [noches] [coincidentes] se cuentan una vez. …
F-022 | Sala Primera | 2026-04-02 | arts. 20 | resolutiva | REVOCADA por F-058 | -22.97
    Para el artículo 20 se suman personas por noches; tres [invitados] que coinciden diez [noches] computan treinta …
```

`indice.sqlite` es un archivo generado: no se versiona.

## Consultas usadas para los hallazgos

| Tema de la cláusula | Consulta | Doctrina citada |
|---|---|---|
| Cómputo de noches de visitas (art. 20) | `noches coincidentes invitados` | F-058 (plenario, revoca F-022) |
| Cuotas de batería central (arts. 15 y 16) | `batería central cuotas bien común` | F-037 (plenario, revoca F-014); F-002 |
| Pintura por decoloración (art. 14) | `decoloración pintar desgaste normal` | F-076 (plenario, revoca F-031) |
| Marcas automáticas de entrega (art. 26) | `marcas plataforma recepción humana` | F-104 (plenario, revoca F-052) |
| Ingreso por alerta aislada (art. 18) | `alerta aislada corroboración acceso` | F-106 (plenario, revoca la extensión de F-043); F-089 |
| Adhesión al Fondo Atenea (arts. 12 y 25) | `adhesión cobertura depósito no reintegrable` | F-097 (plenario, revoca F-009) |
| Indemnización por salida anticipada (art. 22) | `salida anticipada indemnización preaviso` --articulo 22 | F-003, F-115 |
