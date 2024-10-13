from django.db import IntegrityError, DataError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from categorias.models import Subcategoria, Categoria
from usuarios.templatetags.tags import control_acceso
from usuarios.views import obtener_empresa
from .models import Producto
from .forms import ProductoForm


@control_acceso('Contabilidad')
def crear_producto(request):
    subcategorias = Subcategoria.objects.all()

    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        tipo_producto = request.POST.get('tipo_producto')
        subcategoria_id = request.POST.get('categoria')

        try:
            subcategoria = Subcategoria.objects.get(pk=subcategoria_id)

            # Validar que el precio esté en el formato correcto
            if float(precio) <= 0:
                messages.error(request, 'El precio debe ser un valor positivo.')
                return redirect('crear_producto')

            Producto.objects.create(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                tipo_producto=tipo_producto,
                categoria=subcategoria,
                empresa=obtener_empresa(request)  # Asumimos que el usuario tiene una empresa relacionada
            )
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('lista_productos')  # Redirigir a la lista de productos

        except Subcategoria.DoesNotExist:
            messages.error(request, 'Subcategoría no encontrada.')

        except DataError as e:
            # Manejo del error de rango de precio
            messages.error(request, 'El valor del precio está fuera de los límites permitidos. Intenta un valor menor.')

        except IntegrityError as e:
            # Detectamos el error por código duplicado
            if 'Duplicate entry' in str(e):
                messages.error(request, f'El código {codigo} ya existe. Por favor, elige otro.')
            else:
                messages.error(request, 'Ocurrió un error al crear el producto. Inténtalo de nuevo.')

    return render(request, 'nuevo_producto.html', {'subcategorias': subcategorias})


@control_acceso('Contabilidad')
def lista_productos(request):
    # Obtener la empresa del perfil del usuario actual
    empresa = obtener_empresa(request)

    # Filtrar los productos asociados a la empresa
    productos = Producto.objects.filter(empresa=empresa)

    # Pasar los productos al contexto de la plantilla
    return render(request, 'lista_productos.html', {'productos': productos})


@control_acceso('Contabilidad')
def busqueda_producto(request):
    query = request.GET.get('q')
    categoria_id = request.GET.get('categoria')

    # Filtrar los productos por código, nombre o categoría
    productos = Producto.objects.all()

    if query:
        productos = productos.filter(
            Q(codigo__icontains=query) |
            Q(nombre__icontains=query)
        )

        # Filtro por categoría (incluye todas las subcategorías de la categoría seleccionada)
    if categoria_id:
        # Obtener la categoría seleccionada
        categoria = Categoria.objects.get(id=categoria_id)

        # Obtener todas las subcategorías asociadas a la categoría seleccionada
        subcategorias = Subcategoria.objects.filter(categoria=categoria)

        # Filtrar los productos que pertenezcan a las subcategorías de la categoría seleccionada
        productos = productos.filter(categoria__in=subcategorias)

    # Obtener todas las categorías para el filtro
    categorias = Categoria.objects.all()

    context = {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id
    }

    return render(request, 'busqueda_producto.html', context)


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


