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


@control_acceso('Encargado')
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


@control_acceso('Encargado')
def lista_productos(request):
    # Obtener la empresa del perfil del usuario actual
    empresa = obtener_empresa(request)

    # Filtrar los productos asociados a la empresa
    productos = Producto.objects.filter(empresa=empresa)

    # Pasar los productos al contexto de la plantilla
    return render(request, 'lista_productos.html', {'productos': productos})


@control_acceso('Encargado')
def busqueda_producto(request):
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria')

    # Filtrar los productos por código, nombre o categoría
    productos = None
    if query or categoria_id:
        productos = Producto.objects.all()

        if query:
            productos = productos.filter(Q(codigo__icontains=query) | Q(nombre__icontains=query))

            # Filtro por categoría (incluye todas las subcategorías de la categoría seleccionada)
        if categoria_id:
            try:
                # Obtener la categoría seleccionada
                categoria = Categoria.objects.get(id=categoria_id)

                # Obtener todas las subcategorías asociadas a la categoría seleccionada
                subcategorias = Subcategoria.objects.filter(categoria=categoria)

                # Filtrar los productos que pertenezcan a las subcategorías de la categoría seleccionada
                productos = productos.filter(categoria__in=subcategorias)

            except Categoria.DoesNotExist:
                productos = Producto.objects.none()  # En caso de que no exista la categoría

    # Obtener todas las categorías para el filtro
    categorias = Categoria.objects.all()

    context = {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id
    }

    return render(request, 'busqueda_producto.html', context)


def buscar_producto_por_codigo(request):
    """
    Vista para buscar un producto por su código y devolver sus datos en JSON.
    """
    codigo = request.GET.get('codigo')

    try:
        producto = Producto.objects.get(codigo=codigo)
        # Devolver los datos del producto en JSON
        data = {
            'id': producto.pk,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': producto.precio,
            'tipo_producto': producto.tipo_producto,
            'categoria_id': producto.categoria.pk if producto.categoria else None
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        # Si no se encuentra el producto, devolver un error
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)


@control_acceso('Encargado')
def editar_producto(request, pk=None):
    """
    Vista para editar un producto.
    - Si se pasa un pk, edita un producto existente.
    - Si no se pasa un pk, muestra un formulario vacío y permite buscar el producto por AJAX.
    """
    subcategorias = Subcategoria.objects.all().order_by('nombre')

    if pk:
        # Escenario 1: Se pasa un pk, busca el producto
        producto = get_object_or_404(Producto, pk=pk)

        if request.method == 'POST':
            # Procesar la edición del producto
            form = ProductoForm(request.POST, instance=producto)
            if form.is_valid():
                producto = form.save()
                messages.success(request, 'Producto actualizado con éxito.')
                return redirect('editar_producto')
            else:
                messages.error(request, 'Error al actualizar el producto.')
        else:
            form = ProductoForm(instance=producto)

        # Renderizar el formulario para la edición
        return render(request, 'editar_producto.html', {
            'form': form,
            'producto': producto,
            'subcategorias': subcategorias
        })

    else:
        # Escenario 2: No se pasa pk, mostrar formulario vacío para buscar por código
        if request.method == 'POST':
            # Buscar el producto por código
            codigo = request.POST.get('codigo')
            try:
                producto = Producto.objects.get(codigo=codigo)
                form = ProductoForm(request.POST, instance=producto)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Producto actualizado con éxito.')
                    return redirect('editar_producto')
                else:
                    messages.error(request, 'Error al actualizar el producto.')
                    return render(request, 'editar_producto.html', {
                        'form': form,
                        'producto': producto,
                        'subcategorias': subcategorias
                    })
            except Producto.DoesNotExist:
                messages.error(request, 'No se encontró un producto con el código proporcionado.')
                return redirect('editar_producto')

        # Formulario vacío para que el usuario ingrese el código
        return render(request, 'editar_producto.html', {'subcategorias': subcategorias})


def bsq_por_codigo(request):
    """
    Vista para buscar un producto por su código y devolver sus datos en JSON.
    """
    codigo = request.GET.get('codigo')

    try:
        producto = Producto.objects.get(codigo=codigo)
        # Devolver los datos del producto en JSON
        data = {
            'id': producto.pk,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': producto.precio,
            'tipo_producto': producto.tipo_producto,
            'categoria_id': producto.categoria.pk if producto.categoria else None
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        # Si no se encuentra el producto, devolver un error
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)


@control_acceso('Administrador')
def desactivar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'GET':
        producto.estado = 'inactivo'  # Cambiar el estado del producto
        producto.save()
        messages.success(request, 'Producto desactivado con éxito.')
        return redirect('lista_productos')
    return redirect('lista_productos')


@control_acceso('Administrador')
def activar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'GET':
        producto.estado = 'activo'  # Cambiar el estado del producto
        producto.save()
        messages.success(request, 'Producto desactivado con éxito.')
        return redirect('lista_productos')
    return redirect('lista_productos')

