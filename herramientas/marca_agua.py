"""Añade la marca de agua de la Residencia de Estudiantes a los PDFs de una carpeta.

Uso: python -I marca_agua.py <carpeta_pdfs> <carpeta_destino> [logo.png]
(por defecto, assets/Residencia-Logo-Principal-RGB-Teja.png)

Patrón copiado de los ejemplos de dataset/ (*_MDA.pdf):
- Cuadrícula de 3x3 logos girados según la diagonal de la página (atan(alto/ancho)).
- Opacidad 23 % (alfa 59/255) sobre el logo Teja.
- Cada celda mide 1,235 veces la caja del logo girado; el centro del logo está al 40 %
  del ancho y del alto de la celda (desde arriba a la izquierda).
- La cuadrícula se encaja en la página manteniendo la proporción y se coloca en (10, 30) pt.
Cada PDF se guarda como <nombre>_MDA.pdf. Los originales no se modifican.
"""
import math
import sys
import zlib
from pathlib import Path

import pikepdf
from PIL import Image

LOGO = Path(__file__).resolve().parent.parent / "assets" / "Residencia-Logo-Principal-RGB-Teja.png"
OPACITY = 59 / 255
CELL_FACTOR = 1.235
CENTER = 0.4
OFFSET = (10, 30)
PX_PER_PT = 2  # resolución de la marca de agua


def cargar_logo(path=LOGO):
    logo = Image.open(path).convert("RGBA")
    logo.putalpha(logo.getchannel("A").point(lambda v: round(v * OPACITY)))
    return logo


def watermark(logo, pw, ph):
    """Devuelve (imagen RGBA, ancho_pt, alto_pt) para una página de pw x ph puntos."""
    aspect = logo.height / logo.width
    theta = math.atan2(ph, pw)
    c, s = math.cos(theta), math.sin(theta)
    # celda en unidades de ancho de logo
    cw, ch = CELL_FACTOR * (c + aspect * s), CELL_FACTOR * (s + aspect * c)
    fit = min(pw / (3 * cw), ph / (3 * ch))  # puntos por unidad de logo
    w_pt, h_pt = 3 * cw * fit, 3 * ch * fit
    k = fit * PX_PER_PT
    canvas = Image.new("RGBA", (round(w_pt * PX_PER_PT), round(h_pt * PX_PER_PT)), (0, 0, 0, 0))
    lw = round(k)
    rot = logo.resize((lw, round(lw * aspect)), Image.LANCZOS).rotate(
        math.degrees(theta), resample=Image.BICUBIC, expand=True)
    for i in range(3):
        for j in range(3):
            cx = (i + CENTER) * cw * k
            cy = (j + CENTER) * ch * k
            canvas.alpha_composite(rot, (round(cx - rot.width / 2), round(cy - rot.height / 2)))
    return canvas, w_pt, h_pt


def add_watermark(pdf, page, logo, cache):
    mb = [float(v) for v in page.MediaBox]
    pw, ph = mb[2] - mb[0], mb[3] - mb[1]
    key = (round(pw, 1), round(ph, 1))
    if key not in cache:
        img, w_pt, h_pt = watermark(logo, pw, ph)
        smask = pikepdf.Stream(pdf, zlib.compress(img.getchannel("A").tobytes()), Type=pikepdf.Name.XObject,
                               Subtype=pikepdf.Name.Image, Width=img.width, Height=img.height,
                               ColorSpace=pikepdf.Name.DeviceGray, BitsPerComponent=8,
                               Filter=pikepdf.Name.FlateDecode)
        xobj = pikepdf.Stream(pdf, zlib.compress(img.convert("RGB").tobytes()), Type=pikepdf.Name.XObject,
                              Subtype=pikepdf.Name.Image, Width=img.width, Height=img.height,
                              ColorSpace=pikepdf.Name.DeviceRGB, BitsPerComponent=8,
                              Filter=pikepdf.Name.FlateDecode, SMask=smask)
        cache[key] = (xobj, w_pt, h_pt)
    xobj, w_pt, h_pt = cache[key]
    if "/XObject" not in page.Resources:
        page.Resources.XObject = pikepdf.Dictionary()
    page.Resources.XObject.MDA = xobj
    x, y = mb[0] + OFFSET[0], mb[1] + OFFSET[1]
    page.contents_coalesce()
    page.contents_add(pikepdf.Stream(pdf, f"\nq {w_pt:.2f} 0 0 {h_pt:.2f} {x:.2f} {y:.2f} cm /MDA Do Q\n".encode()))


def marcar_pdfs(src, dst, logo_path=LOGO):
    """Guarda en dst una copia _MDA de cada PDF de src. Devuelve el nº de PDFs."""
    dst = Path(dst)
    dst.mkdir(exist_ok=True)
    logo = cargar_logo(logo_path)
    count = 0
    for f in sorted(Path(src).glob("*.pdf")):
        with pikepdf.open(f) as pdf:
            cache = {}
            for page in pdf.pages:
                add_watermark(pdf, page, logo, cache)
            pdf.save(dst / f"{f.stem}_MDA.pdf")
        count += 1
    return count


if __name__ == "__main__":
    logo_arg = sys.argv[3] if len(sys.argv) > 3 else LOGO
    print(f"PDFs con marca de agua: {marcar_pdfs(sys.argv[1], sys.argv[2], logo_arg)}")
