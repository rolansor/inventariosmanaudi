"""Utilidades compartidas entre apps."""


def es_ajax(request):
    """
    Indica si la petición fue hecha con ``XMLHttpRequest`` (jQuery lo marca por defecto).

    Reemplaza a ``request.is_ajax()``, eliminado en Django 4.0. Las vistas lo usan para
    decidir si responden JSON (para los formularios AJAX de los listados) o redirigen.
    """
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'
