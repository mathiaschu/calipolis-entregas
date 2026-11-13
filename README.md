# Calípolis: entregas

Entregas del ejercicio de análisis de contratos de locación de la ciudad ficticia de Calípolis, evaluados exclusivamente con *Las Leyes de Platón* (texto consolidado vigente desde el 01/03/2026). Todas las personas, cuentas y direcciones del material original son sintéticas.

## Estructura

```
calipolis-entregas/
├── nivel-1/
│   ├── hallazgos.json    ← entrega
│   └── README.md         ← resumen del criterio aplicado
├── nivel-2/
│   ├── hallazgos.json    ← entrega (con campo fallos)
│   ├── README.md
│   └── codigo/           ← buscador de sentencias (SQLite FTS5)
├── nivel-3/ … nivel-5/   ← próximas entregas
└── scripts/
    └── validar.py        ← chequeo de formato antes de subir
```

Cada nivel tiene su propia carpeta con el archivo que pide el enunciado y un README con el resumen del análisis. El material del enunciado (leyes y contratos) no se publica acá.

## Estado

| Nivel | Entrega | Estado |
|---|---|---|
| 1 | [`nivel-1/hallazgos.json`](nivel-1/hallazgos.json) | Entregado |
| 2 | [`nivel-2/hallazgos.json`](nivel-2/hallazgos.json) y [`nivel-2/codigo/`](nivel-2/codigo/) | Entregado |
| 3 | Pendiente | |
| 4 | Pendiente | |
| 5 | Pendiente | |

## Validación de formato

```bash
python3 scripts/validar.py nivel-1/hallazgos.json
```

Verifica que el archivo sea una lista JSON en UTF-8, que cada objeto tenga exactamente los campos `contrato`, `clausula`, `articulo` y `explicacion`, que `clausula` vaya de C01 a C10, que `articulo` sea entero, que la explicación tenga entre 40 y 3.000 caracteres y que no haya cláusulas repetidas. Desde el nivel 2 también controla `fallos` (lista de hasta 8 números F-NNN sin repetir).
