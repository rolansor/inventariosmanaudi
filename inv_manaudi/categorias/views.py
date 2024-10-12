from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CategoriaForm, SubcategoriaForm
from .models import Categoria, Subcategoria
from usuarios.templatetags.tags import control_acceso


@control_acceso('Contabilidad')
def nueva_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.empresa = request.user.perfil.empresa  # Asignar la empresa del usuario logueado
            categoria.save()
            return redirect('lista_categorias')  # Redirigir a la lista de categorías
    else:
        form = CategoriaForm()

    return render(request, 'crear_categoria.html', {'form': form})


def lista_categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'lista_categorias.html', {'categorias': categorias})


@control_acceso('Contabilidad')
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            return JsonResponse({
                'id': categoria.id,
                'nombre': categoria.nombre,
                'success': True
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({
        'nombre': categoria.nombre,
        'success': True
    })


@control_acceso('Contabilidad')
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        return JsonResponse({'id': pk, 'success': True})

    return redirect('lista_categorias')


@control_acceso('Contabilidad')
def nueva_subcategoria(request, pk):
    categoria = get_object_or_404(Categoria, id=pk)
    if request.method == 'POST':
        form = SubcategoriaForm(request.POST)
        if form.is_valid():
            subcategoria = form.save(commit=False)
            subcategoria.categoria = categoria
            subcategoria.save()
            if request.is_ajax():
                data = {
                    'id': subcategoria.id,
                    'nombre': subcategoria.nombre,
                    'categoria': categoria.nombre
                }
                return JsonResponse(data)
            else:
                return redirect('lista_subcategorias', pk=pk)
        else:
            if request.is_ajax():
                # Enviar los errores del formulario como JSON
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)


def lista_subcategorias(request, pk):
    categoria = get_object_or_404(Categoria, id=pk)
    subcategorias = Subcategoria.objects.filter(categoria=categoria)
    return render(request, 'lista_subcategorias.html', {'subcategorias': subcategorias, 'categoria': categoria})


@control_acceso('Contabilidad')
def editar_subcategoria(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)

    if request.method == 'POST':
        form = SubcategoriaForm(request.POST, instance=subcategoria)
        if form.is_valid():
            subcategoria = form.save()
            return JsonResponse({
                'id': subcategoria.id,
                'nombre': subcategoria.nombre,
                'categoria': subcategoria.categoria.nombre,
                'success': True
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({
        'nombre': subcategoria.nombre,
        'success': True
    })


@control_acceso('Contabilidad')
def eliminar_subcategoria(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)
    if request.method == 'POST':
        subcategoria.delete()
        return JsonResponse({'id': pk, 'success': True})

    return redirect('lista_subcategorias', categoria_pk=subcategoria.categoria.pk)
