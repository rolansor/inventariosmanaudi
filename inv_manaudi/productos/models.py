from django.db import models
from usuarios.models import Empresa


class ProductoManager(models.Manager):
    def para_empresa(self, empresa):
        return self.filter(empresa=empresa)


class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = [
        ('UNIDAD', 'Unidad'),
        ('GRUPO', 'Grupo'),
    ]
    ESTADO_PRODUCTO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    LINEA_CHOICES = [
        ('93', 'ACCESORIO'),
        ('90', 'MARCO ECONOMICO'),
        ('91', 'MARCO EXCLUSIVO'),
        ('92', 'MARCO GAMA ALTA'),
    ]
    
    SUBLINEA_CHOICES = [
        ('06', 'GAFA'),
        ('01', 'HOMBRE'),
        ('03', 'KID NINA'),
        ('04', 'KID NINO'),
        ('02', 'MUJER'),
        ('05', 'UNISEX'),
    ]
    
    CLASE_CHOICES = [
        ('05', 'AL AIRE'),
        ('01', 'BASICA'),
        ('04', 'CLIP'),
        ('02', 'INTERMEDIA'),
        ('03', 'PREMIUM'),
    ]
    
    MATERIAL_CHOICES = [
        ('PASTA', 'Pasta'),
        ('ACETATO', 'Acetato'),
        ('METAL', 'Metal'),
    ]

    codigo = models.CharField(max_length=50, editable=False)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_producto = models.CharField(max_length=10, choices=TIPO_PRODUCTO_CHOICES, default='UNIDAD')
    estado = models.CharField(max_length=20, choices=ESTADO_PRODUCTO_CHOICES, default='activo')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='productos')
    
    # Nuevos campos para óptica
    linea = models.CharField(max_length=2, choices=LINEA_CHOICES, blank=True, null=True)
    sublinea = models.CharField(max_length=2, choices=SUBLINEA_CHOICES, blank=True, null=True)
    clase = models.CharField(max_length=2, choices=CLASE_CHOICES, blank=True, null=True)
    material = models.CharField(max_length=10, choices=MATERIAL_CHOICES, blank=True, null=True)
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_empresa')
        ]
        indexes = [
            models.Index(fields=['modelo']),
        ]
    
    objects = ProductoManager()
    
    def save(self, *args, **kwargs):
        # Convertir marca y modelo a mayúsculas
        if self.marca:
            self.marca = self.marca.upper()
        if self.modelo:
            self.modelo = self.modelo.upper()
        
        # Generar código automático si hay línea, sublínea y clase
        if self.linea and self.sublinea and self.clase:
            self.codigo = f"{self.linea}{self.sublinea}{self.clase}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        if self.marca and self.modelo:
            return f'{self.codigo} - {self.marca} {self.modelo}'
        return f'{self.codigo} - {self.nombre} ({self.get_tipo_producto_display()})'
