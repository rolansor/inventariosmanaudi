"""
Modelos de la app ``productos``: catálogo de artículos de cada empresa.

Un ``Producto`` pertenece a una ``Empresa`` y se clasifica mediante una ``Clase``
(Categoría / Subcategoría / Clase). El stock por sucursal no vive aquí sino en
``inventario.Inventario``.
"""
from django.db import models
from categorias.models import Clase
from usuarios.models import Empresa


class ProductoManager(models.Manager):
    """Manager con atajos de consulta para el catálogo."""

    def para_empresa(self, empresa):
        """Productos (activos e inactivos) de la empresa indicada."""
        return self.filter(empresa=empresa)


class Producto(models.Model):
    """
    Artículo del catálogo de una empresa.

    Reglas:
    - ``codigo`` es único dentro de la empresa (constraint ``unique_codigo_empresa``);
      el mismo código puede existir en otra empresa.
    - ``codigo``, ``codigo_auxiliar``, ``modelo``, ``nombre`` y ``descripcion`` se
      guardan en MAYÚSCULAS.
    - Los productos no se eliminan: se pasan a ``estado = 'inactivo'`` (solo Manaudi).
    - ``tipo_producto`` distingue unidades sueltas de juegos/kits; es informativo.
    """
    TIPO_PRODUCTO_CHOICES = [
        ('unidad', 'Unidad'),
        ('juego', 'Juego'),
    ]
    ESTADO_PRODUCTO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    codigo = models.CharField(max_length=50)  # Único por empresa (ver Meta.constraints)
    codigo_auxiliar = models.CharField(max_length=50, blank=True, null=True,
                                       help_text='Código auxiliar o alternativo del producto')
    codigo_ean = models.CharField(max_length=13, blank=True, null=True,
                                  help_text='Código EAN-13 (13 dígitos)')
    modelo = models.CharField(max_length=100, blank=True, null=True,
                              help_text='Modelo del producto')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_producto = models.CharField(max_length=10, choices=TIPO_PRODUCTO_CHOICES, default='unidad')
    clase = models.ForeignKey(Clase, related_name='productos', on_delete=models.SET_NULL, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PRODUCTO_CHOICES, default='activo')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='productos')

    objects = ProductoManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_empresa')
        ]

    def save(self, *args, **kwargs):
        """Normaliza a mayúsculas los códigos, el modelo, el nombre y la descripción."""
        if self.codigo:
            self.codigo = self.codigo.upper()
        if self.codigo_auxiliar:
            self.codigo_auxiliar = self.codigo_auxiliar.upper()
        if self.modelo:
            self.modelo = self.modelo.upper()
        if self.nombre:
            self.nombre = self.nombre.upper()
        if self.descripcion:
            self.descripcion = self.descripcion.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo} - {self.nombre} ({self.get_tipo_producto_display()})'
