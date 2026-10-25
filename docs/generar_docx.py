"""
Genera ``docs/Documentacion_Sistema_Inventarios_Manaudi.docx`` a partir de los
manuales en Markdown (README.md, manual_usuario.md, manual_tecnico.md, guion_demo.md).

Uso (desde la raíz del repositorio, con Python 3 y ``pip install python-docx``):

    python docs/generar_docx.py

La tabla de contenido se inserta como campo de Word; al abrir el documento, Word
pide actualizar campos (o pulsar F9 sobre la tabla). Las capturas de pantalla
opcionales se toman de ``docs/capturas/<nombre>.png`` cuando un Markdown contiene
una línea ``![texto](capturas/<nombre>.png)``.

Convierte un subconjunto de Markdown: encabezados, párrafos con **negrita**,
`código` y [enlaces](url), listas con viñetas (anidadas por indentación), listas
numeradas, tablas con tuberías, bloques de código, citas y separadores.
"""
import re
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / 'docs'
SALIDA = DOCS / 'Documentacion_Sistema_Inventarios_Manaudi.docx'

AZUL = RGBColor(0x1F, 0x3A, 0x5F)
GRIS_TEXTO = RGBColor(0x59, 0x59, 0x59)
FUENTE = 'Calibri'
MONO = 'Consolas'

# Sustituciones de emojis que no se ven bien en Word
REEMPLAZOS = {'✅': '✓', '✔️': '✓', '✏️': 'Editar', '🚫': 'Desactivar', '⚠️': '⚠', '──▶': '→', '──': '—'}


# ---------------------------------------------------------------------------
# Utilidades de bajo nivel (XML)
# ---------------------------------------------------------------------------

def sombrear(celda_o_parrafo, color_hex):
    """Aplica un fondo sólido a una celda o a un párrafo."""
    pr = celda_o_parrafo._tc.get_or_add_tcPr() if hasattr(celda_o_parrafo, '_tc') else celda_o_parrafo._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    pr.append(shd)


def campo(parrafo, instruccion, texto_inicial=''):
    """Inserta un campo de Word (PAGE, TOC, ...) en el párrafo."""
    run = parrafo.add_run()
    begin = OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'), 'begin'); begin.set(qn('w:dirty'), 'true')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = instruccion
    sep = OxmlElement('w:fldChar'); sep.set(qn('w:fldCharType'), 'separate')
    txt = OxmlElement('w:t'); txt.text = texto_inicial
    end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end')
    for el in (begin, instr, sep, txt, end):
        run._r.append(el)


def bordes_tabla(tabla):
    """Bordes finos grises en toda la tabla."""
    tblPr = tabla._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for lado in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        b = OxmlElement(f'w:{lado}')
        b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), '4'); b.set(qn('w:space'), '0'); b.set(qn('w:color'), 'A6A6A6')
        borders.append(b)
    tblPr.append(borders)


def evitar_division_fila(fila):
    trPr = fila._tr.get_or_add_trPr()
    cant = OxmlElement('w:cantSplit')
    trPr.append(cant)


# ---------------------------------------------------------------------------
# Texto en línea: **negrita**, `código`, [texto](url)
# ---------------------------------------------------------------------------

INLINE = re.compile(r'(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|<[^ >]+>)')


def limpiar(texto):
    for a, b in REEMPLAZOS.items():
        texto = texto.replace(a, b)
    return texto


def agregar_inline(parrafo, texto, tam=None, negrita_base=False, color=None):
    """Agrega ``texto`` al párrafo interpretando el marcado en línea."""
    for parte in INLINE.split(limpiar(texto)):
        if not parte:
            continue
        if parte.startswith('**') and parte.endswith('**'):
            run = parrafo.add_run(parte[2:-2]); run.bold = True
        elif parte.startswith('*') and parte.endswith('*') and len(parte) > 2:
            run = parrafo.add_run(parte[1:-1]); run.italic = True
        elif parte.startswith('`') and parte.endswith('`'):
            run = parrafo.add_run(parte[1:-1]); run.font.name = MONO
            run._element.rPr.rFonts.set(qn('w:eastAsia'), MONO)
            run.font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)
        elif parte.startswith('[') and '](' in parte:
            etiqueta, url = parte[1:-1].split('](', 1)
            run = parrafo.add_run(etiqueta); run.italic = True
            if url.startswith('http'):
                parrafo.add_run(f' ({url})').font.color.rgb = GRIS_TEXTO
        elif parte.startswith('<http') and parte.endswith('>'):
            run = parrafo.add_run(parte[1:-1]); run.font.color.rgb = RGBColor(0x1F, 0x5F, 0xBF)
        else:
            run = parrafo.add_run(parte)
            if negrita_base:
                run.bold = True
        if tam:
            run.font.size = Pt(tam)
        if color is not None:
            run.font.color.rgb = color


# ---------------------------------------------------------------------------
# Conversor Markdown -> docx
# ---------------------------------------------------------------------------

class Conversor:
    def __init__(self, doc):
        self.doc = doc

    def encabezado(self, nivel, texto):
        h = self.doc.add_heading(level=nivel)
        agregar_inline(h, texto.strip())
        return h

    def parrafo(self, texto, estilo=None):
        p = self.doc.add_paragraph(style=estilo)
        agregar_inline(p, texto.strip())
        return p

    def cita(self, lineas):
        p = self.doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.8)
        sombrear(p, 'F2F7FB')
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        left = OxmlElement('w:left'); left.set(qn('w:val'), 'single'); left.set(qn('w:sz'), '18'); left.set(qn('w:space'), '8'); left.set(qn('w:color'), '1F3A5F')
        pBdr.append(left); pPr.append(pBdr)
        agregar_inline(p, ' '.join(l.strip() for l in lineas), color=RGBColor(0x33, 0x33, 0x33))

    def codigo(self, lineas):
        for linea in lineas or ['']:
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.left_indent = Cm(0.3)
            sombrear(p, 'F3F3F3')
            run = p.add_run(limpiar(linea.rstrip()) or ' ')
            run.font.name = MONO; run.font.size = Pt(8.5)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), MONO)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def lista(self, items):
        """items: lista de (nivel, numerada, texto). La numeración se reinicia en cada lista."""
        contador = {}
        for nivel, numerada, texto in items:
            if numerada:
                contador[nivel] = contador.get(nivel, 0) + 1
                for n in [n for n in contador if n > nivel]:
                    del contador[n]
                p = self.doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.75 + 0.75 * nivel)
                p.paragraph_format.first_line_indent = Cm(-0.6)
                p.paragraph_format.space_after = Pt(2)
                p.add_run(f'{contador[nivel]}.\t')
                agregar_inline(p, texto)
            else:
                # Una viñeta anidada no reinicia la numeración de los niveles superiores
                for n in [n for n in contador if n >= nivel]:
                    del contador[n]
                estilo = 'List Bullet' + ('' if nivel == 0 else f' {min(nivel + 1, 3)}')
                p = self.doc.add_paragraph(style=estilo)
                agregar_inline(p, texto)

    def tabla(self, filas):
        filas = [f for f in filas if not re.match(r'^\|?\s*:?-{2,}', f)]
        celdas = [[c.strip() for c in f.strip().strip('|').split('|')] for f in filas]
        ncol = max(len(f) for f in celdas)
        tabla = self.doc.add_table(rows=0, cols=ncol)
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        tabla.autofit = False
        bordes_tabla(tabla)
        # Ancho de columnas proporcional al texto más largo de cada una (mínimo 2.2 cm)
        total = 16.6
        pesos = [max(2.2, min(9.0, max(len(f[j]) if j < len(f) else 0 for f in celdas) ** 0.75 / 2.2)) for j in range(ncol)]
        anchos = [Cm(total * w / sum(pesos)) for w in pesos]
        for i, fila in enumerate(celdas):
            celdas_fila = tabla.add_row().cells
            evitar_division_fila(tabla.rows[-1])
            for j in range(ncol):
                texto = fila[j] if j < len(fila) else ''
                c = celdas_fila[j]
                c.width = anchos[j]
                p = c.paragraphs[0]
                p.paragraph_format.space_after = Pt(1)
                agregar_inline(p, texto, tam=9.5, negrita_base=(i == 0))
                if i == 0:
                    sombrear(c, 'D9E2F3')
                elif i % 2 == 0:
                    sombrear(c, 'F7F9FC')
                if texto in ('✓', '') and i > 0 and j > 0 and ncol >= 4:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def imagen(self, ruta, pie):
        archivo = DOCS / ruta
        if not archivo.exists():
            return
        self.doc.add_picture(str(archivo), width=Cm(15.5))
        self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if pie:
            p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(pie); r.italic = True; r.font.size = Pt(9); r.font.color.rgb = GRIS_TEXTO

    def convertir(self, markdown, desplazamiento=0, saltar_h1=False):
        """Convierte el texto Markdown. ``desplazamiento`` suma niveles a los encabezados."""
        lineas = markdown.splitlines()
        i = 0
        while i < len(lineas):
            linea = lineas[i]
            s = linea.strip()

            if s.startswith('```'):
                j = i + 1
                bloque = []
                while j < len(lineas) and not lineas[j].strip().startswith('```'):
                    bloque.append(lineas[j]); j += 1
                self.codigo(bloque); i = j + 1; continue

            if not s:
                i += 1; continue

            m = re.match(r'^(#{1,6})\s+(.*)$', s)
            if m:
                nivel = len(m.group(1))
                if not (nivel == 1 and saltar_h1):
                    self.encabezado(min(nivel + desplazamiento, 6), m.group(2))
                i += 1; continue

            if s in ('---', '***'):
                i += 1; continue

            m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', s)
            if m:
                self.imagen(m.group(2), m.group(1)); i += 1; continue

            if s.startswith('>'):
                bloque = []
                while i < len(lineas) and lineas[i].strip().startswith('>'):
                    bloque.append(lineas[i].strip()[1:]); i += 1
                self.cita(bloque); continue

            if s.startswith('|'):
                bloque = []
                while i < len(lineas) and lineas[i].strip().startswith('|'):
                    bloque.append(lineas[i]); i += 1
                self.tabla(bloque); continue

            if re.match(r'^(\s*)([-*]|\d+[.)])\s+', linea):
                items = []
                while i < len(lineas):
                    m = re.match(r'^(\s*)([-*]|\d+[.)])\s+(.*)$', lineas[i])
                    if m:
                        nivel = len(m.group(1).replace('\t', '    ')) // 2
                        nivel = 0 if nivel == 0 else (1 if nivel <= 2 else 2)
                        items.append([nivel, m.group(2)[0].isdigit(), m.group(3)])
                        i += 1
                    elif lineas[i].strip() and lineas[i].startswith('  ') and items and not lineas[i].strip().startswith(('|', '```', '#')):
                        items[-1][2] += ' ' + lineas[i].strip(); i += 1   # continuación del ítem
                    else:
                        break
                self.lista(items); continue

            # Párrafo: juntar líneas consecutivas
            bloque = [s]
            i += 1
            while i < len(lineas) and lineas[i].strip() and not re.match(r'^(\s*([-*]|\d+[.)])\s+|#{1,6}\s|\||>|```|---)', lineas[i]):
                bloque.append(lineas[i].strip()); i += 1
            self.parrafo(' '.join(bloque))


# ---------------------------------------------------------------------------
# Estilos, portada, encabezado/pie
# ---------------------------------------------------------------------------

def configurar_estilos(doc):
    normal = doc.styles['Normal']
    normal.font.name = FUENTE; normal.font.size = Pt(10.5)
    normal._element.rPr.rFonts.set(qn('w:eastAsia'), FUENTE)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08
    for nombre, tam, antes in (('Heading 1', 20, 18), ('Heading 2', 15, 14), ('Heading 3', 12.5, 10), ('Heading 4', 11, 8)):
        st = doc.styles[nombre]
        st.font.name = FUENTE; st.font.size = Pt(tam); st.font.bold = True; st.font.color.rgb = AZUL
        st._element.rPr.rFonts.set(qn('w:eastAsia'), FUENTE)
        st.paragraph_format.space_before = Pt(antes); st.paragraph_format.space_after = Pt(4)
        st.paragraph_format.keep_with_next = True
    for nombre in ('List Bullet', 'List Bullet 2', 'List Bullet 3', 'List Number', 'List Number 2', 'List Number 3'):
        doc.styles[nombre].paragraph_format.space_after = Pt(2)


def configurar_pagina(doc, titulo):
    seccion = doc.sections[0]
    seccion.page_width = Cm(21.0); seccion.page_height = Cm(29.7)  # A4
    seccion.left_margin = seccion.right_margin = Cm(2.2)
    seccion.top_margin = Cm(2.0); seccion.bottom_margin = Cm(1.8)
    seccion.different_first_page_header_footer = True
    enc = seccion.header.paragraphs[0]
    enc.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = enc.add_run(titulo); r.font.size = Pt(8.5); r.font.color.rgb = GRIS_TEXTO
    pie = seccion.footer.paragraphs[0]
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = pie.add_run('MANAUDI S.A. · Página '); r.font.size = Pt(8.5); r.font.color.rgb = GRIS_TEXTO
    campo(pie, 'PAGE', '1')
    for run in pie.runs:
        run.font.size = Pt(8.5); run.font.color.rgb = GRIS_TEXTO


def portada(doc, fecha):
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('MANAUDI S.A.'); r.font.size = Pt(14); r.font.color.rgb = GRIS_TEXTO; r.bold = True
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Sistema de Inventarios'); r.font.size = Pt(34); r.bold = True; r.font.color.rgb = AZUL
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Documentación del sistema'); r.font.size = Pt(18); r.font.color.rgb = AZUL
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Manual de usuario · Manual técnico · Guion de demostración'); r.font.size = Pt(12); r.font.color.rgb = GRIS_TEXTO
    for _ in range(10):
        doc.add_paragraph()
    for texto in (f'Versión 1.0 · {fecha}', 'Django 4.2 LTS · MySQL 8 · Docker', 'Entrega formal del proyecto'):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(texto); r.font.size = Pt(11); r.font.color.rgb = GRIS_TEXTO
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def tabla_contenido(doc):
    h = doc.add_heading('Contenido', level=1)
    p = doc.add_paragraph()
    campo(p, 'TOC \\o "1-3" \\h \\z \\u', 'Pulse F9 (o acepte actualizar campos al abrir) para generar la tabla de contenido.')


def parte(doc, numero, titulo, descripcion):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(f'PARTE {numero}'); r.font.size = Pt(12); r.font.color.rgb = GRIS_TEXTO; r.bold = True
    h = doc.add_heading(titulo, level=1)
    p = doc.add_paragraph(); r = p.add_run(descripcion); r.italic = True; r.font.color.rgb = GRIS_TEXTO


# ---------------------------------------------------------------------------
# Ensamblado
# ---------------------------------------------------------------------------

def leer(nombre):
    return (RAIZ / nombre).read_text(encoding='utf-8')


def seccion_markdown(texto, titulo):
    """Devuelve el bloque de un ``## titulo`` (hasta el siguiente ``## ``)."""
    m = re.search(rf'^## {re.escape(titulo)}\s*$(.*?)(?=^## |\Z)', texto, re.M | re.S)
    return m.group(1) if m else ''


def main():
    fecha = date.today().strftime('%d/%m/%Y')
    doc = Document()
    configurar_estilos(doc)
    configurar_pagina(doc, 'Sistema de Inventarios Manaudi — Documentación')
    portada(doc, fecha)
    tabla_contenido(doc)
    conv = Conversor(doc)

    # Parte I: visión general e instalación (del README, sin la tabla de documentos)
    readme = leer('README.md')
    intro = readme.split('## Documentación')[0].split('\n', 1)[1]
    parte(doc, 'I', 'Visión general e instalación', 'Qué es el sistema, cómo se ejecuta y con qué datos de prueba cuenta.')
    conv.convertir(intro, desplazamiento=1)
    for titulo in ('Puesta en marcha (desarrollo)', 'Datos de prueba', 'Comandos útiles', 'Estructura del repositorio', 'Roles y permisos (resumen)', 'Producción'):
        conv.encabezado(2, titulo)
        conv.convertir(seccion_markdown(readme, titulo), desplazamiento=1)

    # Parte II: manual de usuario
    parte(doc, 'II', 'Manual de usuario', 'Descripción de cada pantalla y de las tareas de cada rol.')
    conv.convertir(leer('docs/manual_usuario.md').split('\n', 1)[1].split('---', 1)[1], desplazamiento=0, saltar_h1=True)

    # Parte III: manual técnico
    parte(doc, 'III', 'Manual técnico', 'Arquitectura, modelo de datos, reglas de negocio, configuración, despliegue y mantenimiento.')
    conv.convertir(leer('docs/manual_tecnico.md').split('\n', 1)[1].split('---', 1)[1], desplazamiento=0, saltar_h1=True)

    # Anexo: guion de demostración
    parte(doc, 'IV', 'Anexo: guion de demostración', 'Recorrido guiado con los datos de demostración, pensado para el video y la capacitación.')
    conv.convertir(leer('docs/guion_demo.md').split('\n', 1)[1], desplazamiento=0, saltar_h1=True)

    doc.core_properties.title = 'Sistema de Inventarios Manaudi — Documentación'
    doc.core_properties.author = 'MANAUDI S.A.'
    doc.core_properties.subject = 'Manual de usuario, manual técnico y guion de demostración'
    doc.save(SALIDA)
    print(f'Generado: {SALIDA}')


if __name__ == '__main__':
    sys.exit(main())
