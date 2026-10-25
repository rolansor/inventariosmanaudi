"""
Modelos de la app ``categorias``: clasificación jerárquica de productos.

    Categoria (por empresa) ──< Subcategoria ──< Clase ──< Producto

Los tres niveles comparten la misma forma: un ``codigo`` de exactamente 3 caracteres
alfanuméricos, único dentro de su padre, y un ``nombre``. Ambos se guardan siempre
en MAYÚSCULAS. Los productos apuntan únicamente a la ``Clase``; la categoría y la
subcategoría se obtienen navegando hacia arriba (``clase.subcategoria.categoria``).
"""
from django.db import models
from django.core.validators import RegexValidator
from usuarios.models import Empresa

CODIGO_3_CARACTERES = RegexValidator(
    r'^[A-Za-z0-9]{3}$',
    'El código debe ser exactamente 3 caracteres alfanuméricos',
)


class Categoria(models.Model):
    """Primer nivel de clasificación. El código es único por empresa (ej. ELE, OFI)."""
    codigo = models.CharField(
        max_length=3,
        validators=[CODIGO_3_CARACTERES],
        help_text='Código de 3 caracteres (letras y números)'
    )
    nombre = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias')

    class Meta:
        unique_together = ('codigo', 'empresa')
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'

    def save(self, *args, **kwargs):
        """Normaliza código y nombre a mayúsculas antes de guardar."""
        self.codigo = self.codigo.upper()
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)


class Subcategoria(models.Model):
    """Segundo nivel. El código es único dentro de su categoría (ej. ELE/COM, ELE/CEL)."""
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    codigo = models.CharField(
        max_length=3,
        validators=[CODIGO_3_CARACTERES],
        help_text='Código de 3 caracteres (letras y números)'
    )
    nombre = models.CharField(max_length=255)

    class Meta:
        unique_together = ('codigo', 'categoria')
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre} (Cat: {self.categoria.codigo})'

    def save(self, *args, **kwargs):
        """Normaliza código y nombre a mayúsculas antes de guardar."""
        self.codigo = self.codigo.upper()
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)


class Clase(models.Model):
    """
    Tercer nivel y el único al que se asocian los productos.

    El código es único dentro de su subcategoría (ej. ELE/COM/LAP). Al eliminar una
    clase, los productos que la usaban quedan "sin clasificación" (``clase = NULL``).
    """
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.CASCADE, related_name='clases')
    codigo = models.CharField(
        max_length=3,
        validators=[CODIGO_3_CARACTERES],
        help_text='Código de 3 caracteres (letras y números)'
    )
    nombre = models.CharField(max_length=255)

    class Meta:
        unique_together = ('codigo', 'subcategoria')
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre} (Subcat: {self.subcategoria.codigo})'

    def save(self, *args, **kwargs):
        """Normaliza código y nombre a mayúsculas antes de guardar."""
        self.codigo = self.codigo.upper()
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)
