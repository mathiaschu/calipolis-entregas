#!/usr/bin/env python3
"""Valida el formato de un hallazgos.json antes de entregarlo."""
import json
import re
import sys

CAMPOS = {"contrato", "clausula", "articulo", "explicacion"}
CAMPOS_CON_FALLOS = CAMPOS | {"fallos"}  # desde el nivel 2


def validar(ruta: str) -> list[str]:
    errores = []
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    if not isinstance(datos, list):
        return ["La raíz tiene que ser una lista."]
    vistos = set()
    esperados = CAMPOS_CON_FALLOS if datos and isinstance(datos[0], dict) and "fallos" in datos[0] else CAMPOS
    for i, fila in enumerate(datos, 1):
        if not isinstance(fila, dict):
            errores.append(f"Fila {i}: no es un objeto.")
            continue
        if set(fila) != esperados:
            errores.append(f"Fila {i}: campos {sorted(fila)}, se esperan {sorted(esperados)}.")
            continue
        if "fallos" in fila:
            fs = fila["fallos"]
            if not isinstance(fs, list) or len(fs) > 8 or len(set(fs)) != len(fs) \
                    or not all(isinstance(x, str) and re.fullmatch(r"F-\d{3}", x) for x in fs):
                errores.append(f"Fila {i}: fallos tiene que ser una lista de hasta 8 F-NNN sin repetir.")
        if not isinstance(fila["contrato"], str) or not fila["contrato"].strip():
            errores.append(f"Fila {i}: contrato vacío o no es texto.")
        if not isinstance(fila["clausula"], str) or not re.fullmatch(r"C(0[1-9]|10)", fila["clausula"]):
            errores.append(f"Fila {i}: clausula '{fila['clausula']}' fuera de C01 a C10.")
        if type(fila["articulo"]) is not int:
            errores.append(f"Fila {i}: articulo no es entero.")
        exp = fila["explicacion"]
        if not isinstance(exp, str) or not 40 <= len(exp) <= 3000:
            errores.append(f"Fila {i}: explicacion con {len(exp) if isinstance(exp, str) else '?'} caracteres (40 a 3000).")
        clave = (fila["contrato"], fila["clausula"])
        if clave in vistos:
            errores.append(f"Fila {i}: {clave[0]} {clave[1]} repetida.")
        vistos.add(clave)
    return errores


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python3 scripts/validar.py nivel-N/hallazgos.json")
    errores = validar(sys.argv[1])
    if errores:
        print("\n".join(errores))
        sys.exit(1)
    print(f"OK: {sys.argv[1]}")
