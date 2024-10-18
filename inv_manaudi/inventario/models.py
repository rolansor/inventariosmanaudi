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
        ('traslado', 'Traslado'),
    ]

    ESTADO_RECEPCION_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
    ]

    sucursal = models.ForeignKey(Sucursal, related_name='movimientos', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='movimientos', on_delete=models.CASCADE)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField()
    sucursal_destino = models.ForeignKey(Sucursal, related_name='movimientos_destino', on_delete=models.SET_NULL, null=True, blank=True)
    cantidad_recibida = models.IntegerField(null=True, blank=True)  # Nuevo campo para registrar la cantidad recibida
    estado_recepcion = models.CharField(max_length=10, choices=ESTADO_RECEPCION_CHOICES, null=True, blank=True)  # Nuevo campo para el estado de recepción
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)
    documento_respaldo = models.TextField(blank=True, null=True)
    documento_traslado = models.FileField(upload_to='documentos_traslado/', blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        if self.tipo_movimiento == 'traslado':
            return f'Traslado de {self.cantidad} {self.producto.get_tipo_producto_display()} de {self.sucursal.nombre} a {self.sucursal_destino.nombre}'
        return f'{self.tipo_movimiento.capitalize()} de {self.cantidad} {self.producto.get_tipo_producto_display()} - {self.producto.nombre}'

    def confirmar_recepcion(self, cantidad_recibida):
        """Método para confirmar la recepción y actualizar el inventario de la sucursal destino."""
        if cantidad_recibida > self.cantidad:
            raise ValueError("La cantidad recibida no puede ser mayor que la cantidad enviada.")

        self.cantidad_recibida = cantidad_recibida
        self.estado_recepcion = 'confirmado'

        # Actualizar el inventario solo en la confirmación de recepción
        inventario_destino, created = Inventario.objects.get_or_create(sucursal=self.sucursal_destino,
                                                                       producto=self.producto)
        inventario_destino.cantidad += self.cantidad_recibida
        inventario_destino.save()
        self.save()

    def save(self, *args, **kwargs):
        # Verificar si ya existe un registro para evitar la sobreescritura en caso de una confirmación previa
        if self.pk is None or self.estado_recepcion == 'pendiente':  # Solo ejecutar si es un nuevo registro o traslado pendiente
            if self.tipo_movimiento == 'traslado':
                self.estado_recepcion = 'pendiente'
            else:
                self.estado_recepcion = None

            # Solo actualizamos el inventario de la sucursal de origen, no el de destino
            inventario_origen, created = Inventario.objects.get_or_create(sucursal=self.sucursal, producto=self.producto)

            if self.tipo_movimiento == 'entrada':
                inventario_origen.cantidad += self.cantidad
            elif self.tipo_movimiento == 'salida':
                if inventario_origen.cantidad >= self.cantidad:
                    inventario_origen.cantidad -= self.cantidad
                else:
                    raise ValueError('Stock insuficiente para la salida solicitada.')
            elif self.tipo_movimiento == 'traslado':
                # Solo restamos en la sucursal de origen
                if inventario_origen.cantidad >= self.cantidad:
                    inventario_origen.cantidad -= self.cantidad
                else:
                    raise ValueError('No hay suficiente stock en la sucursal de origen para este traslado.')
                # No sumamos en la sucursal destino hasta la confirmación

            inventario_origen.save()
        super(MovimientoInventario, self).save(*args, **kwargs)

