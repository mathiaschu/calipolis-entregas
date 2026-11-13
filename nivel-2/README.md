# Nivel 2

Entrega: [`hallazgos.json`](hallazgos.json) con 60 cláusulas incompatibles en 20 contratos (C-201 a C-220, tres por contrato), y el buscador en [`codigo/`](codigo/).

Fecha de corte: 30/09/2026. Las 120 sentencias son anteriores a esa fecha.

## Criterio con la jurisprudencia

- Los plenarios obligan desde el tercer día de su publicación (art. 31). Las sentencias de Sala sólo son persuasivas.
- Seis plenarios revocan expresamente doctrina anterior (art. 32). Las sentencias revocadas no se citan como autoridad:

| Plenario | Revoca | Regla vigente |
|---|---|---|
| F-037 | F-014 | La batería central fija es bien común del propietario; sus cuotas no son consumo. |
| F-058 | F-022 | Las noches de visitas coincidentes se cuentan una vez: 3 visitas × 10 noches = 10, no 30. |
| F-076 | F-031 | La decoloración homogénea es desgaste normal; el pacto de pintar no crea daño. |
| F-097 | F-009 | La adhesión que sólo cubre deuda o daño integra el depósito. |
| F-104 | F-052 | Dos marcas automáticas prueban entrega técnica, no recepción del contenido. |
| F-106 | F-043 (extensión) | Una alerta aislada sin corroboración no habilita el ingreso. |

- `fallos` va vacío cuando el fundamento sale directo del texto de la ley (plazos, topes y prohibiciones expresas).

## Hallazgos por tipo de cláusula

| Tipo | Art. | Fallos | Contratos |
|---|---|---|---|
| 30 noches por 3 visitas simultáneas | 20 | F-058 | 201, 204, 208, 210, 213, 215, 220 |
| Cuotas de celdas de batería central | 16 | F-037, F-002 | 201, 206, 209, 212, 214, 218, 219 |
| Pintura completa por decoloración | 14 | F-076 | 202, 204, 207, 211, 213, 216, 219 |
| Recepción concluyente por dos marcas automáticas | 26 | F-104 | 203, 205, 207, 210, 214, 216, 220 |
| Ingreso por alerta aislada del sensor | 18 | F-106, F-089 | 202, 205, 209, 212, 215, 217 |
| Adhesión al Fondo Atenea (depósito total 1,80) | 12 | F-097 | 203, 206, 208, 211, 217, 218 |
| Indemnización de 0,90 por salida anticipada | 22 | F-003, F-115 | 206, 219 |
| Copia entregada a los 12 días | 4 | | 201, 213 |
| Tributo de la propiedad al locatario | 16 | | 202, 217 |
| Límite de peso para animales de asistencia | 19 | | 203, 215 |
| Plazo de 12 ciclos | 5 | | 204, 214 |
| Reparaciones en 30 días | 17 | | 210, 218 |
| Arancel de apertura (art. 36 derogado) | 37 | | 211, 220 |
| Depósito de 1,90 | 12 | | 205 |
| Mora de 0,25 % diario | 11 | | 207 |
| Inspección con 12 h de aviso | 18 | | 208 |
| Retención del depósito por 60 días | 14 | | 209 |
| Aumento de 12 % cada 3 ciclos | 8 | | 212 |
| Corte de agua y cambio de cerradura por deuda | 24 | | 216 |

## Cláusulas revisadas y consideradas válidas

Reintegro de consumos medidos (art. 15), cesión de habitación autorizada (art. 21), ingreso por inundación con asistencia técnica (art. 18), recupero de agua medida por 28 noches con 2,9 % (art. 20, tope 3,5 %), comunicación con respuesta expresa (art. 26 y F-104), 12 muebles con depósito de 1,65 (art. 13), estadía transitoria de 9 ciclos con constancia (art. 6), mora de 0,07 % y 2,1 % (art. 11), opción cooperativa de 8,9 % (art. 9), perro de asistencia de 24 kg (art. 19), reclamo sólo de daños imputables acreditados (art. 14) y reserva de 0,20 por 9 días (art. 14).
