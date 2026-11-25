"""Añade una capa de texto invisible (OCR con Tesseract) a los PDFs de una carpeta.

Uso: python -I ocr_pdfs.py <carpeta_imagenes> <carpeta_pdfs> <informe.csv>

Tesseract lee cada JPG original y genera solo el texto (textonly_pdf), que se superpone a la
página con pikepdf: la imagen del escaneo no se toca. Cada PDF se reemplaza solo al terminar
bien todas sus páginas.

Las páginas con confianza media inferior a UMBRAL (en la práctica, manuscritos) quedan sin
texto, para no meter texto sin sentido en el PDF. El informe CSV da las palabras, la confianza
media y si el texto se ha incluido, página a página.
"""
import csv
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pikepdf
from PIL import Image, ImageFilter, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_pdfs import agrupar  # noqa: E402

TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = Path(__file__).resolve().parent / "tessdata"
IDIOMAS = "spa+fra+eng+ita+por"
UMBRAL = 70  # confianza media mínima para incluir el texto de una página
# Imágenes revisadas a mano cuyo texto se incluye aunque no lleguen al umbral
FORZAR = set((Path(__file__).resolve().parent / "ocr_forzar.txt").read_text(encoding="utf-8").split())


def preparar(jpg, tmp):
    """Crea una copia temporal para el OCR: gris con contraste, ampliada 2x y enfocada."""
    with Image.open(jpg) as im:
        dpi = im.info["dpi"]
        gris = ImageOps.autocontrast(im.convert("L"), cutoff=1)
    copia = gris.resize((gris.width * 2, gris.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(3, 150, 2))
    ruta = Path(tmp) / f"{Path(jpg).stem}_x2.png"
    copia.save(ruta, dpi=(dpi[0] * 2, dpi[1] * 2))
    return ruta


def ocr_imagen(jpg, tmp):
    """Devuelve (PDF de solo texto, palabras, confianza media, segundos) de una imagen."""
    inicio = time.perf_counter()
    base = Path(tmp) / f"{Path(jpg).stem}_ocr"
    # En las páginas de FORZAR, psm 3 se salta el cuerpo de la carta: se lee con psm 4 una copia preparada
    forzada = Path(jpg).name in FORZAR
    entrada, psm = (preparar(jpg, tmp), "4") if forzada else (jpg, "3")
    cmd = [str(TESSERACT), str(entrada), str(base), "--tessdata-dir", str(TESSDATA), "-l", IDIOMAS,
           "--psm", psm, "-c", "textonly_pdf=1", "-c", "tessedit_create_pdf=1",
           "-c", "tessedit_create_tsv=1"]
    r = subprocess.run(cmd, env=dict(os.environ, OMP_THREAD_LIMIT="1"), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"Tesseract fallo en {Path(jpg).name}: {r.stderr.decode(errors='replace')[-300:]}")
    confianzas = []
    with open(f"{base}.tsv", encoding="utf-8", newline="") as h:
        for fila in csv.DictReader(h, delimiter="\t", quoting=csv.QUOTE_NONE):
            if fila["level"] == "5" and fila["text"].strip() and float(fila["conf"]) >= 0:
                confianzas.append(float(fila["conf"]))
    media = sum(confianzas) / len(confianzas) if confianzas else 0.0
    return Path(f"{base}.pdf"), len(confianzas), media, time.perf_counter() - inicio


def ocr_documento(pdf_path, imagenes):
    """Añade el texto a un PDF, con una imagen por página. Devuelve las filas del informe."""
    pdf_path = Path(pdf_path)
    filas = []
    with tempfile.TemporaryDirectory(prefix="ocr_") as tmp:
        salida = pdf_path.with_name(pdf_path.name + ".tmp")
        with pikepdf.open(pdf_path) as pdf:
            if len(pdf.pages) != len(imagenes):
                raise RuntimeError(f"{len(pdf.pages)} paginas para {len(imagenes)} imagenes")
            for page, jpg in zip(pdf.pages, imagenes):
                texto, palabras, media, seg = ocr_imagen(jpg, tmp)
                incluido = palabras > 0 and (media >= UMBRAL or Path(jpg).name in FORZAR)
                if incluido:
                    with pikepdf.open(texto) as capa:
                        page.add_overlay(capa.pages[0])
                filas.append((pdf_path.stem, Path(jpg).name, palabras, round(media, 1),
                              "si" if incluido else "no", round(seg, 1)))
            pdf.save(salida)
        os.replace(salida, pdf_path)
    return filas


def ocr_pdfs(src, pdf_dir, informe, workers=None):
    """Añade OCR a todos los documentos de src. Devuelve la lista de errores."""
    docs, _ = agrupar(src)
    errores, filas = [], []
    with ThreadPoolExecutor(workers or os.cpu_count()) as pool:
        tareas = {pool.submit(ocr_documento, Path(pdf_dir) / f"{doc}.pdf", [f for _, f in items]): doc
                  for doc, items in docs.items()}
        for hechos, tarea in enumerate(as_completed(tareas), 1):
            try:
                filas.extend(tarea.result())
            except Exception as e:  # se informa al final y el proceso termina con error
                errores.append(f"{tareas[tarea]}: {e}")
            if hechos % 25 == 0 or hechos == len(docs):
                print(f"  OCR: {hechos}/{len(docs)} documentos", flush=True)
    with open(informe, "w", encoding="utf-8-sig", newline="") as h:
        out = csv.writer(h, delimiter=";")
        out.writerow(["documento", "imagen", "palabras", "confianza_media", "texto_incluido", "segundos"])
        out.writerows(sorted(filas, key=lambda f: f[1]))
    return errores


if __name__ == "__main__":
    fallos = ocr_pdfs(sys.argv[1], sys.argv[2], sys.argv[3])
    for fallo in fallos:
        print(f"ERROR {fallo}")
    sys.exit(1 if fallos else 0)
