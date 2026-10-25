"""
Vistas de la app ``categorias``.

Tres pantallas con el mismo patrón, una por nivel:

- ``lista_categorias``   → ``/categorias/lista_categorias/``
- ``lista_subcategorias`` → ``/categorias/<categoria>/lista_subcategorias/``
- ``lista_clases``        → ``/categorias/subcategorias/<subcategoria>/lista_clases/``

Cada listado tiene un modal para crear y botones para editar/eliminar que llaman por
AJAX a las vistas ``nueva_*``, ``editar_*`` y ``eliminar_*``. Crear y editar requiere
el grupo **Supervisor**; eliminar requiere **Manaudi** (borra en cascada los niveles
inferiores; los productos de las clases borradas quedan sin clasificación).

Todas las búsquedas por ``pk`` se acotan a la empresa activa: un ID de otra empresa
devuelve 404.
"""
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CategoriaForm, SubcategoriaForm, ClaseForm
from .models import Categoria, Subcategoria, Clase
from usuarios.templatetags.tags import control_acceso
from usuarios.utils import es_ajax
from usuarios.views import obtener_empresa


# ---------------------------------------------------------------------------
# Helpers: siempre se busca dentro de la empresa activa para evitar que un
# usuario acceda por ID a datos de otra empresa.
# ---------------------------------------------------------------------------

def _categoria_de_empresa(request, pk):
    """Categoría ``pk`` de la empresa activa, o 404."""
    return get_object_or_404(Categoria, pk=pk, empresa=obtener_empresa(request))


def _subcategoria_de_empresa(request, pk):
    """Subcategoría ``pk`` cuya categoría pertenece a la empresa activa, o 404."""
    return get_object_or_404(Subcategoria, pk=pk, categoria__empresa=obtener_empresa(request))


def _clase_de_empresa(request, pk):
    """Clase ``pk`` cuya categoría (dos niveles arriba) pertenece a la empresa activa, o 404."""
    return get_object_or_404(Clase, pk=pk, subcategoria__categoria__empresa=obtener_empresa(request))


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------

@control_acceso('Supervisor')
def nueva_categoria(request):
    """Crea una categoría en la empresa activa (solo POST; GET redirige al listado)."""
    if request.method != 'POST':
        return redirect('lista_categorias')

    form = CategoriaForm(request.POST)
    if form.is_valid():
        categoria = form.save(commit=False)
        categoria.empresa = obtener_empresa(request)
        categoria.save()
        if es_ajax(request):
            return JsonResponse({
                'id': categoria.id,
                'codigo': categoria.codigo,
                'nombre': categoria.nombre,
                'success': True
            })
        return redirect('lista_categorias')

    if es_ajax(request):
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return render(request, 'lista_categorias.html', {
        'categorias': Categoria.objects.filter(empresa=obtener_empresa(request)),
        'form': form,
    })


@control_acceso('Supervisor')
def lista_categorias(request):
    """Listado de categorías de la empresa activa."""
    categorias = Categoria.objects.filter(empresa=obtener_empresa(request))
    return render(request, 'lista_categorias.html', {'categorias': categorias})


@control_acceso('Supervisor')
def editar_categoria(request, pk):
    """
    Edita una categoría (AJAX). GET devuelve los datos actuales en JSON para
    precargar el modal; POST guarda y devuelve la categoría actualizada.
    """
    categoria = _categoria_de_empresa(request, pk)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            return JsonResponse({
                'id': categoria.id,
                'codigo': categoria.codigo,
                'nombre': categoria.nombre,
                'success': True
            })
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({
        'codigo': categoria.codigo,
        'nombre': categoria.nombre,
        'success': True
    })


@control_acceso('Manaudi')
def eliminar_categoria(request, pk):
    """Elimina una categoría con sus subcategorías y clases (solo POST, AJAX)."""
    categoria = _categoria_de_empresa(request, pk)
    if request.method == 'POST':
        categoria.delete()
        return JsonResponse({'id': pk, 'success': True})

    return redirect('lista_categorias')


# ---------------------------------------------------------------------------
# Subcategorías
# ---------------------------------------------------------------------------

@control_acceso('Supervisor')
def nueva_subcategoria(request, pk):
    """Crea una subcategoría dentro de la categoría ``pk`` (solo POST)."""
    categoria = _categoria_de_empresa(request, pk)
    if request.method != 'POST':
        return redirect('lista_subcategorias', pk=pk)

    form = SubcategoriaForm(request.POST)
    if form.is_valid():
        subcategoria = form.save(commit=False)
        subcategoria.categoria = categoria
        subcategoria.save()
        if es_ajax(request):
            return JsonResponse({
                'id': subcategoria.id,
                'codigo': subcategoria.codigo,
                'nombre': subcategoria.nombre,
                'categoria': categoria.nombre,
                'success': True
            })
        return redirect('lista_subcategorias', pk=pk)

    if es_ajax(request):
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return render(request, 'lista_subcategorias.html', {
        'subcategorias': Subcategoria.objects.filter(categoria=categoria),
        'categoria': categoria,
        'form': form,
    })


@control_acceso('Supervisor')
def lista_subcategorias(request, pk):
    """Listado de subcategorías de la categoría ``pk``."""
    categoria = _categoria_de_empresa(request, pk)
    subcategorias = Subcategoria.objects.filter(categoria=categoria)
    return render(request, 'lista_subcategorias.html', {'subcategorias': subcategorias, 'categoria': categoria})


@control_acceso('Supervisor')
def editar_subcategoria(request, pk):
    """Edita una subcategoría (AJAX). GET precarga, POST guarda."""
    subcategoria = _subcategoria_de_empresa(request, pk)

    if request.method == 'POST':
        form = SubcategoriaForm(request.POST, instance=subcategoria)
        if form.is_valid():
            subcategoria = form.save()
            return JsonResponse({
                'id': subcategoria.id,
                'codigo': subcategoria.codigo,
                'nombre': subcategoria.nombre,
                'categoria': subcategoria.categoria.nombre,
                'success': True
            })
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({
        'codigo': subcategoria.codigo,
        'nombre': subcategoria.nombre,
        'success': True
    })


@control_acceso('Manaudi')
def eliminar_subcategoria(request, pk):
    """Elimina una subcategoría con sus clases (solo POST, AJAX)."""
    subcategoria = _subcategoria_de_empresa(request, pk)
    if request.method == 'POST':
        subcategoria.delete()
        return JsonResponse({'id': pk, 'success': True})

    return redirect('lista_subcategorias', pk=subcategoria.categoria.pk)


# ---------------------------------------------------------------------------
# Clases
# ---------------------------------------------------------------------------

@control_acceso('Supervisor')
def nueva_clase(request, pk):
    """Crea una clase dentro de la subcategoría ``pk`` (solo POST)."""
    subcategoria = _subcategoria_de_empresa(request, pk)
    if request.method != 'POST':
        return redirect('lista_clases', pk=pk)

    form = ClaseForm(request.POST)
    if form.is_valid():
        clase = form.save(commit=False)
        clase.subcategoria = subcategoria
        clase.save()
        if es_ajax(request):
            return JsonResponse({
                'id': clase.id,
                'codigo': clase.codigo,
                'nombre': clase.nombre,
                'subcategoria': subcategoria.nombre,
                'categoria': subcategoria.categoria.nombre,
                'success': True
            })
        return redirect('lista_clases', pk=pk)

    if es_ajax(request):
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return render(request, 'lista_clases.html', {
        'clases': Clase.objects.filter(subcategoria=subcategoria),
        'subcategoria': subcategoria,
        'categoria': subcategoria.categoria,
        'form': form,
    })


@control_acceso('Supervisor')
def lista_clases(request, pk):
    """Listado de clases de la subcategoría ``pk``."""
    subcategoria = _subcategoria_de_empresa(request, pk)
    clases = Clase.objects.filter(subcategoria=subcategoria)
    return render(request, 'lista_clases.html', {
        'clases': clases,
        'subcategoria': subcategoria,
        'categoria': subcategoria.categoria
    })


@control_acceso('Supervisor')
def editar_clase(request, pk):
    """Edita una clase (AJAX). GET precarga, POST guarda."""
    clase = _clase_de_empresa(request, pk)

    if request.method == 'POST':
        form = ClaseForm(request.POST, instance=clase)
        if form.is_valid():
            clase = form.save()
            return JsonResponse({
                'id': clase.id,
                'codigo': clase.codigo,
                'nombre': clase.nombre,
                'subcategoria': clase.subcategoria.nombre,
                'categoria': clase.subcategoria.categoria.nombre,
                'success': True
            })
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({
        'codigo': clase.codigo,
        'nombre': clase.nombre,
        'success': True
    })


@control_acceso('Manaudi')
def eliminar_clase(request, pk):
    """
    Elimina una clase (solo POST, AJAX). Los productos que la usaban quedan con
    ``clase = NULL`` ("Sin clasificación").
    """
    clase = _clase_de_empresa(request, pk)
    if request.method == 'POST':
        clase.delete()
        return JsonResponse({'id': pk, 'success': True})

    return redirect('lista_clases', pk=clase.subcategoria.pk)
