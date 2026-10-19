from functools import wraps

from django import template
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render

register = template.Library()


@register.filter(name='pertenece_grupo')
def pertenece_grupo(user, group_name):
    return user.groups.filter(name=group_name).exists()


def control_acceso(grupo_requerido):
    """
    Permite el acceso solo a usuarios autenticados que pertenezcan al grupo indicado.
    Los usuarios anónimos se envían al login (con ?next=), igual que @login_required.
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
