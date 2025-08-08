from django.db import IntegrityError, DataError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from usuarios.templatetags.tags import control_acceso
from usuarios.views import obtener_empresa
from .models import Producto
from .forms import ProductoForm


@control_acceso('Supervisor')
def crear_producto(request):
    empresa_actual = obtener_empresa(request)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.empresa = empresa_actual
            
            try:
                # El código se genera automáticamente en el método save() del modelo
                producto.save()
                messages.success(request, f'Producto creado exitosamente. Código: {producto.codigo}')
                return redirect('lista_productos')
            
            except IntegrityError as e:
                if 'Duplicate entry' in str(e) or 'unique_codigo_empresa' in str(e):
                    messages.error(request, f'Ya existe un producto con este código en su empresa.')
                else:
                    messages.error(request, 'Ocurrió un error al crear el producto.')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ProductoForm()
    
    return render(request, 'nuevo_producto.html', {'form': form})


@control_acceso('Supervisor')
def lista_productos(request):
    # Obtener la empresa del perfil del usuario actual
    empresa_actual = obtener_empresa(request)

    # Filtrar los productos asociados a la empresa
    productos = Producto.objects.para_empresa(empresa_actual)

    # Pasar los productos al contexto de la plantilla
    return render(request, 'lista_productos.html', {'productos': productos})


@control_acceso('Supervisor')
def busqueda_producto(request):
    empresa_actual = obtener_empresa(request)
    query = request.GET.get('q', '')
    linea = request.GET.get('linea')
    sublinea = request.GET.get('sublinea')
    clase = request.GET.get('clase')
    productos = None

    if query or linea or sublinea or clase:
        productos_empresa = Producto.objects.para_empresa(empresa_actual)
        
        if query:
            # Buscar por código, modelo o marca
            productos = productos_empresa.filter(
                Q(codigo__icontains=query) | 
                Q(modelo__icontains=query) | 
                Q(marca__icontains=query)
            )
        else:
            productos = productos_empresa
        
        # Filtros adicionales
        if linea:
            productos = productos.filter(linea=linea)
        if sublinea:
            productos = productos.filter(sublinea=sublinea)
        if clase:
            productos = productos.filter(clase=clase)

    context = {
        'productos': productos,
        'query': query,
        'linea_choices': Producto.LINEA_CHOICES,
        'sublinea_choices': Producto.SUBLINEA_CHOICES,
        'clase_choices': Producto.CLASE_CHOICES,
        'linea_selected': linea,
        'sublinea_selected': sublinea,
        'clase_selected': clase
    }

    return render(request, 'busqueda_producto.html', context)


@control_acceso('Supervisor')
def editar_producto(request, pk=None):
    empresa_actual = obtener_empresa(request)
    producto = get_object_or_404(Producto.objects.para_empresa(empresa_actual), pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto actualizado con éxito. Código: {producto.codigo}')
            return redirect('editar_producto', pk=producto.pk)
        else:
            messages.error(request, 'Error al actualizar el producto.')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'editar_producto.html', {
        'form': form,
        'producto': producto
    })


@control_acceso('Supervisor')
def bsq_por_codigo(request):
    """
    Vista para buscar un producto por su código y devolver sus datos en JSON.
    """
    codigo = request.GET.get('codigo')
    # Obtener la empresa del usuario logueado
    empresa_actual = obtener_empresa(request)

    try:
        producto = Producto.objects.para_empresa(empresa_actual).get(codigo=codigo)
        # Devolver los datos del producto en JSON
        data = {
            'id': producto.pk,
            'codigo': producto.codigo,
            'marca': producto.marca,
            'modelo': producto.modelo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': str(producto.precio),
            'tipo_producto': producto.tipo_producto,
            'linea': producto.linea,
            'sublinea': producto.sublinea,
            'clase': producto.clase,
            'material': producto.material
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        # Si no se encuentra el producto, devolver un error
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)


@control_acceso('Administrador')
def desactivar_producto(request, pk):
    # Obtener la empresa del usuario logueado
    empresa_actual = obtener_empresa(request)
    producto = get_object_or_404(Producto.objects.para_empresa(empresa_actual), pk=pk)
    if request.method == 'GET':
        producto.estado = 'inactivo'  # Cambiar el estado del producto
        producto.save()
        messages.success(request, 'Producto desactivado con éxito.')
        return redirect('lista_productos')
    return redirect('lista_productos')


@control_acceso('Administrador')
def activar_producto(request, pk):
    # Obtener la empresa del usuario logueado
    empresa_actual = obtener_empresa(request)
    producto = get_object_or_404(Producto.objects.para_empresa(empresa_actual), pk=pk)
    if request.method == 'GET':
        producto.estado = 'activo'  # Cambiar el estado del producto
        producto.save()
        messages.success(request, 'Producto activado con éxito.')
        return redirect('lista_productos')
    return redirect('lista_productos')


@control_acceso('Supervisor')
def busqueda_por_modelo(request):
    """
    Vista específica para búsqueda por modelo de producto óptico
    """
    empresa_actual = obtener_empresa(request)
    modelo = request.GET.get('modelo', '')
    productos = None
    
    if modelo:
        productos = Producto.objects.para_empresa(empresa_actual).filter(
            modelo__icontains=modelo.upper()
        ).order_by('modelo', 'marca')
    
    context = {
        'productos': productos,
        'modelo_buscado': modelo
    }
    
    return render(request, 'busqueda_por_modelo.html', context)

