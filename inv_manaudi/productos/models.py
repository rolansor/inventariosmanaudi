from django.db import models
from categorias.models import Subcategoria
from usuarios.models import Empresa


class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = [
        ('unidad', 'Unidad'),
        ('juego', 'Juego'),
    ]
    ESTADO_PRODUCTO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_producto = models.CharField(max_length=10, choices=TIPO_PRODUCTO_CHOICES, default='unidad')
    categoria = models.ForeignKey(Subcategoria, related_name='productos', on_delete=models.SET_NULL, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PRODUCTO_CHOICES, default='activo')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='productos')

    def __str__(self):
        return f'{self.codigo} - {self.nombre} ({self.get_tipo_producto_display()})'
