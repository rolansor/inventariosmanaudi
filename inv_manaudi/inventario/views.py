from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Empresa, Sucursal, Categoria, Subcategoria, Producto
from .forms import EmpresaForm, SucursalForm, CategoriaForm, SubcategoriaForm, ProductoForm


def empresa_list(request):
    # Obtener todas las empresas
    empresas = Empresa.objects.all()

    # Manejo del formulario para crear/editar una empresa
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            if request.is_ajax():
                data = {
                    'id': empresa.pk,
                    'nombre': empresa.nombre,
                    'direccion': empresa.direccion,
                    'telefono': empresa.telefono,
                    'email': empresa.email
                }
                return JsonResponse(data)
            else:
                return redirect('empresa_list')
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        form = EmpresaForm()

    return render(request, 'empresas.html', {'empresas': empresas, 'form': form})


# Editar una empresa existente (llamado con ajax u otro mecanismo)
def empresa_edit(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            empresa = form.save()
            if request.is_ajax():
                # Devolver solo los datos de la empresa como JSON
                data = {
                    'id': empresa.pk,
                    'nombre': empresa.nombre,
                    'direccion': empresa.direccion,
                    'telefono': empresa.telefono,
                    'email': empresa.email
                }
                return JsonResponse(data)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        if request.is_ajax():
            # Devolver los datos para precargar el formulario
            data = {
                'nombre': empresa.nombre,
                'direccion': empresa.direccion,
                'telefono': empresa.telefono,
                'email': empresa.email
            }
            return JsonResponse(data)


# Eliminar una empresa existente
def empresa_delete(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        return redirect('empresa_list')
    return render(request, 'empresas.html', {'form': EmpresaForm(), 'empresas': Empresa.objects.all()})


# Listar todas las sucursales
def sucursal_list(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    sucursales = Sucursal.objects.filter(empresa=empresa)

    if request.method == 'POST':
        form = SucursalForm(request.POST)
        if form.is_valid():
            sucursal = form.save(commit=False)
            sucursal.empresa = empresa  # Asignar la empresa antes de guardar
            sucursal.save()

            if request.is_ajax():
                # Si es una solicitud Ajax, devolvemos los datos de la nueva sucursal
                data = {
                    'id': sucursal.id,
                    'nombre': sucursal.nombre,
                    'abreviatura': sucursal.abreviatura,
                    'direccion': sucursal.direccion,
                    'telefono': sucursal.telefono,
                    'empresa': sucursal.empresa.nombre
                }
                return JsonResponse(data)
            else:
                return redirect('sucursal_list', pk=pk)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        form = SucursalForm()

    return render(request, 'sucursales.html', {'sucursales': sucursales, 'empresa': empresa, 'form': form})


# Editar una sucursal existente
def sucursal_edit(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)

    if request.method == 'POST':
        form = SucursalForm(request.POST, instance=sucursal)
        if form.is_valid():
            sucursal = form.save()
            if request.is_ajax():
                data = {
                    'id': sucursal.pk,
                    'nombre': sucursal.nombre,
                    'abreviatura': sucursal.abreviatura,
                    'direccion': sucursal.direccion,
                    'telefono': sucursal.telefono,
                    'empresa_id': sucursal.empresa_id
                }
                return JsonResponse(data)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        if request.is_ajax():
            data = {
                'nombre': sucursal.nombre,
                'abreviatura': sucursal.abreviatura,
                'direccion': sucursal.direccion,
                'telefono': sucursal.telefono,
                'empresa_id': sucursal.empresa_id
            }
            return JsonResponse(data)


# Eliminar una sucursal
def sucursal_delete(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)
    if request.method == 'POST':
        sucursal.delete()
        return JsonResponse({'success': True})
    return redirect('sucursal_list')


def categoria_list(request):
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            if request.is_ajax():
                data = {
                    'id': categoria.id,
                    'nombre': categoria.nombre,
                }
                return JsonResponse(data)
            else:
                return redirect('categoria_list')
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        form = CategoriaForm()

    return render(request, 'categorias.html', {'categorias': categorias, 'form': form})

def categoria_edit(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            if request.is_ajax():
                data = {
                    'id': categoria.id,
                    'nombre': categoria.nombre,
                }
                return JsonResponse(data)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        if request.is_ajax():
            data = {
                'nombre': categoria.nombre,
            }
            return JsonResponse(data)

def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        if request.is_ajax():
            return JsonResponse({'id': pk})
        else:
            return redirect('categoria_list')


def subcategoria_list(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    subcategorias = Subcategoria.objects.filter(categoria=categoria)

    if request.method == 'POST':
        form = SubcategoriaForm(request.POST)
        if form.is_valid():
            subcategoria = form.save(commit=False)
            subcategoria.categoria = categoria  # Asignar la categoría antes de guardar
            subcategoria.save()

            if request.is_ajax():
                data = {
                    'id': subcategoria.id,
                    'nombre': subcategoria.nombre,
                    'categoria': subcategoria.categoria.nombre
                }
                return JsonResponse(data)
            else:
                return redirect('subcategoria_list', pk=pk)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        form = SubcategoriaForm()

    return render(request, 'subcategorias.html', {'subcategorias': subcategorias, 'categoria': categoria, 'form': form})


def subcategoria_edit(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)

    if request.method == 'POST':
        form = SubcategoriaForm(request.POST, instance=subcategoria)
        if form.is_valid():
            subcategoria = form.save()
            if request.is_ajax():
                data = {
                    'id': subcategoria.id,
                    'nombre': subcategoria.nombre,
                    'categoria': subcategoria.categoria.nombre
                }
                return JsonResponse(data)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        if request.is_ajax():
            data = {
                'nombre': subcategoria.nombre,
            }
            return JsonResponse(data)


def subcategoria_delete(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)
    if request.method == 'POST':
        subcategoria.delete()
        if request.is_ajax():
            return JsonResponse({'id': pk})
        else:
            return redirect('subcategoria_list', pk=subcategoria.categoria.pk)


def producto_list(request):
    productos = Producto.objects.all()
    subcategorias = Subcategoria.objects.all()

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            if request.is_ajax():
                data = {
                    'id': producto.pk,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'precio': producto.precio,
                    'tipo_producto': producto.get_tipo_producto_display(),
                    'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                }
                return JsonResponse(data)
            else:
                print(form.errors)
                return redirect('producto_list')
    else:
        form = ProductoForm()

    return render(request, 'productos.html', {'productos': productos, 'subcategorias': subcategorias, 'form': form})


def producto_edit(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save()
            if request.is_ajax():
                data = {
                    'id': producto.pk,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'precio': producto.precio,
                    'tipo_producto': producto.get_tipo_producto_display(),
                    'categoria': producto.categoria.nombre if producto.categoria else 'Sin categoría',
                }
                return JsonResponse(data)
        else:
            print(form.errors)
            return JsonResponse({'error': 'Formulario no válido'}, status=400)
    else:
        if request.is_ajax():
            data = {
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'precio': producto.precio,
                'tipo_producto': producto.tipo_producto,
                'categoria_id': producto.categoria_id,
            }
            return JsonResponse(data)


def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        if request.is_ajax():
            return JsonResponse({'id': pk})
        else:
            return redirect('producto_list')