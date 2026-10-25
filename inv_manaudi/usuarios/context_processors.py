"""Context processors registrados en ``settings.TEMPLATES``."""
from .models import Empresa
from .views import obtener_empresa


def empresa_context(request):
    """
    Expone la empresa activa a todas las plantillas (cabecera de ``base.html``).

    Variables agregadas al contexto:

    - ``empresa_actual``: empresa sobre la que trabaja el usuario.
    - ``todas_las_empresas``: solo para superusuarios; alimenta el selector de empresa
      de la barra superior (vista ``cambiar_empresa``).
    """
    context = {}

    if request.user.is_authenticated:
        if request.user.is_superuser:
            context['todas_las_empresas'] = Empresa.objects.all().order_by('nombre')
            context['empresa_actual'] = obtener_empresa(request)
        elif hasattr(request.user, 'perfil') and request.user.perfil.empresa:
            context['empresa_actual'] = request.user.perfil.empresa

    return context
