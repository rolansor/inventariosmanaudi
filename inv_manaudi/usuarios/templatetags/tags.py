from functools import wraps

from django import template
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

register = template.Library()


@register.filter(name='pertenece_grupo')
def pertenece_grupo(user, group_name):
    return user.groups.filter(name=group_name).exists()


def control_acceso(grupo_requerido):
    def decorador(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Asume que el perfil tiene un campo 'rol' o similar para verificar el rol
            if request.user.groups.filter(name=grupo_requerido).exists():
                return view_func(request, *args, **kwargs)
            else:
                # Si no tiene el rol adecuado, redirigir a la plantilla de acceso denegado
                return render(request, 'acceso_denegado.html')
        return _wrapped_view
    return decorador
