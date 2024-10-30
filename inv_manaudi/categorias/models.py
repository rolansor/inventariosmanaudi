from django.db import models
from usuarios.models import Empresa


class Categoria(models.Model):
    nombre = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias')

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Convertir el nombre a mayúsculas antes de guardar
        self.nombre = self.nombre.upper()
        super(Categoria, self).save(*args, **kwargs)


class Subcategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.nombre} (Categoría: {self.categoria.nombre})'

    def save(self, *args, **kwargs):
        # Convertir el nombre a mayúsculas antes de guardar
        self.nombre = self.nombre.upper()
        super(Subcategoria, self).save(*args, **kwargs)
