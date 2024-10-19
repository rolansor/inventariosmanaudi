from django.db import models
from django.conf import settings
from productos.models import Producto
from usuarios.models import Empresa, Sucursal


class Inventario(models.Model):
    sucursal = models.ForeignKey(Sucursal, related_name='inventarios', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='inventarios', on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)  # Nuevo campo para el stock mínimo
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sucursal', 'producto')

    def __str__(self):
        return f'{self.producto.nombre} - {self.sucursal.nombre} - {self.cantidad} {self.producto.get_tipo_producto_display()}'

    def is_stock_bajo(self):
        """Verifica si el stock actual está por debajo del stock mínimo."""
        return self.cantidad < self.stock_minimo

    def valor_inventario(self):
        """Calcula el valor total de los productos en inventario."""
        return self.cantidad * self.producto.precio


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    sucursal = models.ForeignKey(Sucursal, related_name='movimientos', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='movimientos', on_delete=models.CASCADE)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)
    documento_respaldo = models.TextField(blank=True, null=True)
    documento_soporte = models.FileField(upload_to='documento_soporte/', blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.tipo_movimiento.capitalize()} de {self.cantidad} {self.producto.nombre} en {self.sucursal.nombre}'

    def save(self, *args, **kwargs):
        if self.pk is None:  # Solo ejecutar si es un nuevo registro
            inventario, created = Inventario.objects.get_or_create(sucursal=self.sucursal, producto=self.producto)

            if self.tipo_movimiento == 'entrada':
                inventario.cantidad += self.cantidad
            elif self.tipo_movimiento == 'salida':
                if inventario.cantidad >= self.cantidad:
                    inventario.cantidad -= self.cantidad
                else:
                    raise ValueError('Stock insuficiente para la salida solicitada.')
            inventario.save()
        super(MovimientoInventario, self).save(*args, **kwargs)


class Traslado(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    sucursal_origen = models.ForeignKey(Sucursal, related_name='transferencias_salida', on_delete=models.CASCADE)
    sucursal_destino = models.ForeignKey(Sucursal, related_name='transferencias_entrada', on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    documento_respaldo = models.TextField(blank=True, null=True)
    documento_soporte = models.FileField(upload_to='documento_soporte/', blank=True, null=True)
    movimiento_salida = models.ForeignKey(MovimientoInventario, related_name='transferencia_salida', on_delete=models.SET_NULL, null=True, blank=True)
    movimiento_entrada = models.ForeignKey(MovimientoInventario, related_name='transferencia_entrada', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Validar que la sucursal de origen y destino no sean las mismas
        if self.sucursal_origen == self.sucursal_destino:
            raise ValueError('La sucursal de origen y destino no pueden ser las mismas.')

        # Crear movimiento de salida al crear el traslado si es un nuevo registro
        if not self.pk:
            try:
                movimiento_salida = MovimientoInventario.objects.create(
                    sucursal=self.sucursal_origen,
                    producto=self.producto,
                    tipo_movimiento='salida',
                    cantidad=self.cantidad,
                    comentario=f'Transferencia a {self.sucursal_destino.nombre}',
                    documento_soporte=self.documento_soporte,
                    documento_respaldo=self.documento_respaldo,
                    usuario=self.usuario
                )
                self.movimiento_salida = movimiento_salida
            except ValueError as e:
                raise ValueError(f'Error al crear movimiento de salida: {e}')
        super(Traslado, self).save(*args, **kwargs)

    def confirmar(self):
        if self.estado != 'pendiente':
            raise ValueError('Esta transferencia ya ha sido confirmada.')

        # Verificar que no haya errores de stock en la sucursal destino
        try:
            movimiento_entrada = MovimientoInventario.objects.create(
                sucursal=self.sucursal_destino,
                producto=self.producto,
                tipo_movimiento='entrada',
                cantidad=self.cantidad,
                comentario=f'Transferencia desde {self.sucursal_origen.nombre}',
                documento_soporte=self.documento_soporte,
                documento_respaldo=self.documento_respaldo,
                usuario=self.usuario
            )
            self.movimiento_entrada = movimiento_entrada
            self.estado = 'confirmado'
            self.save()

        except ValueError as e:
            raise ValueError(f'Error al crear movimiento de entrada: {e}')
