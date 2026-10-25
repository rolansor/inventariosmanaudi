"""
Arma los videos ilustrativos del recorrido a partir de las capturas de ``docs/capturas``.

    pip install pillow imageio imageio-ffmpeg
    python docs/generar_videos.py

Genera en ``docs/videos``:

- ``escena_N_<nombre>.gif``: una presentación por escena (una captura cada ~3 s)
  con una franja de subtítulo que describe la pantalla.
- ``recorrido_completo.mp4``: todas las escenas seguidas, en formato de video.

Las escenas y los subtítulos están en ``ESCENAS``; para cambiar el orden o los textos
basta editar esa estructura y volver a ejecutar el script.
"""
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

DOCS = Path(__file__).resolve().parent
CAPTURAS = DOCS / 'capturas'
SALIDA = DOCS / 'videos'
ANCHO = 1280
SEGUNDOS_POR_CAPTURA = 3
FPS_VIDEO = 10

ESCENAS = [
    ('1_administracion', 'Escena 1 · Administración (usuario techcorp_manaudi)', [
        ('01_login', 'Pantalla de ingreso al sistema'),
        ('02_dashboard_manaudi', 'Dashboard: resumen de la empresa y últimos movimientos'),
        ('03_empresas', 'Manejo Empresas: alta, edición y acceso a sucursales'),
        ('04_sucursales_formulario', 'Sucursales: formulario con nombre, abreviatura y tipo'),
        ('05_sucursales_lista', 'Sucursal creada sin recargar la página'),
        ('06_categorias', 'Clasificación: categorías de la empresa'),
        ('07_subcategorias', 'Subcategorías de ELECTRÓNICA'),
        ('08_clases', 'Clases de COMPUTADORAS'),
        ('09_clases_modal_crear', 'Crear clase: código de 3 caracteres y nombre'),
        ('10_clases_creada', 'La clase MONITORES queda registrada'),
        ('11_carga_masiva', 'Carga masiva de productos desde Excel'),
        ('12_carga_masiva_instrucciones', 'Instrucciones y columnas de la plantilla'),
        ('13_busqueda_inactivo', 'Búsqueda: producto inactivo con botón Activar (solo Manaudi)'),
    ]),
    ('2_supervisor', 'Escena 2 · Supervisor de la bodega (usuario techcorp_supervisor)', [
        ('14_dashboard_supervisor', 'Dashboard filtrado por la sucursal Matriz Quito'),
        ('16_nuevo_producto_lleno', 'Nuevo producto: clasificación, códigos, modelo y precio'),
        ('17_lista_productos_supervisor', 'Lista de productos con exportación y botón editar'),
        ('18_movimiento_formulario', 'Entrada/Salida: la sucursal queda fija para el usuario'),
        ('19_movimiento_entrada', 'Entrada de 20 unidades por factura'),
        ('20_movimiento_registrado', 'Movimiento registrado y stock actualizado'),
        ('21_movimiento_stock_insuficiente', 'Una salida mayor al stock se rechaza'),
        ('22_traslado_formulario', 'Traslado: origen, destino, producto y guía de remisión'),
        ('23_traslados_pendientes_supervisor', 'El traslado queda pendiente (en tránsito)'),
        ('24_traslados_recientes', 'Historial de traslados recientes'),
        ('25_movimientos_producto', 'Kardex por producto: entradas, salidas y traslados'),
        ('26_movimientos_empresa', 'Movimientos de toda la empresa'),
        ('27_movimientos_sucursal', 'Movimientos de una sucursal'),
    ]),
    ('3_encargado', 'Escena 3 · Encargado de sucursal (usuario techcorp_encargado)', [
        ('28_dashboard_encargado', 'Dashboard de Sucursal Guayaquil con menú reducido'),
        ('29_acceso_denegado', 'Una URL sin permiso muestra Acceso Denegado'),
        ('30_acuse_recibo', 'Acuse Recibo: traslados dirigidos a su sucursal'),
        ('31_confirmar_recepcion', 'Confirmar recepción indicando la cantidad recibida'),
        ('32_acuse_recibo_confirmado', 'Recepción confirmada: entra el stock en destino'),
        ('33_salida_encargado', 'Salida por nota de venta en su sucursal'),
        ('34_salida_registrada', 'Salida registrada'),
        ('35_busqueda_encargado', 'Búsqueda de productos sin botones de edición'),
        ('36_kardex_tablet', 'Kardex del producto nuevo: stock total 19'),
        ('37_kardex_traslados', 'Pestaña de traslados: enviado vs. recibido'),
    ]),
    ('4_auditor', 'Escena 4 · Auditoría (usuario techcorp_auditor)', [
        ('38_dashboard_auditor', 'Solo lectura: Productos y Reportes'),
        ('39_reporte_diario', 'Reporte de movimientos del día'),
        ('40_reporte_diario_usuarios', 'Resumen por usuario'),
        ('41_valorizado_detalle', 'Inventario valorizado: detalle por producto y sucursal'),
        ('42_valorizado_sucursal', 'Totales por sucursal'),
        ('45_valorizado_categoria', 'Totales por categoría'),
        ('43_valorizado_top', 'Top 10 de productos por valor'),
        ('44_valorizado_alertas', 'Alertas de stock bajo y agotado'),
        ('52_lista_productos_auditor', 'Lista de productos sin acciones de edición'),
    ]),
    ('5_superusuario', 'Escena 5 · Superusuario y administración (usuario admin)', [
        ('46_selector_empresa', 'Selector de empresa en la barra superior'),
        ('47_dashboard_comercial_andina', 'La misma pantalla con otra empresa activa'),
        ('48_admin_inicio', 'Administrador de Django'),
        ('49_admin_nuevo_usuario', 'Alta de usuario'),
        ('50_admin_perfiles', 'Perfiles: empresa y sucursal de cada usuario'),
        ('51_admin_grupo', 'Grupo Encargado con su lista de usuarios'),
    ]),
]


def fuente(tamano):
    for nombre in ('segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def cuadro(ruta, subtitulo, titulo_escena):
    """Captura escalada a ANCHO con una franja superior (escena) e inferior (subtítulo)."""
    img = Image.open(ruta).convert('RGB')
    img = img.resize((ANCHO, round(img.height * ANCHO / img.width)))
    franja_sup, franja_inf = 36, 54
    lienzo = Image.new('RGB', (ANCHO, img.height + franja_sup + franja_inf), (31, 58, 95))
    lienzo.paste(img, (0, franja_sup))
    d = ImageDraw.Draw(lienzo)
    d.text((16, 8), titulo_escena, fill='white', font=fuente(20))
    d.rectangle([0, lienzo.height - franja_inf, ANCHO, lienzo.height], fill=(20, 20, 20))
    d.text((16, lienzo.height - franja_inf + 14), subtitulo, fill='white', font=fuente(24))
    return lienzo


def portada(texto, alto):
    lienzo = Image.new('RGB', (ANCHO, alto), (31, 58, 95))
    d = ImageDraw.Draw(lienzo)
    f = fuente(44)
    w = d.textlength(texto, font=f)
    d.text(((ANCHO - w) / 2, alto / 2 - 40), texto, fill='white', font=f)
    f2 = fuente(24)
    sub = 'Sistema de Inventarios Manaudi'
    d.text(((ANCHO - d.textlength(sub, font=f2)) / 2, alto / 2 + 30), sub, fill=(200, 215, 235), font=f2)
    return lienzo


def main():
    SALIDA.mkdir(exist_ok=True)
    todos = []
    for clave, titulo, capturas in ESCENAS:
        cuadros = []
        for nombre, subtitulo in capturas:
            ruta = CAPTURAS / f'{nombre}.jpg'
            if not ruta.exists():
                print(f'  [aviso] falta {ruta.name}')
                continue
            cuadros.append(cuadro(ruta, subtitulo, titulo))
        if not cuadros:
            continue
        alto = cuadros[0].height
        cuadros = [c.resize((ANCHO, alto)) for c in cuadros]
        gif = SALIDA / f'escena_{clave}.gif'
        cuadros[0].save(gif, save_all=True, append_images=cuadros[1:], duration=SEGUNDOS_POR_CAPTURA * 1000, loop=0, optimize=True)
        print(f'GIF: {gif.name} ({len(cuadros)} capturas)')
        todos.append(portada(titulo, alto))
        todos.extend(cuadros)

    alto = min(c.height for c in todos)
    alto -= alto % 2  # ffmpeg exige dimensiones pares
    mp4 = SALIDA / 'recorrido_completo.mp4'
    with imageio.get_writer(mp4, fps=FPS_VIDEO, codec='libx264', quality=7, macro_block_size=None) as w:
        for c in todos:
            frame = c.resize((ANCHO, alto))
            for _ in range(SEGUNDOS_POR_CAPTURA * FPS_VIDEO):
                w.append_data(np.asarray(frame))
    print(f'MP4: {mp4.name} ({len(todos)} cuadros, {len(todos) * SEGUNDOS_POR_CAPTURA} s)')


if __name__ == '__main__':
    main()
