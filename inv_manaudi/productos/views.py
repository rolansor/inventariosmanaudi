from django.db import IntegrityError, DataError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from categorias.models import Subcategoria, Categoria, Clase
from usuarios.templatetags.tags import control_acceso
from usuarios.views import obtener_empresa
from .models import Producto
from .forms import ProductoForm


@control_acceso('Supervisor')
def crear_producto(request):
    empresa_actual = obtener_empresa(request)

    if request.method == 'POST':
        form = ProductoForm(request.POST, empresa=empresa_actual)
        if form.is_valid():
            try:
                # Validar que la clase pertenezca a la empresa
                clase = form.cleaned_data['clase']
                if clase and clase.subcategoria.categoria.empresa != empresa_actual:
                    messages.error(request, 'La clase seleccionada no pertenece a tu empresa.')
                    return redirect('crear_producto')
                
                # Crear el producto con los datos del formulario
                producto = form.save(commit=False)
                producto.empresa = empresa_actual
                producto.save()
                
                messages.success(request, 'Producto creado exitosamente.')
                return redirect('lista_productos')
                
            except IntegrityError as e:
                # Detectamos el error por código duplicado
                if 'Duplicate entry' in str(e) or 'unique_codigo_empresa' in str(e):
                    messages.error(request, f'El código {form.cleaned_data["codigo"]} ya existe. Por favor, elige otro.')
                else:
                    messages.error(request, 'Ocurrió un error al crear el producto. Inténtalo de nuevo.')
                    
            except DataError as e:
                messages.error(request, 'El valor del precio está fuera de los límites permitidos. Intenta un valor menor.')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductoForm(empresa=empresa_actual)

    return render(request, 'nuevo_producto.html', {
        'form': form
    })


@control_acceso('Supervisor')
def lista_productos(request):
    # Obtener la empresa del perfil del usuario actual
    empresa_actual = obtener_empresa(request)
    
    # Si es una petición AJAX de DataTables (server-side processing)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('draw'):
        # Parámetros de DataTables
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')
        
        # Mapeo de columnas para ordenamiento
        columns = ['codigo', 'codigo_auxiliar', 'codigo_ean', 'nombre', 'descripcion', 'precio', 
                  'tipo_producto', 'clase', 'estado']
        
        # Query base
        productos = Producto.objects.para_empresa(empresa_actual).select_related(
            'clase__subcategoria__categoria'
        )
        
        # Total de registros sin filtrar
        total_records = productos.count()
        
        # Aplicar búsqueda si existe
        if search_value:
            productos = productos.filter(
                Q(codigo__icontains=search_value) |
                Q(codigo_auxiliar__icontains=search_value) |
                Q(codigo_ean__icontains=search_value) |
                Q(nombre__icontains=search_value) |
                Q(descripcion__icontains=search_value)
            )
        
        # Total de registros filtrados
        filtered_records = productos.count()
        
        # Ordenamiento
        if order_column < len(columns):
            order_by = columns[order_column]
            if order_dir == 'desc':
                order_by = '-' + order_by
            productos = productos.order_by(order_by)
        
        # Paginación
        productos = productos[start:start + length]
        
        # Preparar datos para DataTables
        data = []
        for producto in productos:
            data.append([
                producto.codigo,
                producto.codigo_auxiliar or '-',
                producto.codigo_ean or '-',
                producto.nombre,
                producto.descripcion or 'Sin descripción',
                f'${producto.precio}',
                producto.get_tipo_producto_display(),
                f"{producto.clase.subcategoria.categoria.codigo} / {producto.clase.subcategoria.codigo} / {producto.clase.codigo}" if producto.clase else 'Sin clasificación',
                f'<span class="badge bg-{"success" if producto.estado == "activo" else "secondary"}">{producto.get_estado_display()}</span>',
                f'''<div class="btn-group btn-group-sm" role="group">
                    <a href="/productos/editar/{producto.pk}/" class="btn btn-info" title="Editar">
                        <i class="fa fa-edit"></i>
                    </a>
                </div>'''
            ])
        
        response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        }
        
        return JsonResponse(response)
    
    # Para la carga inicial de la página (no AJAX)
    return render(request, 'lista_productos.html', {'empresa_actual': empresa_actual})


@control_acceso('Supervisor')
def busqueda_producto(request):
    empresa_actual = obtener_empresa(request)
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria')
    
    # Empezar con todos los productos de la empresa
    productos = Producto.objects.para_empresa(empresa_actual)
    
    # Aplicar filtro de búsqueda por texto si existe
    if query:
        productos = productos.filter(
            Q(codigo__icontains=query) | 
            Q(codigo_auxiliar__icontains=query) | 
            Q(codigo_ean__icontains=query) | 
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query)
        )
    
    # Aplicar filtro por categoría si existe
    if categoria_id:
        try:
            # Obtener la categoría seleccionada
            categoria = Categoria.objects.get(id=categoria_id, empresa=empresa_actual)
            
            # Obtener todas las subcategorías asociadas a la categoría seleccionada
            subcategorias = Subcategoria.objects.filter(categoria=categoria)
            
            # Obtener todas las clases de las subcategorías de la categoría seleccionada
            clases = Clase.objects.filter(subcategoria__in=subcategorias)
            
            # Filtrar productos que pertenezcan a esas clases
            productos = productos.filter(clase__in=clases)
            
        except Categoria.DoesNotExist:
            productos = Producto.objects.none()
    
    # Si no hay ningún filtro, no mostrar productos (o mostrar todos, según preferencia)
    if not query and not categoria_id:
        productos = None
    
    # Obtener todas las categorías para el filtro
    categorias = Categoria.objects.filter(empresa=empresa_actual)
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id
    }
    
    return render(request, 'busqueda_producto.html', context)


@control_acceso('Supervisor')
def editar_producto(request, pk=None):
    empresa_actual = obtener_empresa(request)
    # Obtener el producto
    producto = get_object_or_404(Producto.objects.para_empresa(empresa_actual), pk=pk)

    if request.method == 'POST':
        # Procesar la edición del producto usando el form
        form = ProductoForm(request.POST, instance=producto, empresa=empresa_actual)
        if form.is_valid():
            # Validar que la clase pertenezca a la empresa
            clase = form.cleaned_data['clase']
            if clase and clase.subcategoria.categoria.empresa != empresa_actual:
                messages.error(request, 'La clase seleccionada no pertenece a tu empresa.')
                return redirect('editar_producto', pk=producto.pk)
            
            form.save()
            messages.success(request, 'Producto actualizado con éxito.')
            return redirect('editar_producto', pk=producto.pk)
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductoForm(instance=producto, empresa=empresa_actual)

    # Renderizar el formulario para la edición
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
        # Devolver todos los datos del producto en JSON
        data = {
            'id': producto.pk,
            'codigo': producto.codigo,
            'codigo_auxiliar': producto.codigo_auxiliar,
            'codigo_ean': producto.codigo_ean,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': str(producto.precio),  # Convertir Decimal a string para JSON
            'tipo_producto': producto.tipo_producto,
            'clase_id': producto.clase.pk if producto.clase else None,
            'clase_nombre': f"{producto.clase.subcategoria.categoria.nombre} / {producto.clase.subcategoria.nombre} / {producto.clase.nombre}" if producto.clase else None,
            'estado': producto.estado
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
        messages.success(request, f'Producto {producto.codigo} desactivado con éxito.')
        return redirect('busqueda_producto')
    return redirect('busqueda_producto')


@control_acceso('Administrador')
def activar_producto(request, pk):
    # Obtener la empresa del usuario logueado
    empresa_actual = obtener_empresa(request)
    producto = get_object_or_404(Producto.objects.para_empresa(empresa_actual), pk=pk)
    if request.method == 'GET':
        producto.estado = 'activo'  # Cambiar el estado del producto
        producto.save()
        messages.success(request, f'Producto {producto.codigo} activado con éxito.')
        
        # Obtener la URL de referencia para volver a la misma página
        referer = request.META.get('HTTP_REFERER')
        if referer and 'busqueda_producto' in referer:
            return redirect(referer)
        return redirect('busqueda_producto')
    return redirect('busqueda_producto')

