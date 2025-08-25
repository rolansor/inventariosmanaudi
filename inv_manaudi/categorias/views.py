from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CategoriaForm, SubcategoriaForm, ClaseForm
from .models import Categoria, Subcategoria, Clase
from usuarios.templatetags.tags import control_acceso


@control_acceso('Supervisor')
def nueva_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.empresa = request.user.perfil.empresa  # Asignar la empresa del usuario logueado
            categoria.save()
            if request.is_ajax():
                return JsonResponse({
                    'id': categoria.id,
                    'codigo': categoria.codigo,
                    'nombre': categoria.nombre,
                    'success': True
                })
        else:
            if request.is_ajax():
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@control_acceso('Supervisor')
def lista_categorias(request):
    empresa = request.user.perfil.empresa
    categorias = Categoria.objects.filter(empresa=empresa)
    return render(request, 'lista_categorias.html', {'categorias': categorias})


@control_acceso('Supervisor')
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

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
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({
        'codigo': categoria.codigo,
        'nombre': categoria.nombre,
        'success': True
    })


@control_acceso('Manaudi')
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        return JsonResponse({'id': pk, 'success': True})

    return redirect('lista_categorias')


@control_acceso('Supervisor')
def nueva_subcategoria(request, pk):
    categoria = get_object_or_404(Categoria, id=pk)
    if request.method == 'POST':
        form = SubcategoriaForm(request.POST)
        if form.is_valid():
            subcategoria = form.save(commit=False)
            subcategoria.categoria = categoria
            subcategoria.save()
            if request.is_ajax():
                return JsonResponse({
                    'id': subcategoria.id,
                    'codigo': subcategoria.codigo,
                    'nombre': subcategoria.nombre,
                    'categoria': categoria.nombre
                })
            else:
                return redirect('lista_subcategorias', pk=pk)
        else:
            if request.is_ajax():
                # Enviar los errores del formulario como JSON
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@control_acceso('Supervisor')
def lista_subcategorias(request, pk):
    categoria = get_object_or_404(Categoria, id=pk)
    subcategorias = Subcategoria.objects.filter(categoria=categoria)
    return render(request, 'lista_subcategorias.html', {'subcategorias': subcategorias, 'categoria': categoria})


@control_acceso('Supervisor')
def editar_subcategoria(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)

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
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return JsonResponse({
        'codigo': subcategoria.codigo,
        'nombre': subcategoria.nombre,
        'success': True
    })


@control_acceso('Manaudi')
def eliminar_subcategoria(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)
    if request.method == 'POST':
        subcategoria.delete()
        return JsonResponse({'id': pk, 'success': True})

    return redirect('lista_subcategorias', categoria_pk=subcategoria.categoria.pk)


@control_acceso('Supervisor')
def nueva_clase(request, pk):
    subcategoria = get_object_or_404(Subcategoria, id=pk)
    if request.method == 'POST':
        form = ClaseForm(request.POST)
        if form.is_valid():
            clase = form.save(commit=False)
            clase.subcategoria = subcategoria
            clase.save()
            if request.is_ajax():
                data = {
                    'id': clase.id,
                    'codigo': clase.codigo,
                    'nombre': clase.nombre,
                    'subcategoria': subcategoria.nombre,
                    'categoria': subcategoria.categoria.nombre
                }
                return JsonResponse(data)
            else:
                return redirect('lista_clases', pk=pk)
        else:
            if request.is_ajax():
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@control_acceso('Supervisor')
def lista_clases(request, pk):
    subcategoria = get_object_or_404(Subcategoria, id=pk)
    clases = Clase.objects.filter(subcategoria=subcategoria)
    return render(request, 'lista_clases.html', {
        'clases': clases, 
        'subcategoria': subcategoria,
        'categoria': subcategoria.categoria
    })


@control_acceso('Supervisor')
def editar_clase(request, pk):
    clase = get_object_or_404(Clase, pk=pk)
    
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
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    return JsonResponse({
        'codigo': clase.codigo,
        'nombre': clase.nombre,
        'success': True
    })


@control_acceso('Manaudi')
def eliminar_clase(request, pk):
    clase = get_object_or_404(Clase, pk=pk)
    if request.method == 'POST':
        clase.delete()
        return JsonResponse({'id': pk, 'success': True})
    
    return redirect('lista_clases', pk=clase.subcategoria.pk)
