from django.db import models
from usuarios.models import Empresa


class Categoria(models.Model):
    nombre = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias')

    def __str__(self):
        return self.nombre


class Subcategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.nombre} (Categoría: {self.categoria.nombre})'
