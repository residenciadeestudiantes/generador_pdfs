"""Separa un PDF matriz (expediente AEM) en un PDF por carta, sin recomprimir.

Uso:
    python -I herramientas\\separar_cartas.py <pdf_matriz> <carpeta_salida> <rangos> [--excluir 1-2]

<rangos> es una lista de documentos separados por comas; cada documento es una
página ("5") o un rango ("14-16"). Las páginas se numeran desde 1, como en el visor.
Cada documento se guarda como <nombre_matriz>_NNN.pdf, en orden ascendente.

Las páginas se copian tal cual con pikepdf (imagen y capa de texto OCR intactas).
Comprueba que cada página del expediente queda en un documento o en --excluir,
y que ninguna se repite ni se salta.
"""
import argparse, csv, hashlib, sys
from pathlib import Path
import pikepdf


def parse(spec):
    docs = []
    for parte in spec.split(','):
        parte = parte.strip()
        if not parte:
            continue
        a, _, b = parte.partition('-')
        a = int(a); b = int(b) if b else a
        assert a <= b, parte
        docs.append(list(range(a, b + 1)))
    return docs


def huella(pg):
    """Huella del contenido de una página: flujo de contenido y recursos."""
    h = hashlib.sha256()
    h.update(pg.obj.Contents.read_bytes() if not isinstance(pg.obj.Contents, pikepdf.Array)
             else b''.join(c.read_bytes() for c in pg.obj.Contents))
    for nombre, im in pg.images.items():
        h.update(im.read_raw_bytes())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('matriz'); ap.add_argument('salida'); ap.add_argument('rangos')
    ap.add_argument('--excluir', default='')
    a = ap.parse_args()
    src = pikepdf.open(a.matriz)
    n = len(src.pages)
    docs = parse(a.rangos)
    excl = [p for d in parse(a.excluir) for p in d] if a.excluir else []
    usadas = [p for d in docs for p in d] + excl
    faltan = sorted(set(range(1, n + 1)) - set(usadas))
    repes = sorted({p for p in usadas if usadas.count(p) > 1})
    fuera = sorted(p for p in usadas if p < 1 or p > n)
    planas = [p for d in docs for p in d]
    if faltan or repes or fuera or planas != sorted(planas):
        sys.exit(f'Rangos incorrectos: faltan {faltan}, repetidas {repes}, fuera {fuera}, '
                 f'orden {"OK" if planas == sorted(planas) else "MAL"}')
    out = Path(a.salida); out.mkdir(parents=True, exist_ok=True)
    base = Path(a.matriz).stem
    ancho = max(3, len(str(len(docs))))
    filas = []
    for k, paginas in enumerate(docs, 1):
        nuevo = pikepdf.new()
        for p in paginas:
            nuevo.pages.append(src.pages[p - 1])
        destino = out / f'{base}_{k:0{ancho}d}.pdf'
        nuevo.save(destino)
        # verificación: cada página idéntica a la del expediente
        chk = pikepdf.open(destino)
        assert len(chk.pages) == len(paginas)
        for pg, p in zip(chk.pages, paginas):
            assert huella(pg) == huella(src.pages[p - 1]), (destino.name, p)
        chk.close()
        filas.append([destino.name, paginas[0], paginas[-1], len(paginas)])
    with open(out / f'{base}_indice.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['pdf', 'pagina_inicial', 'pagina_final', 'paginas'])
        w.writerows(filas)
    print(f'{len(docs)} PDFs en {out} ({sum(len(d) for d in docs)} paginas; excluidas {excl or "ninguna"}). '
          f'Verificacion OK: cada pagina identica a la del expediente.')


if __name__ == '__main__':
    main()
