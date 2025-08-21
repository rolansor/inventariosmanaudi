from .models import Empresa
from .views import obtener_empresa


def empresa_context(request):
    """
    Context processor para agregar información de empresas a todos los templates.
    """
    context = {}
    
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # Para superadmin, mostrar todas las empresas y la actual
            context['todas_las_empresas'] = Empresa.objects.all().order_by('nombre')
            context['empresa_actual'] = obtener_empresa(request)
        elif hasattr(request.user, 'perfil') and request.user.perfil.empresa:
            # Para usuarios normales, solo su empresa
            context['empresa_actual'] = request.user.perfil.empresa
    
    return context