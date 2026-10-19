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
    return get_object_or_404(Categoria, pk=pk, empresa=obtener_empresa(request))


def _subcategoria_de_empresa(request, pk):
    return get_object_or_404(Subcategoria, pk=pk, categoria__empresa=obtener_empresa(request))


def _clase_de_empresa(request, pk):
    return get_object_or_404(Clase, pk=pk, subcategoria__categoria__empresa=obtener_empresa(request))


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------

@control_acceso('Supervisor')
def nueva_categoria(request):
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
    categorias = Categoria.objects.filter(empresa=obtener_empresa(request))
    return render(request, 'lista_categorias.html', {'categorias': categorias})


@control_acceso('Supervisor')
def editar_categoria(request, pk):
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
    categoria = _categoria_de_empresa(request, pk)
    subcategorias = Subcategoria.objects.filter(categoria=categoria)
    return render(request, 'lista_subcategorias.html', {'subcategorias': subcategorias, 'categoria': categoria})


@control_acceso('Supervisor')
def editar_subcategoria(request, pk):
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
    subcategoria = _subcategoria_de_empresa(request, pk)
    clases = Clase.objects.filter(subcategoria=subcategoria)
    return render(request, 'lista_clases.html', {
        'clases': clases,
        'subcategoria': subcategoria,
        'categoria': subcategoria.categoria
    })


@control_acceso('Supervisor')
def editar_clase(request, pk):
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
    clase = _clase_de_empresa(request, pk)
    if request.method == 'POST':
        clase.delete()
        return JsonResponse({'id': pk, 'success': True})

    return redirect('lista_clases', pk=clase.subcategoria.pk)
