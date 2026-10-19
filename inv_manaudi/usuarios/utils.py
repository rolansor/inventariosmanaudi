"""Utilidades compartidas entre apps."""


def es_ajax(request):
    """
    Reemplazo de request.is_ajax() (eliminado en Django 4.0).
    Detecta peticiones hechas con XMLHttpRequest (jQuery las marca por defecto).
    """
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'
