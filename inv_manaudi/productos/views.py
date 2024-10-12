from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from categorias.models import Subcategoria
from .models import Producto
from .forms import ProductoForm


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


def consulta_producto(request):
    productos = Producto.objects.all()
    return render(request, 'consulta_producto.html', {'productos': productos})


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


