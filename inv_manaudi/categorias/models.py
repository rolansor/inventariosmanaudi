from django.db import models
from django.core.validators import RegexValidator
from usuarios.models import Empresa


class Categoria(models.Model):
    codigo = models.CharField(
        max_length=3,
        validators=[RegexValidator(r'^[A-Za-z0-9]{3}$', 'El código debe ser exactamente 3 caracteres alfanuméricos')],
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
        # Convertir el código y nombre a mayúsculas antes de guardar
        self.codigo = self.codigo.upper()
        self.nombre = self.nombre.upper()
        super(Categoria, self).save(*args, **kwargs)


class Subcategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    codigo = models.CharField(
        max_length=3,
        validators=[RegexValidator(r'^[A-Za-z0-9]{3}$', 'El código debe ser exactamente 3 caracteres alfanuméricos')],
        help_text='Código de 3 caracteres (letras y números)'
    )
    nombre = models.CharField(max_length=255)

    class Meta:
        unique_together = ('codigo', 'categoria')
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre} (Cat: {self.categoria.codigo})'

    def save(self, *args, **kwargs):
        # Convertir el código y nombre a mayúsculas antes de guardar
        self.codigo = self.codigo.upper()
        self.nombre = self.nombre.upper()
        super(Subcategoria, self).save(*args, **kwargs)


class Clase(models.Model):
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.CASCADE, related_name='clases')
    codigo = models.CharField(
        max_length=3,
        validators=[RegexValidator(r'^[A-Za-z0-9]{3}$', 'El código debe ser exactamente 3 caracteres alfanuméricos')],
        help_text='Código de 3 caracteres (letras y números)'
    )
    nombre = models.CharField(max_length=255)

    class Meta:
        unique_together = ('codigo', 'subcategoria')
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.nombre} (Subcat: {self.subcategoria.codigo})'

    def save(self, *args, **kwargs):
        # Convertir el código y nombre a mayúsculas antes de guardar
        self.codigo = self.codigo.upper()
        self.nombre = self.nombre.upper()
        super(Clase, self).save(*args, **kwargs)

