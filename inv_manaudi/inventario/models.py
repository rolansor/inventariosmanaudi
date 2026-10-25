"""
Modelos de la app ``inventario``: stock por sucursal, movimientos y traslados.

- ``Inventario``: saldo actual de un producto en una sucursal (una fila por par).
- ``MovimientoInventario``: cada entrada o salida. Al crearse actualiza el saldo del
  ``Inventario`` correspondiente dentro de una transacción con bloqueo de fila.
- ``Traslado``: envío de un producto entre dos sucursales de la misma empresa. Genera
  un movimiento de salida al crearse y uno de entrada al confirmarse la recepción.

Integridad: el saldo nunca se edita a mano desde la aplicación; solo cambia a través
de movimientos. La única excepción es la carga masiva (``reportes.views``), que fija
un inventario inicial directamente.
"""
from django.db import models, transaction
from django.conf import settings
from productos.models import Producto
from usuarios.models import Empresa, Sucursal


class Inventario(models.Model):
    """
    Saldo de un producto en una sucursal.

    ``stock_minimo`` dispara las alertas de "stock bajo" del dashboard y del reporte
    de inventario valorizado. ``ultima_actualizacion`` se refresca en cada movimiento.
    """
    sucursal = models.ForeignKey(Sucursal, related_name='inventarios', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='inventarios', on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)  # Umbral de alerta de stock bajo
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sucursal', 'producto')

    def __str__(self):
        return f'{self.producto.nombre} - {self.sucursal.nombre} - {self.cantidad} {self.producto.get_tipo_producto_display()}'

    def is_stock_bajo(self):
        """True si el saldo actual está por debajo del stock mínimo configurado."""
        return self.cantidad < self.stock_minimo

    def valor_inventario(self):
        """Valor monetario del saldo (cantidad × precio actual del producto)."""
        return self.cantidad * self.producto.precio


class MovimientoInventario(models.Model):
    """
    Entrada o salida de stock de un producto en una sucursal.

    Al **crear** un movimiento, ``save()`` ajusta el saldo de ``Inventario``:
    suma en las entradas y resta en las salidas. Si una salida supera el saldo
    disponible se lanza ``ValueError('Stock insuficiente...')`` y no se guarda nada.

    Al **editar** un movimiento existente (p. ej. desde el admin de Django) el saldo
    NO se recalcula; por eso la aplicación no ofrece edición de movimientos.

    Los movimientos generados por traslados se reconocen porque el ``Traslado`` los
    referencia en ``movimiento_salida`` / ``movimiento_entrada`` (relaciones inversas
    ``traslado_salida`` y ``traslado_entrada``).
    """
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    TIPO_DOCUMENTO_CHOICES = [
        ('nota_venta', 'Nota de Venta'),
        ('factura', 'Factura'),
        ('orden_trabajo', 'Orden de Trabajo'),
        ('nota_pedido', 'Nota de Pedido'),
        ('otros', 'Otros'),
    ]

    sucursal = models.ForeignKey(Sucursal, related_name='movimientos', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='movimientos', on_delete=models.CASCADE)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)
    documento_respaldo = models.TextField(blank=True, null=True)  # Número del documento físico
    documento_soporte = models.FileField(upload_to='documento_soporte/', blank=True, null=True)  # Adjunto opcional, máx. 5 MB
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.tipo_movimiento.capitalize()} de {self.cantidad} {self.producto.nombre} en {self.sucursal.nombre}'

    def save(self, *args, **kwargs):
        """
        Guarda el movimiento y, si es nuevo, actualiza el saldo del inventario.

        Se hace en una sola transacción con ``select_for_update()`` sobre la fila de
        ``Inventario`` para que dos movimientos simultáneos sobre el mismo
        producto/sucursal no se pisen.

        :raises ValueError: si es una salida y el stock disponible no alcanza.
        """
        if self.pk is not None:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            inventario, _ = Inventario.objects.select_for_update().get_or_create(
                sucursal=self.sucursal, producto=self.producto
            )

            if self.tipo_movimiento == 'entrada':
                inventario.cantidad += self.cantidad
            elif self.tipo_movimiento == 'salida':
                if inventario.cantidad >= self.cantidad:
                    inventario.cantidad -= self.cantidad
                else:
                    raise ValueError('Stock insuficiente para la salida solicitada.')
            inventario.save()
            super().save(*args, **kwargs)


class Traslado(models.Model):
    """
    Envío de un producto desde una sucursal a otra de la misma empresa.

    Ciclo de vida:

    1. ``pendiente``: al crearse, ``save()`` genera el movimiento de **salida** en la
       sucursal de origen por ``cantidad_entregada`` (la mercadería "está en tránsito").
    2. ``confirmado``: ``confirmar()`` genera el movimiento de **entrada** en la sucursal
       de destino por ``cantidad_recibida``, que puede diferir de la entregada (faltantes
       o sobrantes). La diferencia se muestra en "Movimientos por producto".

    Quién confirma: un usuario con sucursal solo confirma los traslados destinados a
    su sucursal; un usuario sin sucursal puede confirmar cualquiera de su empresa.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
    ]

    TIPO_DOCUMENTO_CHOICES = [
        ('guia_remision', 'Guia de Remision'),
        ('guia_servientrega', 'Guia Servientrega'),
        ('orden_trabajo', 'Orden de Trabajo'),
        ('otros', 'Otros'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    sucursal_origen = models.ForeignKey(Sucursal, related_name='transferencias_salida', on_delete=models.CASCADE)
    sucursal_destino = models.ForeignKey(Sucursal, related_name='transferencias_entrada', on_delete=models.CASCADE)
    cantidad_entregada = models.IntegerField()
    cantidad_recibida = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES)
    documento_respaldo = models.TextField(blank=True, null=True)
    documento_soporte = models.FileField(upload_to='documento_soporte/', blank=True, null=True)
    movimiento_salida = models.ForeignKey(MovimientoInventario, related_name='traslado_salida', on_delete=models.SET_NULL, null=True, blank=True)
    movimiento_entrada = models.ForeignKey(MovimientoInventario, related_name='traslado_entrada', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return (f'Traslado de {self.cantidad_entregada} {self.producto.codigo}: '
                f'{self.sucursal_origen.nombre} -> {self.sucursal_destino.nombre} ({self.estado})')

    def save(self, *args, **kwargs):
        """
        Guarda el traslado. Si es nuevo, crea antes el movimiento de salida en origen.

        Ambas escrituras van en la misma transacción: si falla el guardado del traslado
        el stock no queda descontado sin respaldo.

        :raises ValueError: si origen y destino son la misma sucursal o si el origen
            no tiene stock suficiente (propagado desde ``MovimientoInventario``).
        """
        if self.sucursal_origen == self.sucursal_destino:
            raise ValueError('La sucursal de origen y destino no pueden ser las mismas.')

        if self.pk:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            try:
                movimiento_salida = MovimientoInventario.objects.create(
                    sucursal=self.sucursal_origen,
                    producto=self.producto,
                    tipo_movimiento='salida',
                    cantidad=self.cantidad_entregada,
                    comentario=f'Transferencia a {self.sucursal_destino.nombre}',
                    tipo_documento=self.tipo_documento,
                    documento_soporte=self.documento_soporte,
                    documento_respaldo=self.documento_respaldo,
                    usuario=self.usuario
                )
            except ValueError as e:
                raise ValueError(f'Error al crear movimiento de salida: {e}')
            self.movimiento_salida = movimiento_salida
            super().save(*args, **kwargs)

    def confirmar(self):
        """
        Registra la recepción: crea el movimiento de entrada en destino y marca
        el traslado como confirmado. Requiere ``cantidad_recibida`` > 0 ya asignada.

        :raises ValueError: si el traslado no está pendiente o no hay cantidad recibida.
        """
        if self.estado != 'pendiente':
            raise ValueError('Esta transferencia ya ha sido confirmada.')

        if self.cantidad_recibida is None or self.cantidad_recibida == 0:
            raise ValueError('Debe ingresar una cantidad recibida antes de confirmar la transferencia.')

        with transaction.atomic():
            try:
                movimiento_entrada = MovimientoInventario.objects.create(
                    sucursal=self.sucursal_destino,
                    producto=self.producto,
                    tipo_movimiento='entrada',
                    cantidad=self.cantidad_recibida,
                    comentario=f'Transferencia desde {self.sucursal_origen.nombre}',
                    tipo_documento=self.tipo_documento,
                    documento_soporte=self.documento_soporte,
                    documento_respaldo=self.documento_respaldo,
                    usuario=self.usuario
                )
            except ValueError as e:
                raise ValueError(f'Error al crear movimiento de entrada: {e}')
            self.movimiento_entrada = movimiento_entrada
            self.estado = 'confirmado'
            self.save()
