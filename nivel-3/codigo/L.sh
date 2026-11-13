#!/bin/bash
# Registra cada comando y su salida completa (lo que ve el modelo externo) en enviado/NNN.txt
S=/private/tmp/claude-501/-Users-MathiasChu-Documents-Claude-Code/9a2989f7-6591-400c-b204-578305abc01f/scratchpad
n=$(ls $S/enviado | grep -c '^[0-9]')
f=$(printf "%s/enviado/%03d-salida-herramienta.txt" $S $((n+1)))
out=$(bash -c "$1" 2>&1)
{ printf "COMANDO EJECUTADO LOCALMENTE:\n%s\n\nSALIDA RECIBIDA POR EL MODELO:\n%s\n" "$1" "$out"; } > "$f"
printf "%s\n" "$out"
