"""Proceso de un fondo: revisión, PDFs y verificación; OCR y marca de agua, solo si se piden.

Uso (desde la carpeta del proyecto):
    python -I herramientas\\procesar_fondo.py <FONDO> [--revisar | --verificar] [--salida CARPETA] [--ocr] [--mda]

    <FONDO>      carpeta de imágenes (p. ej. EDC\\EDC_02).
    --salida     dónde crear <nombre>_PDF y <nombre>_PDF_MDA (por defecto, junto a <FONDO>).
    --ocr        añade texto buscable con Tesseract (desactivado por defecto).
    --mda        crea además <nombre>_PDF_MDA con la marca de agua (desactivado por defecto).
    --revisar    solo muestra el informe previo, sin generar nada.
    --verificar  solo verifica lo ya generado, sin generar nada.

Si hay archivos fuera de patrón, no se genera nada: se perdería una página sin avisar.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pikepdf  # noqa: E402
import pypdfium2  # noqa: E402

from make_pdfs import agrupar, generar_pdfs, pruebas_color  # noqa: E402
from marca_agua import marcar_pdfs  # noqa: E402
from ocr_pdfs import ocr_pdfs  # noqa: E402


def informe(src):
    """Muestra carpetas, imágenes, documentos, huecos y archivos fuera de patrón."""
    docs, skipped = agrupar(src)
    images = sum(len(v) for v in docs.values())
    color = pruebas_color(src)
    carpetas = sorted({d.rsplit("_", 1)[0] for d in docs})
    print(f"Carpetas: {len(carpetas)}  imagenes de documentos: {images}  documentos: {len(docs)}  "
          f"pruebas de color: {len(color)}")
    for f in color:
        print(f"  Prueba de color (excluida): {f.name}")
    for f in Path(src).rglob("*.txt"):
        print(f"  Nota, hay que leerla: {f.name}")
    for carpeta in carpetas:
        nums = sorted(int(d.rsplit("_", 1)[1]) for d in docs if d.rsplit("_", 1)[0] == carpeta)
        huecos = sorted(set(range(1, nums[-1] + 1)) - set(nums))
        if huecos:
            print(f"  {carpeta}: faltan documentos {', '.join(f'{h:03d}' for h in huecos)}")
    for doc, items in docs.items():
        paginas = [p for p, _ in items]
        if paginas != list(range(1, len(paginas) + 1)):
            print(f"  {doc}: paginas {', '.join(f'{p:03d}' for p in paginas)}")
    if skipped:
        print(f"  Fuera de patron ({len(skipped)}): {', '.join(skipped[:20])}")
    return skipped


def escaneo(page):
    """Devuelve los bytes de la imagen JPEG del escaneo de una página (error si no hay solo una)."""
    jpegs = [v for k, v in page.Resources.get("/XObject", {}).items()
             if k != "/MDA" and v.get("/Subtype") == "/Image" and v.get("/Filter") == "/DCTDecode"]
    if len(jpegs) != 1:
        raise ValueError(f"{len(jpegs)} imagenes JPEG en la pagina")
    return bytes(jpegs[0].read_raw_bytes())


def verificar_carpeta(carpeta, docs, sufijo, color, textos, parcial=False):
    """Devuelve (nº PDFs, nº páginas, errores) comparando carpeta con lo que debe contener.

    Con parcial=True no se exige que estén todos los PDFs (pruebas con unos pocos).
    """
    errores, pdfs, paginas = [], 0, 0
    esperados = {f"{doc}{sufijo}.pdf": doc for doc in docs}
    presentes = {f.name for f in Path(carpeta).iterdir()} if Path(carpeta).is_dir() else set()
    if not parcial:
        errores += [f"falta {n}" for n in sorted(set(esperados) - presentes)]
    errores += [f"sobra {n}" for n in sorted(presentes - set(esperados))]
    for nombre in sorted(set(esperados) & presentes):
        items = docs[esperados[nombre]]
        ruta = Path(carpeta) / nombre
        try:
            with pikepdf.open(ruta) as pdf:
                pdfs += 1
                paginas += len(pdf.pages)
                if len(pdf.pages) != len(items):
                    errores.append(f"{nombre}: {len(pdf.pages)} paginas, esperadas {len(items)}")
                for n, (page, (_, jpg)) in enumerate(zip(pdf.pages, items), 1):
                    datos = escaneo(page)
                    if datos != jpg.read_bytes():
                        errores.append(f"{nombre} p.{n}: la imagen no es identica a {jpg.name}")
                    if datos in color:
                        errores.append(f"{nombre} p.{n}: contiene la prueba de color")
                    if ("/MDA" in page.Resources.get("/XObject", {})) != bool(sufijo):
                        errores.append(f"{nombre} p.{n}: marca de agua {'ausente' if sufijo else 'indebida'}")
            if textos is not None:
                doc = pypdfium2.PdfDocument(ruta)
                try:
                    for n, (_, jpg) in enumerate(items):
                        hay = doc[n].get_textpage().count_chars() > 0
                        if hay != textos.get(jpg.name, False):
                            errores.append(f"{nombre} p.{n + 1}: texto {'indebido' if hay else 'ausente'}")
                finally:
                    doc.close()
        except Exception as e:
            errores.append(f"{nombre}: {e}")
    return pdfs, paginas, errores


def leer_informe_ocr(ruta):
    """Devuelve ({imagen: si lleva texto}, [imágenes sin texto]) a partir del informe CSV."""
    with open(ruta, encoding="utf-8-sig", newline="") as h:
        filas = list(csv.DictReader(h, delimiter=";"))
    return {f["imagen"]: f["texto_incluido"] == "si" for f in filas}, \
        [f["imagen"] for f in filas if f["texto_incluido"] != "si"]


def verificar(src, pdf_dir, mda_dir=None, informe_ocr=None):
    """Verifica nombres, contenido, orden, marca y OCR. Devuelve True si todo es correcto.

    Sin mda_dir solo se comprueba pdf_dir. Sin informe_ocr, ninguna página debe llevar texto.
    """
    docs, _ = agrupar(src)
    n_paginas = sum(len(v) for v in docs.values())
    color = {f.read_bytes() for f in pruebas_color(src)}
    textos, sin_texto = {}, []
    if informe_ocr:
        textos, sin_texto = leer_informe_ocr(informe_ocr)
    ok = True
    for carpeta, sufijo in [(pdf_dir, "")] + ([(mda_dir, "_MDA")] if mda_dir else []):
        pdfs, paginas, errores = verificar_carpeta(carpeta, docs, sufijo, color, textos)
        bien = not errores and pdfs == len(docs) and paginas == n_paginas
        ok &= bien
        print(f"  {Path(carpeta).name}: {pdfs} PDFs (esperados {len(docs)}), {paginas} paginas "
              f"(esperadas {n_paginas}) -> {'OK' if bien else 'ERROR'}")
        for e in errores[:50]:
            print(f"    {e}")
        if len(errores) > 50:
            print(f"    ... y {len(errores) - 50} errores mas")
    if informe_ocr:
        print(f"  OCR: {n_paginas - len(sin_texto)} paginas con texto, {len(sin_texto)} sin texto "
              f"(baja confianza; ver {Path(informe_ocr).name})")
    return ok


def informe_texto_acrobat(carpeta, docs, ruta_csv):
    """Cuenta el texto de cada página de los PDFs de carpeta y lo escribe en ruta_csv.

    Devuelve (páginas con texto, páginas sin texto). Que una página no tenga texto no es
    un error: el manuscrito no se reconoce.
    """
    con, sin = 0, 0
    with open(ruta_csv, "w", encoding="utf-8-sig", newline="") as h:
        w = csv.writer(h, delimiter=";")
        w.writerow(["imagen", "pdf", "pagina", "caracteres", "muestra"])
        for doc, items in docs.items():
            ruta = Path(carpeta) / f"{doc}.pdf"
            if not ruta.exists():
                continue
            pdf = pypdfium2.PdfDocument(ruta)
            try:
                for n, (_, jpg) in enumerate(items):
                    tp = pdf[n].get_textpage()
                    texto = tp.get_text_range().strip() if tp.count_chars() else ""
                    letras = sum(c.isalnum() for c in texto)
                    con, sin = (con + 1, sin) if letras else (con, sin + 1)
                    muestra = " ".join(texto.split())[:80]
                    w.writerow([jpg.name, ruta.name, n + 1, letras, muestra])
            finally:
                pdf.close()
    return con, sin


def verificar_acrobat(src, pdf_dir, ocr_dir, ruta_csv, parcial=False):
    """Verifica la salida del OCR de Acrobat y que los PDFs de partida siguen intactos."""
    docs, _ = agrupar(src)
    color = {f.read_bytes() for f in pruebas_color(src)}
    ok = True
    for carpeta, es_parcial in [(pdf_dir, False), (ocr_dir, parcial)]:
        pdfs, paginas, errores = verificar_carpeta(carpeta, docs, "", color, None, es_parcial)
        n_docs = len(docs) if not es_parcial else pdfs
        n_pag = sum(len(v) for v in docs.values()) if not es_parcial else paginas
        bien = not errores and pdfs == n_docs and paginas == n_pag and pdfs > 0
        ok &= bien
        print(f"  {Path(carpeta).name}: {pdfs} PDFs (esperados {n_docs}), {paginas} paginas "
              f"(esperadas {n_pag}) -> {'OK' if bien else 'ERROR'}")
        for e in errores[:50]:
            print(f"    {e}")
        if len(errores) > 50:
            print(f"    ... y {len(errores) - 50} errores mas")
    con, sin = informe_texto_acrobat(ocr_dir, docs, ruta_csv)
    print(f"  OCR Acrobat: {con} paginas con texto, {sin} sin texto (ver {Path(ruta_csv).name})")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fondo", type=Path)
    ap.add_argument("--salida", type=Path)
    ap.add_argument("--ocr", action="store_true")
    ap.add_argument("--mda", action="store_true")
    ap.add_argument("--revisar", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--acrobat", nargs="?", const=True, default=None, metavar="CARPETA")
    ap.add_argument("--parcial", action="store_true")
    args = ap.parse_args()

    if args.acrobat:
        src = args.fondo
        salida = args.salida or src.parent
        pdf_dir = salida / f"{src.name}_PDF"
        ocr_dir = salida / f"{src.name}_PDF_OCR" if args.acrobat is True else Path(args.acrobat)
        ruta_csv = ocr_dir.parent / f"{ocr_dir.name}_texto.csv"
        print(f"== Verificacion del OCR de Acrobat en {ocr_dir}")
        ok = verificar_acrobat(src, pdf_dir, ocr_dir, ruta_csv, args.parcial)
        print("RESULTADO: " + ("OK" if ok else "ERROR"))
        sys.exit(0 if ok else 1)

    src = args.fondo
    salida = args.salida or src.parent
    pdf_dir = salida / f"{src.name}_PDF"
    mda_dir = salida / f"{src.name}_PDF_MDA" if args.mda else None
    informe_ocr = salida / f"{src.name}_OCR_informe.csv" if args.ocr else None

    print("== Revision previa")
    skipped = informe(src)
    if args.revisar:
        return
    if not args.verificar:
        if skipped:
            print("ERROR: hay archivos fuera de patron. Corrigelos antes de generar.")
            sys.exit(1)
        print(f"== Generando {pdf_dir.name}")
        generar_pdfs(src, pdf_dir)
        if args.ocr:
            print("== OCR")
            fallos = ocr_pdfs(src, pdf_dir, informe_ocr)
            if fallos:
                print("ERROR: el OCR ha fallado en:")
                for fallo in fallos:
                    print(f"  {fallo}")
                sys.exit(1)
        if args.mda:
            print(f"== Marca de agua en {mda_dir.name}")
            marcar_pdfs(pdf_dir, mda_dir)

    print("== Verificacion")
    ok = verificar(src, pdf_dir, mda_dir, informe_ocr)
    print("RESULTADO: " + ("OK" if ok else "ERROR"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
