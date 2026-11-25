# Digitalización de archivo: de JPG a PDF con marca de agua

Proyecto de archivo documental de la Residencia de Estudiantes: carpetas de imágenes JPG digitalizadas que se convierten en un PDF por documento y después se marcan con la marca de agua oficial.

Fondos actuales:
- `EDC`: Enrique Díez-Canedo.
- `JMR`: José Antonio Muñoz Rojas.
- `GD`: Gustavo Durán.

Todos tienen la misma estructura. El usuario va dejando cajas nuevas y pide revisarlas y generar sus PDFs.

## Estructura del proyecto

```
GENERADOR DE PDFS\
├── EDC\                        fondo EDC: cajas originales (EDC_19\EDC_19_001\…) y sus salidas (EDC_19_PDF\)
├── JMR\                        fondo JMR: cajas (JMR_047\JMR_47_001\…) y salidas (JMR_047_PDF\)
├── GUSTAVO DURÁN - EXTENSIÓN\  fondo GD: cajas (GD_1\GD_1_001\…) y salidas (GD_1_PDF\)
├── EDC_PDF_MDA\                serie EDC_01 con marca de agua (sufijo _MDA), de la etapa anterior
├── EDC_02_OCR_informe.csv      informe del OCR de Tesseract de EDC_02 (etapa anterior)
├── *_renombrado.csv            tablas de los renombrados de originales (nombre antiguo, nuevo, SHA-256)
├── dataset\                    PDFs de ejemplo con la marca de agua oficial (referencia del patrón)
├── assets\                     logos oficiales de la Residencia (Teja y Teja-Alt)
├── prueba_acrobat\             prueba de OCR con Acrobat (ver «OCR»)
└── herramientas\               scripts del proceso y modelos de OCR (tessdata\)
```

- **Dónde van las salidas:** cada salida va junto a sus cajas, dentro de la carpeta del fondo. Se indica con `--salida EDC`, `--salida JMR` o `--salida "GUSTAVO DURÁN - EXTENSIÓN"`.
- **Las imágenes no se quedan en el proyecto:** cuando una caja ya está generada, el usuario suele retirar la carpeta de imágenes y solo queda la carpeta `_PDF`.
- **Lo que queda (2026-11-19):**
  - **Imágenes originales:** solo `EDC\EDC_11_nueva`, `JMR\JMR_051`, `JMR\JMR_052` (ya con las carpetas 009 y 010), `JMR\JMR_50_EXTENSION` (documento 029 de la caja 50), `EDC\EDC_20`, `EDC\EDC_21`, `EDC\EDC_22`, `EDC\EDC_23`, `EDC\EDC_24`, `EDC\EDC_25`, `ERNESTO DURÁN\ED_1` y `JMR\JMR_048_apartadas`. `JMR\JMR_52_PARA_UNIR` quedó vacía.
  - **Salidas:** `EDC_03_PDF` … `EDC_19_PDF` (y `EDC_11_PDF`) y `JMR_039_PDF` … `JMR_052_PDF`.
- **Lo que ya no está:**
  - las imágenes y salidas de EDC_01 y EDC_02 (`EDC_PDF`, `EDC_02_PDF`, `EDC_02_PDF_MDA`);
  - las imágenes de las demás cajas ya generadas;
  - la caja `GD_1` y su `GD_1_PDF`.
- **Carpetas vacías:** `GUSTAVO DURÁN - EXTENSIÓN` y `CAJA 1` existen, pero están vacías. `ERNESTO DURÁN` tiene `ED_1` y `ED_1_PDF` desde el 2026-11-20.
- **Si hay que volver a revisar una caja ya generada:** sus imágenes ya no estarán aquí, así que se trabaja sobre sus PDFs con pikepdf (por ejemplo, para contar páginas).

## Nomenclatura de las imágenes

`FONDO_SS_CCC_DDD_PPP.jpg` — ejemplo: `EDC_01_001_004_002.jpg`

| Parte | Significado |
|---|---|
| `EDC` | Fondo (siglas del autor o colección) |
| `01` | Serie o caja |
| `001` | Carpeta o expediente |
| `004` | Número de documento dentro de la carpeta |
| `002` | Imagen o página dentro del documento |

- Un documento empieza en `_DDD_001` y acaba en la última imagen con el mismo `DDD`.
- Un mismo número de documento puede agrupar varias piezas físicas (p. ej. tarjetas anotadas a lápiz "4A" y "4B"). Se tratan como un solo documento.
- **La prueba de color (carta ColorChecker) nunca se incluye en los PDFs.** Se reconoce por el documento o la página `000`: `_000_000.jpg` en EDC; en JMR, `JMR_40_001_001_000.jpg`, donde la carta se fotografió junto a la primera hoja, que tiene además su propia imagen `_001`.
- La serie puede tener dos cifras en el nombre aunque la carpeta tenga tres: `JMR\JMR_040\JMR_40_001\`. También puede tener una sola cifra: `GD_1_001_001_001.jpg` (fondo Gustavo Durán). El patrón de `make_pdfs.py` acepta 1 o 2 cifras desde el 2026-11-18.
- Un `.txt` en la carpeta es una nota del digitalizador (p. ej. `INCIDENCIA.txt`): no bloquea el proceso, pero hay que leerla y contársela al usuario.
- Puede haber huecos en la numeración de documentos o de páginas (p. ej. páginas 001, 002, 006). Se respetan tal cual: no se rellenan ni se renumeran, pero hay que informar de ellos al usuario.
- Un hueco puede ser una errata de nombre, no una falta. Antes de generar, mirar las imágenes de alrededor y compararlas con la anotación a lápiz («3a», «5b»: documento y hoja). Renombrar un original solo si lo decide el usuario, y comprobar el SHA-256.

## Proceso normal (lo actual con un fondo nuevo)

**Por decisión del usuario, de momento solo se generan PDFs normales, sin OCR y sin marca de agua.** El código de ambos se conserva para usarlo más adelante: no borrarlo ni activarlo sin que el usuario lo pida.

```powershell
# 1. Solo revisión: carpetas, imágenes, documentos, huecos, archivos fuera de patrón
python -I herramientas\procesar_fondo.py EDC\EDC_19 --revisar

# 2. Genera EDC\EDC_19_PDF (junto a la caja) y verifica el resultado
python -I herramientas\procesar_fondo.py EDC\EDC_19 --salida EDC
python -I herramientas\procesar_fondo.py JMR\JMR_052 --salida JMR
python -I herramientas\procesar_fondo.py "GUSTAVO DURÁN - EXTENSIÓN\GD_1" --salida "GUSTAVO DURÁN - EXTENSIÓN"

# Solo volver a verificar lo ya generado
python -I herramientas\procesar_fondo.py EDC\EDC_19 --salida EDC --verificar

# Para más adelante: añadir marca de agua (--mda) y OCR de Tesseract (--ocr)
python -I herramientas\procesar_fondo.py EDC\EDC_19 --salida EDC --mda --ocr
```

Primero ejecutar la revisión y contarle al usuario lo que salga (sobre todo huecos y archivos fuera de patrón) antes de generar. Si hay archivos fuera de patrón, no se genera nada: una errata en el nombre haría perder una página sin avisar.

### Flujo con cada caja nueva

1. **Localizar la caja.** El usuario puede equivocarse de fondo: dijo «49 y 50 de EDC» y eran `JMR_49` y `JMR_50`. Hay que buscar en todos.
2. **Revisión y comprobaciones previas:**
   - ejecutar `--revisar`;
   - contar los patrones de nombre por carpeta;
   - buscar imágenes cuyo prefijo `FONDO_SS_CCC` no coincide con su carpeta;
   - leer todos los `.txt`.
3. **Mirar las imágenes de cada caso.** Usar hojas de contacto con la esquina superior izquierda ampliada, donde está la anotación a lápiz:
   - todos los `_000`, para confirmar que son la carta ColorChecker;
   - los vecinos de cada hueco;
   - cada archivo fuera de patrón.
4. **Preguntar al usuario** cada renombrado con AskUserQuestion. Proponer la opción recomendada y, en los nombres de carpeta, el formato de 3 cifras de JMR (`JMR_47` → `JMR_047`).
5. **Renombrar con un script de Python:**
   - comprobar que no hay colisiones;
   - si una cadena de renombrados se pisa, hacerlo en dos fases con nombres `__tmp__`;
   - calcular el SHA-256 antes y después;
   - escribir la tabla en `<serie>_renombrado.csv`, en la raíz;
   - no hacer `cd` dentro de las carpetas de la caja, porque las bloquea y luego no se pueden renombrar.
6. **Generar con `--salida <fondo>`,** comprobar que la verificación da OK y añadir la «Referencia de la serie» aquí.

### Erratas habituales de los digitalizadores (vistas hasta ahora)

- **Página o prueba de color con 4 cifras:** `_0001`, `_0000`.
- **Prefijo equivocado:**
  - una carpeta entera con el número de otra carpeta (JMR_47_002, JMR_48_004);
  - la caja equivocada (`JMR_45_` dentro de la 47);
  - una imagen suelta con el prefijo de otra carpeta (JMR_51_004).
- **Número de la cámara en vez de nombre** (`0444.jpg`, `EDC_14_003_3243.jpg`, `190_1.jpg`). Hay que situarlos por la anotación a lápiz y por el contenido.
- **Una anotación a lápiz ya usada por otro documento** («4A» repetido). La solución habitual es un documento nuevo al final de la carpeta, aunque en JMR_50_008 el usuario prefirió meterlo dentro del documento relacionado.
- **Sufijos en el nombre:**
  - `_DUPLICADO` resultó ser otra pieza distinta;
  - `_PARTE1/_PARTE2` (o `PARTE 1`) son las mitades de un recorte grande: van como páginas 001 y 002, sin unirlas, para no recomprimir.
- **Documento de una sola hoja numerado como página `_002`** (EDC_21, EDC_23): la anotación a lápiz lleva solo el número, sin letra. Se renombra a `_001`.
- **Documento y página intercambiados en el nombre** (JMR_52_003 `020_010`…) y **numeración que no empieza en 001** (JMR_49_003 `125`…).
- **Una imagen repetida, con los píxeles idénticos** (JMR_48_011_004_002): se aparta sin borrarla a `<fondo>\<serie>_apartadas\`, fuera de la caja, porque `--revisar` trataría una subcarpeta como una carpeta más.
- **Una versión «nueva» de una caja ya generada** (`EDC_11_nueva`): se compara con los PDFs ya hechos, página a página, antes de rehacer nada.

La verificación final termina con código 1 si algo falla. Comprueba:
- **Nombres:** están exactamente los PDFs esperados, sin faltantes ni sobrantes.
- **Calidad, contenido y orden:** en cada página, el escaneo es idéntico byte a byte a su JPG.
- **Prueba de color:** no hay ningún PDF `_000` y ninguna página la contiene.
- **Marca:** ninguna página de `_PDF` la lleva y, con `--mda`, todas las de `_PDF_MDA` llevan `/MDA`.
- **OCR:** sin `--ocr`, ninguna página lleva texto; con `--ocr`, cada página lleva o no texto según el informe CSV.

No mide si el texto reconocido es correcto: eso solo se comprueba leyéndolo.

## Herramientas (`herramientas\`)

| Script | Qué hace |
|---|---|
| `procesar_fondo.py` | Orquesta todo: revisión → PDFs → OCR (solo con `--ocr`) → marca de agua (solo con `--mda`) → verificación |
| `ocr_pdfs.py` | Aparcado. Añade texto invisible con Tesseract sin tocar el escaneo y escribe el informe CSV |
| `make_pdfs.py` | JPG → un PDF por documento (`FONDO_SS_CCC_DDD.pdf`), todos en una carpeta sin subcarpetas. Usa **img2pdf**: incrusta los JPG sin recomprimir. No usar Pillow para guardar PDFs |
| `marca_agua.py` | Aparcado. Copia cada PDF con la marca de agua como `<nombre>_MDA.pdf`. Logo por defecto: `assets\Residencia-Logo-Principal-RGB-Teja.png` |

Cada script también se puede usar por separado:

```powershell
python -I herramientas\make_pdfs.py "EDC\EDC_02" "EDC_02_PDF"
python -I herramientas\marca_agua.py "EDC_02_PDF" "EDC_02_PDF_MDA"
```

Ejecutar siempre con `python -I` desde la carpeta del proyecto. Los scripts nunca modifican las imágenes ni los PDFs de origen.

## Marca de agua: el patrón

Copiado de los ejemplos de `dataset\` y validado contra ellos (diferencia media de opacidad de 1–2 sobre 255). El usuario dio el visto bueno al resultado.

- Logo **Teja** (rojo 218,60,0), **no** el Teja-Alt.
- Cuadrícula de **3×3** logos con un **23 % de opacidad** (alfa 59/255), superpuestos al escaneo.
- Cada logo está girado según la **diagonal de la página**, `atan(alto/ancho)`: unos 57° en las verticales y unos 37° en las horizontales.
- Cada celda mide 1,235 veces la caja del logo girado. El centro del logo queda al 40 % del ancho y del alto de la celda.
- La cuadrícula se encaja en la página manteniendo su proporción y se coloca en (10, 30) pt.
- Se guarda como imagen PNG con transparencia, a 2 px por punto, como recurso `/MDA` de cada página.
- Los PDFs de `dataset\` también llevan OCR (Adobe Acrobat) y sus imágenes están recomprimidas a unos 150 dpi; los nuestros conservan el JPG original.

## OCR (aparcado)

- El usuario pide para los PDFs: alta calidad (JPG sin recomprimir) y sin pruebas de color. Quiere OCR de calidad más adelante.
- **Pendiente: probar Adobe Acrobat.** El usuario considera poco efectivo Tesseract y tiene Acrobat instalado, con su módulo de OCR. La vía prevista es el Asistente de acciones, lanzado por el usuario, con «Imagen con capacidad de búsqueda (exacta)» sobre PDFs sin OCR, y la marca de agua después. Hay que comprobar byte a byte que el JPG no cambia.
- **Primera prueba (2026-11-06, `prueba_acrobat\`, 6 PDFs de EDC_01, Acrobat 26 Paper Capture): falló.** Las 10 imágenes se recomprimieron (calidad JPEG bastante más baja, ~55–60 % menos peso, bloques de 8×8 visibles en fondos oscuros) y una página (`EDC_01_011_014` p. 3) se enderezó, cambiando su tamaño y añadiendo márgenes blancos. Hay que revisar los ajustes de salida de Acrobat (sin enderezar, sin reducir ni recomprimir imágenes) y repetir la prueba.
- Motor usado hasta ahora: Tesseract 5.4 con modelos `tessdata_best` (spa, fra, eng, ita, por) en `herramientas\tessdata\`.
- Las páginas con confianza media inferior a 70 quedan sin texto, para no meter texto sin sentido: es la decisión del usuario.
- El umbral es imperfecto: la confianza baja también por sellos, membretes o papel oscuro, y descarta algo de mecanografiado. También deja pasar algo de ruido, como las orlas de `EDC_02_008_019_001`.
- El manuscrito no se reconoce.
- **Problema conocido sin resolver en el conjunto del fondo:** con `psm 3`, Tesseract puede tomar el cuerpo mecanografiado por texto vertical y saltárselo, a veces con confianza alta porque solo queda el membrete. Una confianza alta no garantiza que se haya leído la página.
- `herramientas\ocr_forzar.txt` lista las páginas revisadas a mano: su texto se incluye siempre y se leen con `psm 4` sobre una copia temporal en gris, con contraste, ampliada 2× y enfocada. El PDF conserva el JPG original.
- La verificación no detecta texto mal leído: al forzar una página, leer el resultado y compararlo con la imagen.

## Referencia de la serie EDC_01

16 carpetas, 1.108 imágenes (1 prueba de color), 705 documentos, 1.107 páginas.
- Huecos: falta el documento 006 en la carpeta 003; faltan el 013, el 023 y el 054 en la 008; el 033 y el 060 en la 009; y el 027 en la 012.
- El documento `EDC_01_003_005` tiene las páginas 001, 002 y 006.
- Tamaño: `EDC_PDF` ocupa unos 713 MB y `EDC_PDF_MDA` unos 847 MB.

## Referencia de la serie EDC_02

18 carpetas, 960 imágenes (1 prueba de color, en la carpeta 001), 510 documentos, 959 páginas, sin huecos.
- Errata corregida: `EDC_02_008_0441_001.jpg` se renombró a `EDC_02_008_041_001.jpg` (anotación a lápiz «41A»; contenido idéntico por SHA-256).
- `EDC_02_PDF`: versión actual, sin marca ni OCR, unos 541 MB. Se genera en segundos.
- `EDC_02_PDF_MDA` y `EDC_02_OCR_informe.csv` son de la versión anterior: 510 PDFs con marca y OCR de Tesseract, unos 643 MB. Ya no se corresponden con `EDC_02_PDF` y el usuario decidirá qué hacer con ellos.
- Ese OCR dio 354 páginas con texto y 605 sin él, de las que 143 no dieron ninguna palabra. Hay mucho manuscrito, pero también mecanografiado afectado por el problema de `psm 3`.

## Referencia de la serie EDC_03

33 carpetas, 590 imágenes (1 prueba de color), 289 documentos, 589 páginas, sin huecos. Salida en `EDC\EDC_03_PDF`.
- Errata corregida por decisión del usuario (contenido idéntico por SHA-256): `EDC_03_0_2 3331.jpg` → `EDC_03_024_001_001.jpg` (única imagen de la carpeta 024, a lápiz «1»).

## Referencia de la serie EDC_04

12 carpetas, 756 imágenes (1 prueba de color), 235 documentos, 755 páginas. Salida en `EDC\EDC_04_PDF`.
- Huecos: faltan los documentos 063 y 064 en la carpeta 002, y el 004 y el 005 en la 006. Las anotaciones de los vecinos («62A», «62B», «65»; «3A», «3B», «6A», «6B») coinciden con sus nombres. Los huecos se respetan; están pendientes de contrastar con los originales físicos.

## Referencia de la serie EDC_05

24 carpetas, 698 imágenes (1 prueba de color, en la carpeta 001), 234 documentos, 697 páginas. Salida en `EDC\EDC_05_PDF`, unos 550 MB.
- Hueco: falta el documento 027 en la carpeta 007. Las anotaciones de los vecinos («26A–C», «28A–C») coinciden con sus nombres. El 028 parece una copia al carbón del 026 (mismo artículo y misma foliación antigua 786–788). El hueco se respeta; está pendiente de contrastar con el original físico.

## Referencia de la serie EDC_06

9 carpetas, 633 imágenes (1 prueba de color: `EDC_06_001_000_000.jpg`), 105 documentos, 632 páginas, sin huecos ni notas. Salida en `EDC\EDC_06_PDF`, unos 501 MB.

## Referencia de la serie EDC_07

15 carpetas, 920 imágenes, **sin prueba de color**, 257 documentos, 920 páginas. Salida en `EDC\EDC_07_PDF`, unos 673 MB.
- Hueco: faltan los documentos 011, 012 y 013 en la carpeta 014. El 010 es un manuscrito continuo de 25 páginas (paginación del autor 1–25, fechado «20-V-34»), así que no los contiene. El hueco se respeta; está pendiente de contrastar con el original físico.

## Referencia de la serie EDC_08

12 carpetas, 1.121 imágenes (1 prueba de color: `EDC_08_001_000_000.jpg`), 74 documentos, 1.120 páginas, sin huecos. Salida en `EDC\EDC_08_PDF`, unos 600 MB.
- La carpeta 006 llegó con 133 imágenes numeradas con el contador de la cámara (`EDC_08_006_1912.jpg` … `_2045.jpg`, sin la 1989). Con la pista del usuario («11 documentos») se dividió en 11 por la anotación a lápiz del número de documento y la paginación propia de cada texto. Se renombraron por decisión del usuario (contenido idéntico por SHA-256); la tabla de equivalencias está en `EDC_08_006_renombrado.csv`.
- Los documentos: 001 (1912–1929) Machado, manuscrito; 002 (1930–1941) «Antonio Machado, poeta español», mecanoscrito; 003 (1942–1951) su copia al carbón; 004 (1952–1965) «Racine, estatua viva», manuscrito; 005 (1966–1973) y 006 (1974–1980) mecanoscritos de Racine; 007 (1981–1987) copia al carbón del 006, sin número a lápiz; 008 (1988 portadilla «Conferencia sobre González Martínez» + 1990–2001); 009 (2002–2016) ensayo sobre teatro, mecanoscrito; 010 (2017–2031) conferencia sobre Cabanyes y Piferrer, manuscrito; 011 (2032–2045) «Dos poetas castellanos de Cataluña», mecanoscrito (la última imagen es un reverso en blanco).
- La 1989 que falta cae entre la portadilla y la p. 1 del 008, y el texto es continuo: es un salto del contador, no una página perdida.

## Referencia de la serie EDC_09

7 carpetas, 1.132 imágenes (1 prueba de color: `EDC_09_001_001_000.jpg`), 20 documentos, 1.131 páginas, sin huecos ni notas. Salida en `EDC\EDC_09_PDF`, unos 638 MB. Hay documentos muy largos: `EDC_09_001_001` tiene 315 páginas y `EDC_09_007_001`, 342.

## Referencia de la serie EDC_10

5 carpetas, 989 imágenes (1 prueba de color: `EDC_10_001_001_000.jpg`), 5 documentos (uno por carpeta), 988 páginas, sin huecos. Salida en `EDC\EDC_10_PDF`, unos 703 MB.
- En las carpetas 002–005, la imagen `_000` no era una prueba de color, sino la primera página del documento (paginada «1»; la `_001` llevaba un «2»). Generarlas tal cual habría perdido 4 páginas sin aviso. Por decisión del usuario, se desplazó la numeración una posición en esas carpetas (`_000` → `_001`, `_001` → `_002`…; 708 imágenes, contenido idéntico por SHA-256). La tabla de equivalencias está en `EDC_10_EDC_11_renombrado.csv`.
- **Lección:** que la revisión marque un `_000` como prueba de color no basta. Hay que mirar cada `_000` y comprobar que es de verdad la carta ColorChecker.
- La carpeta 004 parece una copia al carbón de la 002 (las mismas páginas mecanografiadas).

## Referencia de la serie EDC_11

5 carpetas, 911 imágenes (1 prueba de color: `EDC_11_001_000_000.jpg`), 21 documentos, 910 páginas, sin huecos. Salida en `EDC\EDC_11_PDF`, unos 435 MB.
- Las imágenes llegaron sin prefijo (`001_001.jpg`). Por decisión del usuario se les añadió `EDC_11_CCC_` según su carpeta, sin cambiar la numeración (contenido idéntico por SHA-256; tabla en `EDC_10_EDC_11_renombrado.csv`).
- `EDC_11_005_005` es la obra «Ohara Go Ko (La visita imperial a Ohara)». Llegó como `005_001` (portada e inicio), `005_002` (última página, acaba en «fin») y 7 hojas sueltas con el contador de la cámara (`1409`–`1415`), que son el cuerpo de la obra. Por decisión del usuario quedó: portada (001), 1409–1415 (002–008) y «fin» (009). El orden se dedujo del texto, sin paginación en el original: está pendiente de contrastar con el original físico.
- **`EDC\EDC_11_nueva`** (llegó el 2026-11-13): las mismas 911 imágenes, byte a byte, ya con los nombres definitivos, salvo el orden de «Ohara Go Ko». Ahí el «fin» está como página 002 y las hojas 1409–1415 como 003–009. El texto confirma el orden ya generado (la 001 acaba en «…se para en el nanori-za», la 1409 empieza «Daijin: Soy caballero…»). Por decisión del usuario se mantiene `EDC_11_PDF` y no se genera nada desde `EDC_11_nueva`.

## Referencia de la serie EDC_12

11 carpetas, 779 imágenes (1 prueba de color: `EDC_12_001_000_000.jpg`, fotografiada junto a la hoja `001_001_001`, que tiene su propia imagen), 394 documentos, 778 páginas, sin huecos ni notas. Salida en `EDC\EDC_12_PDF`, unos 610 MB.

## Referencia de la serie EDC_13

7 carpetas, 625 imágenes (1 prueba de color: `EDC_13_001_000_000.jpg`, junto a la hoja `001_001_001`, que tiene su propia imagen), 123 documentos, 624 páginas, sin notas. Salida en `EDC\EDC_13_PDF`, unos 421 MB.
- Por decisión del usuario se renombraron dos imágenes (contenido idéntico por SHA-256; tabla en `EDC_13_renombrado.csv`): `EDC_13_002_004_001_PARTE 1.jpg` y `_PARTE 2.jpg` → `EDC_13_002_004_001.jpg` y `_002.jpg`. Son las mitades de arriba y de abajo de una página grande de periódico («Literatura y Arte», con «Doña Bellasmin»).
- Hueco: falta el documento 002 en la carpeta 007. Los vecinos están anotados «1C» (fin de una lista mecanografiada de artículos de «El Sol») y «3A». El hueco se respeta; está pendiente de contrastar con el original físico.

## Referencia de la serie EDC_14

6 carpetas, 750 imágenes (1 prueba de color: `EDC_14_001_000_000.jpg`), 305 documentos, 749 páginas, sin huecos ni notas. Salida en `EDC\EDC_14_PDF`, unos 410 MB.
- Por decisión del usuario (contenido idéntico por SHA-256; tabla en `EDC_14_renombrado.csv`), `EDC_14_003_3243.jpg` → `EDC_14_003_003_010.jpg`. Tenía el número de la cámara y es una hoja de papel cebolla en blanco, sin anotación, fotografiada justo después de la última hoja («3I») del documento 003, la traducción inédita de Paul Valéry «La muerte fingida». Queda como última página de ese PDF.

## Referencia de la serie EDC_15

10 carpetas, 881 imágenes (1 prueba de color: `EDC_15_001_000_000.jpg`), 251 documentos, 880 páginas, sin huecos, notas ni erratas. Salida en `EDC\EDC_15_PDF`, unos 503 MB.

## Referencia de la serie EDC_16

14 carpetas, 761 imágenes (1 prueba de color: `EDC_16_001_000_000.jpg`), 221 documentos, 760 páginas, sin huecos ni notas. Salida en `EDC\EDC_16_PDF`, unos 340 MB.
- La carpeta 013 llegó como `EDC_16_013_UNIR`. El documento 031 es un recorte largo («Un espectador en Madrid. Traducciones, reposiciones») fotografiado en dos mitades horizontales que se solapan (`_PARTE1`, `_PARTE2`). El usuario decidió no unirlas en una imagen nueva, para no recomprimir, sino dejarlas como páginas 001 y 002 (contenido idéntico por SHA-256; tabla en `EDC_16_renombrado.csv`). La carpeta pasó a `EDC_16_013`.

## Referencia de la serie EDC_17

17 carpetas, 1.003 imágenes (1 prueba de color: `EDC_17_001_000_000.jpg`), 275 documentos, 1.002 páginas, sin notas ni erratas. Salida en `EDC\EDC_17_PDF`, unos 451 MB. La carpeta 001 tiene 526 imágenes.
- Hueco: faltan los documentos 018 y 019 en la carpeta 017 (invitaciones). Los vecinos están anotados «17» y «20», y sus nombres coinciden. El hueco se respeta; está pendiente de contrastar con el original físico.

## Referencia de la serie EDC_18

19 carpetas, 585 imágenes (1 prueba de color: `EDC_18_001_000_000.jpg`), 492 documentos, 584 páginas, sin huecos, notas ni erratas. Salida en `EDC\EDC_18_PDF`, unos 336 MB.

## Referencia de la serie EDC_19

19 carpetas, 506 imágenes (1 prueba de color: `EDC_19_001_000_000.jpg`), 351 documentos, 505 páginas, sin huecos, notas ni erratas. Salida en `EDC\EDC_19_PDF`, unos 309 MB.

## Referencia de la serie EDC_20

6 carpetas, 235 imágenes (1 prueba de color: `EDC_20_001_000_000.jpg`), 135 documentos, 234 páginas, sin huecos, notas ni erratas. Salida en `EDC\EDC_20_PDF`, unos 210 MB.

## Referencia de la serie EDC_21

14 carpetas, 516 imágenes (1 prueba de color: `EDC_21_001_000_000.jpg`), 447 documentos, 515 páginas, sin huecos ni notas. Salida en `EDC\EDC_21_PDF`, unos 300 MB.
- Por decisión del usuario se renombraron tres documentos de una sola hoja que empezaban en la página 002 (contenido idéntico por SHA-256; tabla en `EDC_21_renombrado.csv`): `EDC_21_002_031_002`, `EDC_21_012_030_002` y `_031_002` → `_001`. Están anotados a lápiz «31», «30» y «31», sin letra.
- Informe para el digitalizador: `INFORME_ERRATAS_EDC_21_ED_1.txt`, en la raíz.

## Referencia de la serie EDC_22

14 carpetas, 506 imágenes (1 prueba de color: `EDC_22_001_000_000.jpg`, junto al periódico «Grito de carne»), 351 documentos, 505 páginas, sin huecos, notas ni erratas. Salida en `EDC\EDC_22_PDF`, unos 336 MB.
- Coincide con EDC_19 en documentos y páginas, pero no comparte ninguna imagen con ella (comprobado por SHA-256) y tiene otra estructura de carpetas: es una coincidencia.

## Referencia de la serie EDC_23

15 carpetas, 480 imágenes (1 prueba de color: `EDC_23_001_001_000.jpg`, junto a un recorte), 362 documentos, 479 páginas, sin huecos. Salida en `EDC\EDC_23_PDF`, unos 419 MB.
- Erratas corregidas por decisión del usuario (contenido idéntico por SHA-256; tabla en `EDC_23_renombrado.csv`; informe para el digitalizador en `INFORME_ERRATAS_EDC_23.txt`):
  - En la carpeta 002 había 22 imágenes `EDC_23_005_001_001` … `_022`, distintas del `005_001` de la carpeta 005. Son un álbum «Recortes» completo (tapa, recortes de abril de 1936 sobre el nombramiento de Díez-Canedo como embajador en Buenos Aires y contratapa), sin anotación a lápiz. Pasaron a ser el documento nuevo `EDC_23_002_006` (001–022).
  - Los documentos 052–056 de la carpeta 004 eran recortes de una hoja que empezaban en la página 002 (a lápiz «52»…«56», sin letra) → `_001`.
- `EDC_23.txt`: «carpeta 4, el documento 49B no existe». El `004_049` es una sola hoja, «49A», así que no hay hueco en los nombres.

## Referencia de la serie EDC_24

7 carpetas, 608 imágenes (1 prueba de color: `EDC_24_001_000_000.jpg`, junto al recorte «Con dolor de España, la esposa de Díez-Canedo…»), 261 documentos, 607 páginas, sin huecos ni notas. Salida en `EDC\EDC_24_PDF`, unos 504 MB.
- Llegó anidada (`EDC\EDC_24\EDC_24\…`) y con la carpeta `EDC_24_006_UNIR`. Por decisión del usuario se aplanó y la carpeta pasó a `EDC_24_006`.
- Erratas corregidas por decisión del usuario, sin unir imágenes ni recomprimir (contenido idéntico por SHA-256; tabla en `EDC_24_renombrado.csv`):
  - `EDC_24_002_040`: un número de «El Tiempo» (Madrid, 1879) de dos hojas, cada una fotografiada en dos mitades. `_001_PARTE1/2` y `_002_PARTE1/2` pasaron a ser `_001`…`_004`;
  - `EDC_24_006_036`: un recorte largo en tira, fotografiado en dos partes. `_001_PARTE1/2` pasaron a ser `_001` y `_002`, en un único PDF.

## Referencia de la serie EDC_25

18 carpetas, 819 imágenes (1 prueba de color: `EDC_25_001_001_000.jpg`), 83 documentos, 818 páginas, sin huecos ni erratas. Salida en `EDC\EDC_25_PDF`, unos 381 MB. La carpeta 005 tiene 443 imágenes.
- `EDC_25.txt`: «carpeta 014, el documento 3 es documentación suelta» (32 imágenes; sin efecto en los nombres).

## Fondo Ernesto Durán (`ERNESTO DURÁN\`)

Cajas `ED_1`, … con la estructura de siempre (`ED_1\ED_1_001\ED_1_001_001_001.jpg`). Salida: `python -I herramientas\procesar_fondo.py "ERNESTO DURÁN\ED_1" --salida "ERNESTO DURÁN"`.

## Referencia de la serie ED_1

14 carpetas, 571 imágenes (1 prueba de color: `ED_1_001_001_000.jpg`, junto a una carta manuscrita), 214 documentos, 570 páginas. Salida en `ERNESTO DURÁN\ED_1_PDF`, unos 371 MB.
- Erratas corregidas por decisión del usuario (contenido idéntico por SHA-256; tabla en `ED_1_renombrado.csv`; informe para el digitalizador en `INFORME_ERRATAS_EDC_21_ED_1.txt`):
  - `ED_1_006_059_003  .jpg`, con dos espacios antes de la extensión → `ED_1_006_059_003.jpg` (a lápiz «59C»);
  - en la carpeta 014, `ED_1_013_002_001.jpg` y `ED_1_013_003_001.jpg` → `ED_1_014_002_001.jpg` y `ED_1_014_003_001.jpg`. Son distintas de las de igual nombre de la carpeta 013: el recorte «Capital mourns passing of Tobey» y «Cultura», del 25-II-1995.
- Hueco que se respeta: falta el documento 026 de la carpeta 006 (vecinos «25A/25B» y «27A»). Está pendiente de contrastar con el original físico.
- `ED_1.txt`, sin efecto en los nombres: «carpeta 004, el documento 4 tendría A, B y C» (tiene 3 páginas); «carpeta 006, el documento 15 tendría B» (tiene 2); «la carpeta 12 está repetida, sería 13» (las carpetas 012 y 013 tienen nombres correctos y contenido distinto; quizá se refiere a la etiqueta física).

## Referencia de la serie JMR_039

16 carpetas, 881 imágenes (1 prueba de color: `JMR_39_001_001_000.jpg`), 485 documentos, 880 páginas. Salida en `JMR\JMR_039_PDF`.
- Errata corregida por decisión del usuario (contenido idéntico por SHA-256): `JMR_39_007_00_002.jpg` → `JMR_39_007_002_002.jpg` (a lápiz «2B», sigue a la hoja «2A»).
- Hueco: falta el documento 033 de la carpeta 015. Las anotaciones de los documentos vecinos («32», «34A», «34B») coinciden con sus nombres. El hueco se respeta; está pendiente de contrastar con el original físico.
- `INCIDENCIAS.txt` avisa de una anotación a lápiz equivocada: «27E» en `JMR_39_015_027_004` debería ser 27D. El nombre de archivo ya era correcto.

## Referencia de la serie JMR_040

17 carpetas, 836 imágenes (1 prueba de color, en la carpeta 001), 422 documentos, 835 páginas, sin huecos tras corregir las erratas. Salida en `JMR\JMR_040_PDF`, unos 395 MB.
- Erratas corregidas por decisión del usuario (contenido idéntico por SHA-256): `JMR_40_006_001_003.jpg` → `JMR_40_006_003_001.jpg` (carta distinta, a lápiz «3a»); `JMR_40_006_006_002.jpg` → `JMR_40_006_005_002.jpg` (segunda hoja de la carta 5, a lápiz «5b»).
- `INCIDENCIA.txt` avisa de dos anotaciones a lápiz equivocadas en los originales físicos: «39D» en `JMR_40_007_039_002` debería ser 39B, y «3B» en `JMR_40_009_002_002` debería ser 2B. Los nombres de archivo ya eran correctos.
- Solo se han comprobado a ojo los casos señalados por la revisión. Una errata que no deje hueco en la numeración no se detecta.

## Referencia de la serie JMR_041

16 carpetas, 864 imágenes (1 prueba de color: `JMR_41_001_001_000.jpg`), 450 documentos, 863 páginas, sin huecos tras corregir las erratas. Salida en `JMR\JMR_041_PDF`, unos 568 MB.
- Erratas corregidas por decisión del usuario (contenido idéntico por SHA-256): `JMR_41_001_001_00.jpg` → `JMR_41_001_001_000.jpg` (prueba de color); `JMR_41_010_028_001` con un carácter invisible DEL (`0x7F`) en el nombre → `JMR_41_010_028_002.jpg` (a lápiz «28B»); `JMR_41_004_001_002.jpg` → `JMR_41_004_002_001.jpg` (carta distinta, a lápiz «2»); `JMR_41_014_006_008.jpg` → `JMR_41_014_008_001.jpg` (carta distinta, a lápiz «8»).
- Las 54 imágenes de la carpeta 016 estaban sueltas en la raíz de la serie; se movieron a `JMR_41_016\` por decisión del usuario, sin cambiar sus nombres.
- `INCIDENCIAS.txt`: en `JMR_41_008_018` falta la anotación de la hoja B; `JMR_41_009_043` «son tres documentos», pero son tres imágenes que parecen una sola carta y se dejan como un solo PDF, pendiente de contrastar; la anotación «19B» en `JMR_41_011_018_002` debería ser 18B. Ninguna afecta a los nombres de archivo.
- Solo se han comprobado a ojo los casos señalados por la revisión. Una errata que no deje hueco en la numeración no se detecta.

## Referencia de la serie JMR_042

10 carpetas, 835 imágenes (1 prueba de color: `JMR_42_001_001_000.jpg`), 433 documentos, 834 páginas. Salida en `JMR\JMR_042_PDF`, unos 482 MB.
- Erratas corregidas por el usuario: `JMR_42_005_047_008.jpg` → `JMR_42_005_048_001.jpg` (a lápiz «48A»); `JMR_42_007_020_001` con un carácter DEL (`0x7F`) en el nombre → `JMR_42_007_020_002.jpg` (a lápiz «20B»).
- Propuestas que el usuario decidió no aplicar: `JMR_42_010_030_007` y `_030_008` están anotadas «31» y «32» y son cartas distintas, pero quedan dentro del PDF del documento 030. `JMR_42_006_013` tiene las páginas 001 y 003 (la 003 es el reverso fotográfico de la postal).
- Huecos: faltan los documentos 025 y 026 en la carpeta 006 (los vecinos están anotados «24» y «27A»), y el 005 en la 010 (vecinos «4» y «6»). Con las decisiones anteriores, también faltan el 031 y el 032 en la 010.
- `INCIDENCIAS.txt`: en la carpeta 007, del 19A no existe el B. En la carpeta 010, la 30B lleva detrás la C sin marcar y la 30C lleva detrás la D sin marcar; el texto continúa desde la B.

## Referencia de la serie JMR_044

12 carpetas, 792 imágenes (1 prueba de color: `JMR_44_001_001_000.jpg`), 296 documentos, 791 páginas. Salida en `JMR\JMR_044_PDF`, unos 435 MB.
- La carpeta de la serie se llamaba `JMR_44`; se renombró a `JMR_044` por decisión del usuario. Las subcarpetas y las imágenes conservan `JMR_44_…`.
- Erratas corregidas por decisión del usuario (contenido idéntico por SHA-256): las 85 imágenes de las carpetas 008 y 009 tenían la página con 4 cifras (`JMR_44_008_001_0001.jpg` → `JMR_44_008_001_001.jpg`). Cada carpeta es una sola obra mecanografiada: «Aurora (poema dramático en prosa)», de 38 páginas, y «Estaba anocheciendo (farsa dramática)», de 47.
- Huecos de página: `JMR_44_004_031` tiene las páginas 001 y 003 (a lápiz «31A» y «31C»; el texto no continúa, así que falta la hoja B). `JMR_44_011_047` solo tiene la 002 (a lápiz «47B»; empieza a mitad de frase, así que falta la hoja A). Se respetan; están pendientes de contrastar con los originales físicos.
- `INCIDENCIAS_44.txt`: en `JMR_44_011_001` la anotación a lápiz salta de «1D» a «1F». La carta termina firmada en la 1D y la 1F es el sobre, así que no parece faltar ninguna hoja. Los nombres de archivo son correlativos.

## Referencia de la serie JMR_045

11 carpetas, 880 imágenes, **sin prueba de color**, 528 documentos, 880 páginas. Salida en `JMR\JMR_045_PDF`, unos 2.056 MB: los JPG originales pesan de media unos 2,3 MB (unos 3.700×5.100 px a 200 dpi), unas cuatro veces más que en las series anteriores.
- La carpeta de la serie se llamaba `JMR_45`; se renombró a `JMR_045` por decisión del usuario. Las subcarpetas y las imágenes conservan `JMR_45_…`.
- Erratas corregidas por decisión del usuario (contenido idéntico por SHA-256): las 32 imágenes de `JMR_45_004_036` tenían la página con 4 cifras (`_0001` → `_001`; es un impreso: «Revista de Occidente. Vicente Aleixandre: primeros poemas»). `JMR_45_011_036_001.jpg` → `JMR_45_011_026_001.jpg` (a lápiz «26», sigue a la «25»).
- Huecos explicados en `INCIDENCIAS_45.txt` («no se digitaliza»): el documento 043 y la hoja 044A en la carpeta 001; la hoja 013A en la 002; el documento 007 en la 009.
- Huecos que no aparecen en la nota: falta el documento 026 en la 004 (vecinos «25» y «27A»); falta el 043 en la 010 (vecinos «42A» y «44»; el 042 solo tiene la hoja A); en `JMR_45_002_034` faltan las páginas 005 y 006 (las hojas «34E» y «34F»; las de alrededor están anotadas «34D» y «34G»); `JMR_45_002_046` solo tiene la 002 («46B», que empieza a mitad de texto).
- `JMR_45_006_002` tiene las páginas 001, 002, 003 y 005, anotadas hasta «2C» y después «2E»: falta la 2D. La nota dice «2C no existe», pero la 2C sí está, así que probablemente quería decir 2D.
- Resto de `INCIDENCIAS_45.txt`, sin efecto en los nombres: «002_010 tiene B» (están la 001 y la 002); «004_012D no está, salta al E» (las páginas 001–008 son correlativas); «006_033» y «008_043 hoja A» tienen texto a la vuelta; «010_032C, luego vendría el D» (páginas 001–005 correlativas).
- Todos los huecos se respetan; están pendientes de contrastar con los originales físicos.

## Referencia de la serie JMR_046

12 carpetas, 799 imágenes, **sin prueba de color**, 442 documentos, 799 páginas. Salida en `JMR\JMR_046_PDF`, unos 490 MB.
- La carpeta de la serie se llamaba `JMR_46`; se renombró a `JMR_046` por decisión del usuario. Las subcarpetas y las imágenes conservan `JMR_46_…`.
- Erratas corregidas por decisión del usuario (contenido idéntico por SHA-256): 99 imágenes tenían la página con 4 cifras (`_0001` → `_001`): la carpeta 009 entera (67 imágenes, un único expediente: el del Premio Juan Lladó) y `JMR_46_011_011` (32 imágenes, el mecanoscrito «El paro en España» de Antonio Robert).
- La nota del digitalizador se llama `INCIDENCIAS_45.txt`, pero habla de la caja 46. Dice que el `005_015` «viene paginado así» (la paginación del original salta: 5, 7, 11, 12, 14…; los nombres de archivo son correlativos) y que la carpeta 009 es un «expediente único».
- Huecos de página que se respetan: `JMR_46_005_035` solo tiene la 002 (a lápiz «35B», un aerograma; falta la A). `JMR_46_006_043` tiene la 001 y la 003, anotadas «43B» y «43C», y el texto pasa directamente de una a otra. Si falta algo, sería una «43A» anterior. El usuario decidió no renombrar la 003. Ambos huecos están pendientes de contrastar con los originales físicos.

## Referencia de la serie JMR_047

8 carpetas, 516 imágenes (1 prueba de color: `JMR_47_001_001_000.jpg`, junto a la hoja «1A»), 161 documentos, 515 páginas. Salida en `JMR\JMR_047_PDF`, unos 408 MB.
- Llegó con muchas erratas, enumeradas para el equipo de digitalización en `JMR\JMR_047\INFORME_REVISION_JMR_47.txt` (escrito antes de corregirlas).
- Por decisión del usuario se renombraron 255 imágenes (contenido idéntico por SHA-256; tabla en `JMR_47_renombrado.csv`) y la carpeta `JMR_47` pasó a `JMR_047`:
  - las 64 de la carpeta 002 se llamaban `JMR_47_001_…` → `JMR_47_002_…`;
  - 10 de la carpeta 003 llevaban la caja 45 → 47;
  - 185 tenían la página con 4 cifras → 3, y la prueba de color `_0000` → `_000`;
  - `JMR_47_005\0444.jpg` y `0445.jpg` (recortes del «Ya», 20-VI-1982, a lápiz «4A» y «4B», distintos del folleto del «Hoy» que es el 004) → documento nuevo `JMR_47_005_007` (001–002);
  - `JMR_47_006_030` tenía las parejas recorte + ficha cruzadas y dos `_DUPLICADO`. Quedó en un solo PDF emparejado por contenido: 001 recorte de ABC (25-XI-1945), 002 ficha «Melchor F.ª Almagro, 25-11-1945» (antes `_002_DUPLICADO`), 003 recorte «Libros, por Rafael Ferreres» (antes `_001_DUPLICADO`), 004 ficha «Rafael Ferreres, nov. 1945» (antes `_002`).
- Huecos explicados en `INCIDENCIAS_47.txt` («no se digitaliza» / «no existe»): documento 011 de la carpeta 002, 013 de la 007 y 004 de la 008; `JMR_47_006_036` y `JMR_47_008_007` solo tienen la hoja A; `JMR_47_006_037` tiene las páginas 001 y 003.
- Hueco por confirmar: `JMR_47_006_029` tiene la 001 y la 003 (la 003 es la ficha «29C»). La nota dice «29 tiene A y B, cómo se corta»: quizá el recorte A+B se fotografió en una sola imagen.
- Todos los huecos se respetan; están pendientes de contrastar con los originales físicos.

## Referencia de la serie JMR_048

11 carpetas, 561 imágenes (1 prueba de color: `JMR_48_001_001_000.jpg`, junto a la hoja «1A»), 227 documentos, 560 páginas, sin huecos. Salida en `JMR\JMR_048_PDF`, unos 339 MB.
- Por decisión del usuario (contenido idéntico por SHA-256; tabla en `JMR_48_renombrado.csv`), la carpeta `JMR_48` pasó a `JMR_048` y se cambiaron 52 imágenes:
  - 51 imágenes de la carpeta 004 (documentos 002–031) se llamaban `JMR_48_001_…` → `JMR_48_004_…`. Las anotaciones a lápiz coinciden con el número de documento.
  - `JMR_48_011_004_002.jpg` era la misma foto que la `_001` (folleto «United air atlas», «4A»; píxeles idénticos). Se apartó sin borrarla a `JMR\JMR_048_apartadas\`.
- `INCIDENCIAS_48.txt`, sin efecto en los nombres:
  - «001 23C no se digitaliza» y «006 10B no se digitaliza»;
  - «004 archivo 30 tiene B» (están la 001 y la 002);
  - en `JMR_48_005_013_004` la anotación a lápiz dice «9D» y debería ser 13D;
  - «011 archivo 2: digitalizar portada entera» (es una sola imagen con la cubierta desplegada);
  - «011_004_001 ¿se corta?»: el folleto se ve entero.

## Referencia de la serie JMR_049

8 carpetas, 836 imágenes (1 prueba de color: `JMR_49_001_001_000.jpg`, junto a la portada del 001), 44 documentos, 835 páginas, sin huecos. Salida en `JMR\JMR_049_PDF`, unos 686 MB. La carpeta `JMR_49` pasó a `JMR_049` por decisión del usuario.
- Mecanoscritos largos:
  - `001_001`: «Desde el amanecer (autobiografía)», de Rosa Chacel, 207 imágenes. `INCIDENCIAS_49.txt` dice «página 95 no existe»: es un salto de la paginación del original, no de los nombres.
  - `002_001`: otra copia de la misma obra, 165 imágenes.
  - `003_001`: poemas («El último invierno», «Tiempo último 2»…).
  - `004_001`: «Invocación al silencio», de José Luis Miranda.
- Por decisión del usuario se renumeraron las 93 imágenes de `003_001`, que iban de la 125 a la 217, como 001–093 (contenido idéntico por SHA-256; tabla en `JMR_49_50_renombrado.csv`). No llevan paginación propia que explique el 125. Si las «1–124» aparecen en otra caja, habrá que revisarlo.

## Referencia de la serie JMR_050

8 carpetas, 743 imágenes (1 prueba de color: `JMR_50_001_001_000.jpg`, junto a la hoja «1A»), 226 documentos, 742 páginas. Salida en `JMR\JMR_050_PDF`, unos 952 MB. La carpeta `JMR_50` pasó a `JMR_050` por decisión del usuario.
- Erratas corregidas por decisión del usuario (contenido idéntico por SHA-256; tabla en `JMR_49_50_renombrado.csv`):
  - `JMR_50_003_017_0022.jpg` → `_017_002.jpg` (a lápiz «17B»);
  - `JMR_50_001_001_011.jpg` → `JMR_50_001_002_001.jpg` (a lápiz «2», carta de la Fundación de Estudios Sociológicos; el 001 son las hojas 1A–1J);
  - `JMR_50_005\0308.jpg` y `0309.jpg` (carta «Querida María…», 26-II-87, anotada «14A» y «14B», distinta del 014 en inglés de Marcia) → documento nuevo `JMR_50_005_033` (001–002);
  - `JMR_50_008\0624.jpg` y `0625.jpg` («Proyecto de contrato», anotado «6A» y «6B») → `JMR_50_008_006_004` y `_005`, dentro del 006: la carátula `008_012` lo enumera junto al escrito y el proyecto de Estatuto.
- **Extensión (2026-11-20, `JMR\JMR_50_EXTENSION`):** llegó el documento 029 de la carpeta 001 (`029_001` y `029_002`). Es una postal de «Alfonso» desde San Martín de los Andes (lago Lolog), con fecha 27-III-87 y la anotación a lápiz «29». Se generó `JMR_50_001_029.pdf`, de 2 páginas idénticas byte a byte a los JPG, y se añadió a `JMR_050_PDF` sin rehacer el resto.
  - El anverso (`029_002`) es la misma postal que la página 2 de `JMR_50_001_028`, la «foto de paisaje sin anotar». Es otra fotografía, con otro SHA-256, pero de la misma pieza. Probablemente la `028_002` era este anverso mal colocado.
- **En `JMR_050_PDF` falta `JMR_50_004_026.pdf`** (detectado el 2026-11-20). La carpeta tiene 226 PDFs y 723 páginas con el 029. Debería tener 227 y unas 744, así que faltan unas 21 páginas. La carpeta se modificó el 2026-11-19 a las 16:58. El PDF no está en la papelera y las imágenes ya no están en el proyecto.
- Huecos que se respetan, pendientes de contrastar con los originales físicos:
  - `JMR_50_004_006` empieza en la página 002 («6B», que es la p. 2 de la carta): falta la hoja 6A.
- `INCIDENCIAS_50.txt`: la anotación de `JMR_50_002_013_007` debería ser «13G» (sin efecto en los nombres).

## Referencia de la serie JMR_051

8 carpetas, 419 imágenes (1 prueba de color: `JMR_51_001_001_000.jpg`, junto a un folleto de Pan American), 129 documentos, 418 páginas, sin huecos. Salida en `JMR\JMR_051_PDF`, unos 308 MB. La carpeta `JMR_51` pasó a `JMR_051` por decisión del usuario.
- Errata corregida por decisión del usuario (contenido idéntico por SHA-256; tabla en `JMR_51_52_renombrado.csv`): `JMR_51_004\JMR_51_005_001_001.jpg` → `JMR_51_004_005_001.jpg` (a lápiz «5», télex de Colville, entre la «4» y la «6»).
- `INCIDENCIAS_51.txt`: en la carpeta 005, las hojas «26B» y «47B» no se digitalizan. Sus documentos acaban en la hoja A, así que no hay hueco en la numeración.

## Referencia de la serie JMR_052

10 carpetas, 764 imágenes (1 prueba de color: `JMR_52_001_001_000.jpg`), 98 documentos, 763 páginas, sin huecos. Salida en `JMR\JMR_052_PDF`, unos 586 MB.
- Las carpetas 009 y 010 llegaron el 2026-11-20 en `JMR\JMR_52_PARA_UNIR`, sin erratas. Se movieron a `JMR_052` y se regeneró toda la caja.
  - **009:** planos grandes en 5 documentos y 9 imágenes. El 001 y el 002 son el «Proyecto de reforma en la casita del guarda de la finca Las Zagalas» (estado actual y alzado). El 003 y el 004 son tramos de planos fotografiados por partes («Villa Carmen», carretera de Málaga a Almería). El 005 es un plano en papel transparente.
  - **010:** 26 sobres. Del 001 al 023 hay dos páginas por sobre (anverso «A» y reverso «B»); del 024 al 026, una sola. Muchos son de Jorge Guillén y de Sánchez-Albornoz.
- **Un PDF por carpeta en la 009 y la 010 (decisión del usuario, 2026-11-24):** sus 31 PDFs por documento se sustituyeron por `JMR_52_009.pdf` (9 páginas) y `JMR_52_010.pdf` (49 páginas). Las páginas van en el orden de los nombres y son idénticas byte a byte a los JPG. `JMR_052_PDF` tiene ahora 69 PDFs: 67 por documento de las carpetas 001–008 y esos 2.
  - Por eso `procesar_fondo.py JMR\JMR_052 --verificar` dará error en esas carpetas, porque espera un PDF por documento. **No volver a generar la caja con `procesar_fondo.py`**, o se recrearían los 31 PDFs sueltos. Para rehacerlos, usar `img2pdf.convert` con los JPG ordenados de cada carpeta. La carpeta `JMR_52` pasó a `JMR_052` por decisión del usuario.
- Por decisión del usuario (contenido idéntico por SHA-256; tabla en `JMR_51_52_renombrado.csv`), las 17 imágenes `JMR_52_003_020_010` … `_036_010` se renombraron como `JMR_52_003_006_001` … `_017`, en el mismo orden. Son un mecanoscrito de poemas en papel blanco, sin anotación a lápiz, distinto del 005 («Poemas líricos»). Empieza con «Cambridge», y la siguiente hoja está paginada «-20-», así que serían las pp. 19–35 del original: faltan las pp. 1–18, pendientes de contrastar con el original físico.
- `INCIDENCIAS_52.txt`: «`JMR_52_005_004_001` y siguientes mal paginado». Se refiere a la paginación del original; los nombres de archivo son correlativos.

## Fondo Gustavo Durán (`GUSTAVO DURÁN - EXTENSIÓN\`)

Cajas `GD_1`, … con la estructura de siempre (`GD_1\GD_1_001\GD_1_001_001_001.jpg`). La salida va junto a las cajas: `python -I herramientas\procesar_fondo.py "GUSTAVO DURÁN - EXTENSIÓN\GD_1" --salida "GUSTAVO DURÁN - EXTENSIÓN"`.

## Referencia de la serie GD_1

16 carpetas, 763 imágenes (1 prueba de color: `GD_1_001_001_000.jpg`, junto a la primera carta), 251 documentos, 762 páginas, sin huecos de documentos. Salida en `GUSTAVO DURÁN - EXTENSIÓN\GD_1_PDF`, unos 593 MB.
- Por decisión del usuario se renombraron 20 imágenes (contenido idéntico por SHA-256; tabla en `GD_1_renombrado.csv`):
  - Carpeta 004: 18 imágenes con el número de la cámara cubrían los 12 documentos que faltaban, según la anotación a lápiz:
    - 015: postal «15A» (001), su anverso, el Pisanello de `190_1` (002), y el sobre `0193`, «15B» (003);
    - 016: `0194`–`0195`;
    - 017: `0196`;
    - 018: `0197`–`0198`;
    - 019: `0199`–`0200`;
    - 020: `0201`, «20A», y el sobre `0206`, «20B»;
    - 021: `0207`;
    - 022: `0204`;
    - 023: `0205`;
    - 024: `0208`;
    - 028: `0213`;
    - 029: `0214`;
    - 030: `0215`.
  - Carpeta 010: `GD_1_010_010_007_011/_012` (a lápiz «7K», «7L») → `GD_1_010_007_011/_012`.
- Hueco de nombre que se respeta: `GD_1_014_001` salta del archivo 024 al 026, pero la paginación del original es seguida (22, 23, 24, 25): no falta ninguna hoja.
- `GD_1.txt` (nota del digitalizador), sin efecto en los nombres: «014: del 106 salta al 121» y «015: el documento 16 comienza en pág. 3» se refieren a la paginación del original; «`GD_1_016_015_004` sería D» corrige una anotación a lápiz.

## Referencia de la serie GD_12

El usuario pidió **no generarla** de momento (2026-11-19). No se ha revisado.

## Referencia de la serie GD_13

9 carpetas, 517 imágenes (1 prueba de color: `GD_13_001_001_000.jpg`, junto a un artículo «He Was Never a Soviet Spy»), 96 documentos, 516 páginas, sin huecos ni erratas. Salida en `GUSTAVO DURÁN - EXTENSIÓN\GD_13_PDF`, unos 463 MB.
- La nota `GD_13.txt` empieza con «CAJA_2» por error, pero habla de esta caja. Ninguno de sus avisos afecta a los nombres de archivo:
  - carpeta 004: el documento 1A no tiene hoja B;
  - carpeta 006: la hoja 14AI no existe;
  - carpeta 008: el documento 9 empieza en la p. 4 (paginación del original).

## Referencia de la serie GD_14

11 carpetas, 645 imágenes (1 prueba de color: `GD_14_001_001_000.jpg`), 143 documentos, 644 páginas. Salida en `GUSTAVO DURÁN - EXTENSIÓN\GD_14_PDF`, unos 445 MB.
- Errata corregida por decisión del usuario (contenido idéntico por SHA-256; tabla en `GD_14_renombrado.csv`): `GD_14_001_022_0022.jpg` → `GD_14_001_022_002.jpg` (a lápiz «22B», p. «-2-» de la carta).
- Hueco que se respeta: falta el documento 003 de la carpeta 007 (vecinos «2A» y «4»). Está pendiente de contrastar con el original físico.
- Huecos solo de nombre: `GD_14_011_001` (expediente del FBI, 122 imágenes) salta las páginas 032 y 092. La paginación del original sigue (61, 62, 63, 64 alrededor de la 092; en la 031 acaba un memorando y en la 033 empieza otro informe), así que no falta ninguna hoja.
- `GD_14.txt`: «carpeta 008: el documento 1B está repetido, sería 1C». Se refiere a la anotación a lápiz; los nombres de archivo son correlativos.

## Referencia de la serie VARIOS_IV_ED (Ernesto Durán)

`ERNESTO DURÁN\VARIOS_IV_ED\VARIOS_IV_ED_001\`: 79 imágenes de fotografías, con otra nomenclatura. Las fotos de una sola imagen se llaman `VARIOS_IV_ED_DDD.jpg`; las que tienen anverso y reverso, `VARIOS_IV_ED_DDD_001/002.jpg`. Los nombres no llevan el número de carpeta.
- 1 prueba de color (`VARIOS_IV_ED_000.jpg`) y 56 documentos (001–056), de los que 22 tienen 2 imágenes. Son 78 páginas, sin huecos.
- `procesar_fondo.py` no reconoce este patrón: lo da todo como fuera de patrón. Los PDFs se generaron el 2026-11-24 con un script aparte (img2pdf, verificación byte a byte) en `ERNESTO DURÁN\VARIOS_IV_ED_PDF\VARIOS_IV_ED_DDD.pdf`, unos 14 MB.

## Fondo AEM: separar expedientes en cartas (`AEM\`)

Tarea distinta de la digitalización: en `AEM\PDF\` hay 13 PDFs matriz, uno por expediente (`FON_AEMC-CAJ_65_EXP_564.pdf` … `CAJ_67-EXP_576.pdf`; en la caja 65 el separador antes de `EXP` es `_` y en la 66 y la 67, `-`). Son escaneos del Fondo Histórico del Ateneo Español de México, serie Correspondencia, con OCR de ABBYY FineReader 14. No tienen marcadores ni separadores entre cartas.
- **Objetivo (2026-11-24):** separar cada carta en su propio PDF, sin mezclar documentos. Los PDFs se llaman como la matriz más `_NNN`, en orden ascendente, y van en `AEM\EXP_<n>\`.
- **Herramienta:** `herramientas\separar_cartas.py <matriz> <salida> "<rangos>" --excluir 1-2`. Copia las páginas con pikepdf sin recomprimir y conserva el texto OCR. Comprueba que cada página va a un solo documento o se excluye, que el orden es el correcto y que cada página es idéntica a la de la matriz. También escribe `<matriz>_indice.csv`.
- **Cómo se deciden los límites:** con hojas de contacto de todas las páginas y el texto del OCR (inicio y final de cada página). Cada folio lleva a lápiz, arriba a la derecha, el número de foja del archivo.
  - Van juntos en un PDF: las cartas de varias páginas, los anexos que la carta dice que adjunta y el reverso de una hoja.
  - Las copias duplicadas de una misma carta van por separado.
- Las páginas 1 y 2 de cada matriz son la portada y la contraportada de la carpeta. Se excluyen.

### EXP_564 (prueba, 2026-11-24)

190 páginas → 177 PDFs en `AEM\EXP_564`, con las páginas 3–190; se excluyen la 1 y la 2. Rangos en `AEM\EXP_564\FON_AEMC-CAJ_65_EXP_564_indice.csv`. Documentos de varias páginas:
- 14–16: carta del PCE, 3 páginas;
- 18–20: carta de Metro-Goldwyn-Mayer y su lista de películas;
- 29–30: carta de Enrique Muñoz Orts y su reverso, con anotaciones;
- 32–34: carta de Robles («Recibe estos recortes…») y sus 2 recortes;
- 84–85: Rubén Landa, manuscrita;
- 108–109: Rivas Cherif, manuscrita;
- 161–162: Faustino Ballvé;
- 179–180: Instituto de Intercambio Cultural Mexicano-Ruso.

Se dejaron por separado, pendiente de que lo confirme el usuario: 8 y 9, y 28 y 31, que son dos copias de la misma carta o circular; y 189 y 190, dos recortes de prensa sueltos al final.

## Entorno

- Windows, PowerShell 5.1, Python 3.13 con Pillow, img2pdf, pikepdf y pypdfium2 (no hay numpy).
- Tesseract 5.4 en `C:\Program Files\Tesseract-OCR\`.
- Para revisar visualmente un PDF marcado o extraer su texto, usar pypdfium2.
- El usuario trabaja en español.
