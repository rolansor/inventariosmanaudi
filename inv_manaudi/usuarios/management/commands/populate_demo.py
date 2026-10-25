"""
Comando ``populate_demo``: historial de operación realista para demostraciones.

    docker compose exec web python manage.py populate_demo
    docker compose exec web python manage.py populate_demo --force   # agrega otra tanda

Requiere haber corrido antes ``populate_data`` (usa sus empresas, sucursales,
usuarios y productos; **no crea ni modifica usuarios**). Para cada empresa:

- Completa ``codigo_auxiliar`` y ``codigo_ean`` en algunos productos y desactiva uno.
- Genera ~30 días de movimientos (entradas por factura/nota de pedido, salidas por
  nota de venta/orden de trabajo) repartidos entre sucursales y usuarios, más varios
  movimientos de **hoy** para que el "Reporte de Movimientos del Día" tenga datos.
- Crea traslados confirmados (uno con faltante: recibido < entregado) y traslados
  pendientes hacia la sucursal del encargado, listos para el "Acuse Recibo".
- Deja productos con stock bajo y un producto agotado en una sucursal.

Todos los documentos de respaldo generados empiezan con ``DEMO-``; el comando se
niega a correr de nuevo si ya existen, salvo con ``--force``.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from usuarios.models import Usuario, Empresa
from productos.models import Producto
from inventario.models import Inventario, MovimientoInventario, Traslado

PREFIJO = 'DEMO-'

COMENTARIOS_ENTRADA = ['COMPRA PRODUCTOS', 'REPOSICIÓN DE STOCK', 'DEVOLUCIÓN DE PRODUCTO', 'INVENTARIO INICIAL']
COMENTARIOS_SALIDA = ['VENTA AL CLIENTE', 'PEDIDO ESPECIAL', 'AJUSTE POR PÉRDIDA', 'PRODUCTO DEFECTUOSO']


class Command(BaseCommand):
    help = 'Genera movimientos, traslados y alertas de stock de demostración (requiere populate_data)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Generar aunque ya existan datos de demostración')
        parser.add_argument('--seed', type=int, default=2026,
                            help='Semilla aleatoria para obtener siempre los mismos datos')

    def handle(self, *args, **options):
        random.seed(options['seed'])

        if not Empresa.objects.exists():
            raise CommandError('No hay empresas. Ejecute primero: python manage.py populate_data')

        if MovimientoInventario.objects.filter(documento_respaldo__startswith=PREFIJO).exists() and not options['force']:
            raise CommandError('Ya existen datos de demostración (documentos DEMO-*). Use --force para agregar más.')

        self.stdout.write(self.style.WARNING('Generando datos de demostración...'))
        for empresa in Empresa.objects.order_by('id'):
            with transaction.atomic():
                self.poblar_empresa(empresa)

        self.stdout.write(self.style.SUCCESS('\n[OK] Datos de demostración generados.'))
        self.stdout.write(f'  - Movimientos totales: {MovimientoInventario.objects.count()}')
        self.stdout.write(f'  - Traslados: {Traslado.objects.count()} '
                          f'(pendientes: {Traslado.objects.filter(estado="pendiente").count()})')
        self.stdout.write(f'  - Productos inactivos: {Producto.objects.filter(estado="inactivo").count()}')

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _usuarios(self, empresa):
        """Usuarios operativos de la empresa: supervisor, encargado y manaudi (si existen)."""
        base = Usuario.objects.filter(perfil__empresa=empresa, is_superuser=False)
        return {
            'supervisor': base.filter(groups__name='Supervisor').exclude(groups__name='Manaudi').first(),
            'encargado': base.filter(groups__name='Encargado').exclude(groups__name='Supervisor').first(),
            'manaudi': base.filter(groups__name='Manaudi').first(),
        }

    @staticmethod
    def _fechar(objeto, dias_atras, hora=None):
        """Retrocede la fecha de un movimiento o traslado (los campos son auto_now_add)."""
        fecha = timezone.now() - timedelta(days=dias_atras)
        if hora is not None:
            fecha = fecha.replace(hour=hora, minute=random.randint(0, 59), second=random.randint(0, 59))
        campo = 'fecha' if isinstance(objeto, MovimientoInventario) else 'fecha_creacion'
        type(objeto).objects.filter(pk=objeto.pk).update(**{campo: fecha})

    def _movimiento(self, producto, sucursal, tipo, cantidad, usuario, dias_atras, numero):
        """Crea un movimiento (actualiza stock vía el modelo) y lo fecha hacia atrás."""
        if tipo == 'entrada':
            tipo_doc = random.choice(['factura', 'nota_pedido'])
            comentario = random.choice(COMENTARIOS_ENTRADA)
        else:
            tipo_doc = random.choice(['nota_venta', 'orden_trabajo'])
            comentario = random.choice(COMENTARIOS_SALIDA)
        mov = MovimientoInventario.objects.create(
            producto=producto, sucursal=sucursal, tipo_movimiento=tipo, cantidad=cantidad,
            tipo_documento=tipo_doc, documento_respaldo=f'{PREFIJO}{tipo_doc[:3].upper()}-{numero:05d}',
            comentario=comentario, usuario=usuario,
        )
        self._fechar(mov, dias_atras, hora=random.randint(8, 18) if dias_atras else None)
        return mov

    # ------------------------------------------------------------------
    # Generación por empresa
    # ------------------------------------------------------------------

    def poblar_empresa(self, empresa):
        """Genera el historial, los traslados y las alertas de una empresa (ver docstring del módulo)."""
        sucursales = list(empresa.sucursales.order_by('id'))
        productos = list(Producto.objects.filter(empresa=empresa, estado='activo').order_by('id'))
        if len(sucursales) < 2 or len(productos) < 4:
            self.stdout.write(self.style.WARNING(f'  [SKIP] {empresa.nombre}: faltan sucursales o productos'))
            return

        usuarios = self._usuarios(empresa)
        operadores = [u for u in (usuarios['supervisor'], usuarios['encargado'], usuarios['manaudi']) if u]
        if not operadores:
            self.stdout.write(self.style.WARNING(f'  [SKIP] {empresa.nombre}: no tiene usuarios operativos'))
            return

        numero = random.randint(1000, 9000)
        prefijo_ean = str(random.randint(100, 999))

        # 1) Códigos auxiliares / EAN en la mitad de los productos; uno inactivo
        for i, producto in enumerate(productos):
            if i % 2 == 0:
                producto.codigo_auxiliar = f'AUX-{producto.codigo[-6:]}'
                producto.codigo_ean = f'786{prefijo_ean}{producto.pk:07d}'[:13]
                producto.save()
        inactivo = productos[-1]
        inactivo.estado = 'inactivo'
        inactivo.save()
        productos = productos[:-1]

        # 2) Historial de 30 días: entradas y salidas en todas las sucursales
        for dias_atras in range(30, 0, -1):
            for _ in range(random.randint(1, 3)):
                producto = random.choice(productos)
                sucursal = random.choice(sucursales)
                usuario = self._usuario_para(sucursal, usuarios, operadores)
                inventario = Inventario.objects.filter(producto=producto, sucursal=sucursal).first()
                saldo = inventario.cantidad if inventario else 0
                if saldo > 5 and random.random() < 0.55:
                    cantidad = random.randint(1, min(8, saldo - 1))
                    numero += 1
                    self._movimiento(producto, sucursal, 'salida', cantidad, usuario, dias_atras, numero)
                else:
                    numero += 1
                    self._movimiento(producto, sucursal, 'entrada', random.randint(5, 40), usuario, dias_atras, numero)

        # 3) Traslados: bodega (primera sucursal) -> demás sucursales
        origen = sucursales[0]
        destino_encargado = sucursales[1]
        supervisor = usuarios['supervisor'] or operadores[0]

        for idx, (producto, destino, dias_atras, recibido) in enumerate([
            (productos[0], destino_encargado, 20, None),      # confirmado completo
            (productos[1], sucursales[-1], 15, 'faltante'),   # confirmado con faltante
            (productos[2], destino_encargado, 9, None),       # confirmado completo
        ]):
            cantidad = self._asegurar_stock(producto, origen, supervisor, minimo=6, dias_atras=dias_atras + 1, numero=numero)
            numero += 1
            traslado = Traslado.objects.create(
                producto=producto, sucursal_origen=origen, sucursal_destino=destino,
                cantidad_entregada=cantidad, tipo_documento='guia_remision',
                documento_respaldo=f'{PREFIJO}GR-{numero:05d}', usuario=supervisor,
            )
            self._fechar(traslado, dias_atras, hora=10)
            self._fechar(traslado.movimiento_salida, dias_atras, hora=10)
            traslado.cantidad_recibida = cantidad - 1 if recibido == 'faltante' else cantidad
            traslado.usuario = usuarios['encargado'] or supervisor
            traslado.confirmar()
            self._fechar(traslado.movimiento_entrada, max(dias_atras - 1, 0), hora=16)

        # Pendientes (en tránsito): dos hacia la sucursal del encargado, uno hacia otra
        pendientes = [(productos[3], destino_encargado, 2), (productos[4 % len(productos)], destino_encargado, 1)]
        if len(sucursales) > 2:
            pendientes.append((productos[5 % len(productos)], sucursales[2], 1))
        for producto, destino, dias_atras in pendientes:
            cantidad = self._asegurar_stock(producto, origen, supervisor, minimo=4, dias_atras=dias_atras + 1, numero=numero)
            numero += 1
            traslado = Traslado.objects.create(
                producto=producto, sucursal_origen=origen, sucursal_destino=destino,
                cantidad_entregada=cantidad, tipo_documento=random.choice(['guia_remision', 'guia_servientrega']),
                documento_respaldo=f'{PREFIJO}GR-{numero:05d}', usuario=supervisor,
            )
            self._fechar(traslado, dias_atras, hora=11)
            self._fechar(traslado.movimiento_salida, dias_atras, hora=11)

        # 4) Alertas: stock bajo (mínimo por encima del saldo) y un producto agotado
        for producto in productos[:2]:
            inv = Inventario.objects.filter(producto=producto, sucursal=destino_encargado).first()
            if inv:
                inv.stock_minimo = inv.cantidad + random.randint(5, 15)
                inv.save()
        agotado = Inventario.objects.filter(producto=productos[-1], sucursal=sucursales[-1], cantidad__gt=0).first()
        if agotado:
            numero += 1
            self._movimiento(agotado.producto, agotado.sucursal, 'salida', agotado.cantidad,
                             self._usuario_para(agotado.sucursal, usuarios, operadores), 1, numero)

        # 5) Movimientos de hoy (para el reporte diario)
        for _ in range(5):
            producto = random.choice(productos)
            sucursal = random.choice(sucursales)
            usuario = self._usuario_para(sucursal, usuarios, operadores)
            inv = Inventario.objects.filter(producto=producto, sucursal=sucursal).first()
            numero += 1
            if inv and inv.cantidad > 3 and random.random() < 0.5:
                self._movimiento(producto, sucursal, 'salida', random.randint(1, 3), usuario, 0, numero)
            else:
                self._movimiento(producto, sucursal, 'entrada', random.randint(5, 20), usuario, 0, numero)

        self.stdout.write(self.style.SUCCESS(f'  [OK] {empresa.nombre}: historial, traslados y alertas creados'))

    @staticmethod
    def _usuario_para(sucursal, usuarios, operadores):
        """Elige al usuario cuya sucursal coincide; si no hay, uno sin sucursal (manaudi)."""
        for clave in ('supervisor', 'encargado'):
            u = usuarios[clave]
            if u and u.perfil.sucursal_id == sucursal.id:
                return u
        return usuarios['manaudi'] or random.choice(operadores)

    def _asegurar_stock(self, producto, sucursal, usuario, minimo, dias_atras, numero):
        """Garantiza saldo suficiente en la sucursal (crea una entrada si hace falta) y devuelve la cantidad a trasladar."""
        inv, _ = Inventario.objects.get_or_create(producto=producto, sucursal=sucursal)
        if inv.cantidad < minimo:
            self._movimiento(producto, sucursal, 'entrada', minimo + 10, usuario, dias_atras, numero + 500)
            inv.refresh_from_db()
        return random.randint(minimo // 2, min(inv.cantidad, minimo + 4))
