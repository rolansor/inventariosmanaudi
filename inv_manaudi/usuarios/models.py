from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


class Empresa(models.Model):
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Sucursal(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sucursales')
    nombre = models.CharField(max_length=255)
    abreviatura = models.CharField(max_length=3)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f'{self.nombre} - {self.empresa.nombre}'


class Usuario(AbstractUser):
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username


class UsuarioPerfil(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='perfiles')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='perfiles', null=True, blank=True)

    def clean(self):
        if self.sucursal and self.sucursal.empresa != self.empresa:
            raise ValidationError('La sucursal debe pertenecer a la empresa asignada al usuario.')

    def __str__(self):
        return f'{self.usuario.username} - {self.empresa.nombre} ({self.sucursal.nombre if self.sucursal else "Sin Sucursal"})'
