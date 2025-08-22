from django.db import models
from categorias.models import Clase
from usuarios.models import Empresa


class ProductoManager(models.Manager):
    def para_empresa(self, empresa):
        return self.filter(empresa=empresa)


class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = [
        ('unidad', 'Unidad'),
        ('juego', 'Juego'),
    ]
    ESTADO_PRODUCTO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    codigo = models.CharField(max_length=50)
    codigo_auxiliar = models.CharField(max_length=50, blank=True, null=True,
                                       help_text='Código auxiliar o alternativo del producto')
    codigo_ean = models.CharField(max_length=13, blank=True, null=True, 
                                  help_text='Código EAN-13 (13 dígitos)')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_producto = models.CharField(max_length=10, choices=TIPO_PRODUCTO_CHOICES, default='unidad')
    clase = models.ForeignKey(Clase, related_name='productos', on_delete=models.SET_NULL, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PRODUCTO_CHOICES, default='activo')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='productos')
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_empresa')
        ]
    objects = ProductoManager()

    def save(self, *args, **kwargs):
        # Convertir códigos y nombre a mayúsculas antes de guardar
        if self.codigo:
            self.codigo = self.codigo.upper()
        if self.codigo_auxiliar:
            self.codigo_auxiliar = self.codigo_auxiliar.upper()
        if self.nombre:
            self.nombre = self.nombre.upper()
        if self.descripcion:
            self.descripcion = self.descripcion.upper()
        super(Producto, self).save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.codigo} - {self.nombre} ({self.get_tipo_producto_display()})'
