from django.db import models


class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Sucursal(models.Model):
    empresa = models.ForeignKey(Empresa, related_name='sucursales', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    abreviatura = models.CharField(max_length=3)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f'{self.nombre} - {self.empresa.nombre}'


class Categoria(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre


class Subcategoria(models.Model):
    categoria = models.ForeignKey(Categoria, related_name='subcategorias', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.nombre} (Categoría: {self.categoria.nombre})'


class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = [
        ('unidad', 'Unidad'),
        ('juego', 'Juego'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_producto = models.CharField(max_length=10, choices=TIPO_PRODUCTO_CHOICES, default='unidad')
    categoria = models.ForeignKey(Subcategoria, related_name='productos', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.nombre} - {self.get_tipo_producto_display()}'


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


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('traslado', 'Traslado'),
    ]

    sucursal = models.ForeignKey(Sucursal, related_name='movimientos', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='movimientos', on_delete=models.CASCADE)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField()
    sucursal_destino = models.ForeignKey(Sucursal, related_name='movimientos_destino', on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.tipo_movimiento == 'traslado':
            return f'Traslado de {self.cantidad} {self.producto.get_tipo_producto_display()} de {self.sucursal.nombre} a {self.sucursal_destino.nombre}'
        return f'{self.tipo_movimiento.capitalize()} de {self.cantidad} {self.producto.get_tipo_producto_display()} - {self.producto.nombre}'

    def save(self, *args, **kwargs):
        inventario_origen, created = Inventario.objects.get_or_create(sucursal=self.sucursal, producto=self.producto)

        if self.tipo_movimiento == 'entrada':
            inventario_origen.cantidad += self.cantidad
        elif self.tipo_movimiento == 'salida' and inventario_origen.cantidad >= self.cantidad:
            inventario_origen.cantidad -= self.cantidad
        elif self.tipo_movimiento == 'traslado':
            if inventario_origen.cantidad >= self.cantidad:
                inventario_origen.cantidad -= self.cantidad  # Disminuir en la sucursal origen

                # Actualizar inventario de la sucursal de destino
                inventario_destino, created = Inventario.objects.get_or_create(sucursal=self.sucursal_destino, producto=self.producto)
                inventario_destino.cantidad += self.cantidad
                inventario_destino.save()
            else:
                raise ValueError('No hay suficiente stock en la sucursal de origen para este traslado.')
        else:
            raise ValueError('Movimiento inválido o sin stock suficiente.')

        inventario_origen.save()
        super(MovimientoInventario, self).save(*args, **kwargs)
