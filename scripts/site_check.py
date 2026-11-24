#!/usr/bin/env python3
"""
Vocal DNA Studio - Revision automatica diaria.

Comprueba que la web y los datos estan sanos. Si encuentra un fallo,
termina con error: GitHub marca el proceso en rojo y avisa por correo
al dueno del repositorio. Solo usa la libreria estandar.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def main():
    # 1. Canciones
    try:
        with open(os.path.join(ROOT, "data", "generated_songs.json"), encoding="utf-8") as f:
            songs = json.load(f)
        lst = songs.get("songs", [])
        check(len(lst) >= 3, "Hay menos de 3 canciones en el catalogo")
        for s in lst:
            for key in ("id", "title", "bpm", "tonic", "mode", "chords", "drums", "melody", "lyrics", "license"):
                check(key in s, f"Cancion {s.get('id')} sin el campo {key}")
            check(40 <= s.get("bpm", 0) <= 200, f"Cancion {s.get('id')} con tempo raro")
            check(len(s.get("melody", [])) > 0, f"Cancion {s.get('id')} sin melodia")
            for lang in ("es", "en"):
                check(s.get("title", {}).get(lang), f"Cancion {s.get('id')} sin titulo {lang}")
                check(s.get("lyrics", {}).get(lang), f"Cancion {s.get('id')} sin letra {lang}")
            for n in s.get("melody", []):
                check(36 <= n.get("n", 0) <= 96, f"Cancion {s.get('id')} con nota fuera de rango")
    except Exception as e:  # noqa: BLE001
        errors.append(f"generated_songs.json no se puede leer: {e}")

    # 2. Ranking
    try:
        with open(os.path.join(ROOT, "data", "vocal_ranking.json"), encoding="utf-8") as f:
            ranking = json.load(f)
        check(isinstance(ranking.get("entries"), list), "vocal_ranking.json sin lista de entradas")
        for e in ranking.get("entries", []):
            check(0 <= e.get("score", -1) <= 100, f"Puntuacion fuera de rango: {e}")
    except Exception as e:  # noqa: BLE001
        errors.append(f"vocal_ranking.json no se puede leer: {e}")

    # 3. Web
    try:
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
            html = f.read()
        for needed in ('id="scanner"', 'id="songs"', 'id="studio"', 'id="ranking"', 'id="legal"',
                       "data/generated_songs.json", "data/vocal_ranking.json", "</html>"):
            check(needed in html, f"index.html no contiene {needed}")
        es_keys = set(re.findall(r'data-i18n="([\w.]+)"', html))
        for k in es_keys:
            # la clave aparece en la etiqueta + traduccion espanola + traduccion inglesa
            check(html.count(f'"{k}"') >= 3, f"Falta traduccion (es o en) para {k}")
    except Exception as e:  # noqa: BLE001
        errors.append(f"index.html no se puede leer: {e}")

    if errors:
        print("REVISION: se encontraron fallos:")
        for e in errors:
            print(" -", e)
        return 1
    print("REVISION: todo correcto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
