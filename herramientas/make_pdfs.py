"""Genera un PDF por documento a partir de imágenes JPG digitalizadas.

Uso: python -I make_pdfs.py <carpeta_origen> <carpeta_destino>

Nombres esperados: FONDO_SS_CCC_DDD_PPP.jpg (fondo, serie, carpeta, documento, página).
Cada PDF se llama FONDO_SS_CCC_DDD.pdf y se guarda sin subcarpetas en el destino.
El documento 000 o la página 000 (prueba de color) se descartan. Los .txt son notas: no cuentan.
Los JPG se incrustan sin recomprimir.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

import img2pdf

PATTERN = re.compile(r"^([A-Za-z]+_\d{1,2}_\d{3}_(\d{3}))_(\d{3})\.jpe?g$", re.IGNORECASE)


def es_prueba_color(m):
    """Indica si un nombre ya casado con PATTERN es una prueba de color (_000_000 o _DDD_000)."""
    return "000" in m.group(2, 3)


def pruebas_color(src):
    """Devuelve las rutas de las pruebas de color de src."""
    return [f for f in Path(src).rglob("*") if f.is_file()
            and (m := PATTERN.match(f.name)) and es_prueba_color(m)]


def agrupar(src):
    """Devuelve ({documento: [(página, ruta), ...]}, [archivos que no cumplen el patrón])."""
    docs = defaultdict(list)
    skipped = []
    for f in Path(src).rglob("*"):
        if not f.is_file() or f.suffix.lower() == ".txt":
            continue
        m = PATTERN.match(f.name)
        if not m:
            skipped.append(f.name)
            continue
        if es_prueba_color(m):
            continue
        docs[m.group(1)].append((int(m.group(3)), f))
    return {doc: sorted(items) for doc, items in sorted(docs.items())}, skipped


def generar_pdfs(src, dst):
    """Crea un PDF por documento en dst. Devuelve (nº PDFs, nº páginas, ignorados)."""
    dst = Path(dst)
    dst.mkdir(exist_ok=True)
    docs, skipped = agrupar(src)
    pages = 0
    for doc, items in docs.items():
        files = [str(f) for _, f in items]
        (dst / f"{doc}.pdf").write_bytes(img2pdf.convert(files))
        pages += len(files)
    return len(docs), pages, skipped


if __name__ == "__main__":
    n, pages, skipped = generar_pdfs(sys.argv[1], sys.argv[2])
    print(f"PDFs: {n}  paginas: {pages}")
    if skipped:
        print(f"Ignorados por no cumplir el patron ({len(skipped)}): {', '.join(skipped[:20])}")
