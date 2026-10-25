"""
Modelos de la app ``usuarios``: estructura organizacional y cuentas.

Jerarquía:

    Empresa ──< Sucursal
       │
       └──< UsuarioPerfil >── Usuario (AbstractUser)

Toda la información del sistema (categorías, productos, inventario y movimientos)
cuelga de una ``Empresa``. El ``UsuarioPerfil`` indica a qué empresa pertenece cada
usuario y, opcionalmente, a qué sucursal está asignado. Los permisos funcionales no
viven aquí: se resuelven por pertenencia a grupos de ``django.contrib.auth``
(ver ``usuarios.templatetags.tags.control_acceso``).
"""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


class Empresa(models.Model):
    """
    Cliente de Manaudi al que pertenece un conjunto de sucursales, usuarios y productos.

    Es la raíz del aislamiento multi-empresa: todas las consultas de la aplicación
    se filtran por la empresa activa (ver ``usuarios.views.obtener_empresa``).
    """
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Sucursal(models.Model):
    """
    Punto físico de una empresa donde se guarda stock (bodega, punto de venta o laboratorio).

    El inventario y los movimientos siempre se registran contra una sucursal; los
    traslados mueven stock entre dos sucursales de la misma empresa.
    """
    TIPO_SUCURSAL_CHOICES = [
        ('bodega', 'Bodega'),
        ('punto_venta', 'Punto de Venta'),
        ('laboratorio', 'Laboratorio'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sucursales')
    nombre = models.CharField(max_length=255)
    abreviatura = models.CharField(max_length=3)  # Código corto, ej. UIO, GYE
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    tipo_sucursal = models.CharField(max_length=20, choices=TIPO_SUCURSAL_CHOICES)

    def __str__(self):
        return f'{self.nombre} - {self.empresa.nombre}'


class Usuario(AbstractUser):
    """
    Usuario del sistema. Extiende el usuario estándar de Django con teléfono y dirección.

    La empresa y sucursal del usuario están en ``UsuarioPerfil`` (``usuario.perfil``).
    Los roles (Manaudi, Supervisor, Encargado, Auditor) son grupos de Django.
    """
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username


class UsuarioPerfil(models.Model):
    """
    Vincula un usuario con su empresa y, opcionalmente, con una sucursal.

    - Usuario **con** sucursal: opera solo sobre esa sucursal (el formulario de
      movimientos la fija y solo puede confirmar traslados destinados a ella).
    - Usuario **sin** sucursal (Manaudi, Auditor, superusuario): ve toda la empresa.

    Los superusuarios no necesitan perfil: eligen la empresa activa desde la sesión.
    """
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='perfiles')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='perfiles', null=True, blank=True)

    def clean(self):
        """Impide asignar una sucursal que no pertenezca a la empresa del perfil."""
        if self.sucursal and self.sucursal.empresa != self.empresa:
            raise ValidationError('La sucursal debe pertenecer a la empresa asignada al usuario.')

    def __str__(self):
        return f'{self.usuario.username} - {self.empresa.nombre} ({self.sucursal.nombre if self.sucursal else "Sin Sucursal"})'
