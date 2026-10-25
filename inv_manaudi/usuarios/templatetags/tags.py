"""
Control de acceso por grupos.

Los roles del sistema son grupos de ``django.contrib.auth``: **Manaudi**, **Supervisor**,
**Encargado** y **Auditor**. No hay herencia entre ellos en el código: un usuario
acumula permisos sumando grupos (``populate_data`` asigna a Manaudi los cuatro grupos
y a Supervisor los grupos Supervisor + Encargado + Auditor).

Este módulo se carga en las plantillas con ``{% load tags %}`` (filtro
``pertenece_grupo``) y se importa en las vistas para el decorador ``control_acceso``.
"""
from functools import wraps

from django import template
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render

register = template.Library()


@register.filter(name='pertenece_grupo')
def pertenece_grupo(user, group_name):
    """
    Filtro de plantilla: ``{% if request.user|pertenece_grupo:"Manaudi" %}``.

    Devuelve True si el usuario pertenece al grupo indicado. Se usa para mostrar u
    ocultar opciones del menú y botones según el rol.
    """
    return user.groups.filter(name=group_name).exists()


def control_acceso(grupo_requerido):
    """
    Decorador de vistas: permite el acceso solo a usuarios del grupo indicado.

    - Usuario anónimo: redirige al login conservando ``?next=`` (como ``login_required``).
    - Usuario autenticado sin el grupo: renderiza ``acceso_denegado.html`` con HTTP 403.
    - Usuario con el grupo: ejecuta la vista.

    Uso::

        @control_acceso('Supervisor')
        def crear_producto(request): ...
    """
    def decorador(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.groups.filter(name=grupo_requerido).exists():
                return view_func(request, *args, **kwargs)
            return render(request, 'acceso_denegado.html', status=403)
        return _wrapped_view
    return decorador
