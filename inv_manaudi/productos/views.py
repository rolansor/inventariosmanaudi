"""
Vistas de la app ``productos``.

Pantallas:

- ``crear_producto``   (Supervisor)  → ``/productos/nuevo/``
- ``lista_productos``  (Auditor)     → ``/productos/lista_productos/`` (DataTables server-side)
- ``busqueda_producto`` (Encargado)  → ``/productos/busqueda/`` (filtro por texto y categoría,
  con botones de editar / activar / desactivar según el rol)
- ``editar_producto``  (Supervisor)  → ``/productos/editar/<pk>/``
- ``desactivar_producto`` / ``activar_producto`` (Manaudi, solo POST)

Endpoints JSON:

- ``bsq_por_codigo``        → datos de un producto por código exacto.
- ``obtener_modelos_unicos`` → lista de modelos para el autocompletado del formulario.

Todas trabajan sobre la empresa activa (``obtener_empresa``).
"""
from django.db import IntegrityError, DataError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from categorias.models import Categoria
from usuarios.templatetags.tags import control_acceso
from usuarios.views import obtener_empresa
from .models import Producto
from .forms import ProductoForm


def _clase_pertenece_a_empresa(clase, empresa):
    """True si la clase es nula o su categoría pertenece a la empresa indicada."""
    return clase is None or clase.subcategoria.categoria.empresa_id == empresa.id


def _mostrar_errores_formulario(request, form):
    """Convierte los errores de campo del formulario en mensajes flash."""
    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f'{field}: {error}')


@control_acceso('Supervisor')
def crear_producto(request):
    """
    Alta de producto en la empresa activa.

    Valida que la clase elegida pertenezca a la empresa y traduce los errores de base
    de datos más comunes (código duplicado, precio fuera de rango) a mensajes legibles.
    Al crear con éxito redirige al listado.
    """
    empresa_actual = obtener_empresa(request)

    if request.method == 'POST':
        form = ProductoForm(request.POST, empresa=empresa_actual)
        if form.is_valid():
            try:
                clase = form.cleaned_data['clase']
                if not _clase_pertenece_a_empresa(clase, empresa_actual):
                    messages.error(request, 'La clase seleccionada no pertenece a tu empresa.')
                    return redirect('crear_producto')

                producto = form.save(commit=False)
                producto.empresa = empresa_actual
                producto.save()

                messages.success(request, 'Producto creado exitosamente.')
                return redirect('lista_productos')

            except IntegrityError as e:
                if 'Duplicate entry' in str(e) or 'unique_codigo_empresa' in str(e):
                    messages.error(request, f'El código {form.cleaned_data["codigo"]} ya existe. Por favor, elige otro.')
                else:
                    messages.error(request, 'Ocurrió un error al crear el producto. Inténtalo de nuevo.')

            except DataError:
                messages.error(request, 'El valor del precio está fuera de los límites permitidos. Intenta un valor menor.')
        else:
            _mostrar_errores_formulario(request, form)
    else:
        form = ProductoForm(empresa=empresa_actual)

    return render(request, 'nuevo_producto.html', {'form': form})


@control_acceso('Auditor')
def lista_productos(request):
    """
    Listado completo de productos de la empresa activa.

    La página inicial solo renderiza la tabla vacía; DataTables pide los datos por
    AJAX a esta misma URL (``?draw=...``) y la vista responde el JSON con paginación,
    búsqueda global y ordenamiento resueltos en el servidor. El botón de editar solo
    se incluye si el usuario pertenece al grupo Supervisor.
    """
    empresa_actual = obtener_empresa(request)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('draw'):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')
        puede_editar = request.user.groups.filter(name='Supervisor').exists()

        # Índice de columna de DataTables → campo de ordenamiento
        columns = ['codigo', 'codigo_auxiliar', 'codigo_ean', 'modelo', 'nombre', 'descripcion', 'precio',
                   'tipo_producto', 'clase', 'estado']

        productos = Producto.objects.para_empresa(empresa_actual).select_related(
            'clase__subcategoria__categoria'
        )
        total_records = productos.count()

        if search_value:
            productos = productos.filter(
                Q(codigo__icontains=search_value) |
                Q(codigo_auxiliar__icontains=search_value) |
                Q(codigo_ean__icontains=search_value) |
                Q(modelo__icontains=search_value) |
                Q(nombre__icontains=search_value) |
                Q(descripcion__icontains=search_value)
            )
        filtered_records = productos.count()

        if order_column < len(columns):
            order_by = columns[order_column]
            if order_dir == 'desc':
                order_by = '-' + order_by
            productos = productos.order_by(order_by)

        productos = productos[start:start + length]

        data = []
        for producto in productos:
            if puede_editar:
                acciones = f'''<div class="btn-group btn-group-sm" role="group">
                    <a href="/productos/editar/{producto.pk}/" class="btn btn-info" title="Editar">
                        <i class="fa fa-edit"></i>
                    </a>
                </div>'''
            else:
                acciones = ''
            data.append([
                producto.codigo,
                producto.codigo_auxiliar or '-',
                producto.codigo_ean or '-',
                producto.modelo or '-',
                producto.nombre,
                producto.descripcion or 'Sin descripción',
                f'${producto.precio}',
                producto.get_tipo_producto_display(),
                f"{producto.clase.subcategoria.categoria.codigo} / {producto.clase.subcategoria.codigo} / {producto.clase.codigo}" if producto.clase else 'Sin clasificación',
                f'<span class="badge bg-{"success" if producto.estado == "activo" else "secondary"}">{producto.get_estado_display()}</span>',
                acciones,
            ])

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })

    return render(request, 'lista_productos.html', {'empresa_actual': empresa_actual})


@control_acceso('Encargado')
def busqueda_producto(request):
    """
    Búsqueda de productos por texto (``q``: código, código auxiliar, EAN, modelo,
    nombre o descripción) y/o por categoría (``categoria``).

    Sin ningún filtro no se muestran resultados. Desde los resultados un Supervisor
    puede editar y un Manaudi activar/desactivar.
    """
    empresa_actual = obtener_empresa(request)
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria')

    productos = Producto.objects.para_empresa(empresa_actual)

    if query:
        productos = productos.filter(
            Q(codigo__icontains=query) |
            Q(codigo_auxiliar__icontains=query) |
            Q(codigo_ean__icontains=query) |
            Q(modelo__icontains=query) |
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )

    if categoria_id:
        try:
            categoria = Categoria.objects.get(id=categoria_id, empresa=empresa_actual)
            productos = productos.filter(clase__subcategoria__categoria=categoria)
        except (Categoria.DoesNotExist, ValueError):
            productos = Producto.objects.none()

    if not query and not categoria_id:
        productos = None

    categorias = Categoria.objects.filter(empresa=empresa_actual)

    return render(request, 'busqueda_producto.html', {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id
    })


@control_acceso('Supervisor')
def editar_producto(request, pk):
    """Edición de un producto de la empresa activa. Tras guardar vuelve a la misma pantalla."""
    empresa_actual = obtener_empresa(request)
    producto = get_object_or_404(Producto.objects.para_empresa(empresa_actual), pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto, empresa=empresa_actual)
        if form.is_valid():
            clase = form.cleaned_data['clase']
            if not _clase_pertenece_a_empresa(clase, empresa_actual):
                messages.error(request, 'La clase seleccionada no pertenece a tu empresa.')
                return redirect('editar_producto', pk=producto.pk)

            form.save()
            messages.success(request, 'Producto actualizado con éxito.')
            return redirect('editar_producto', pk=producto.pk)
        _mostrar_errores_formulario(request, form)
    else:
        form = ProductoForm(instance=producto, empresa=empresa_actual)

    return render(request, 'editar_producto.html', {
        'form': form,
        'producto': producto
    })


@control_acceso('Auditor')
def bsq_por_codigo(request):
    """
    Endpoint JSON: datos de un producto de la empresa activa buscado por código exacto
    (``?codigo=...``). Devuelve 404 si no existe.
    """
    codigo = request.GET.get('codigo')
    empresa_actual = obtener_empresa(request)

    try:
        producto = Producto.objects.para_empresa(empresa_actual).get(codigo=codigo)
        data = {
            'id': producto.pk,
            'codigo': producto.codigo,
            'codigo_auxiliar': producto.codigo_auxiliar,
            'codigo_ean': producto.codigo_ean,
            'modelo': producto.modelo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': str(producto.precio),  # Decimal no es serializable a JSON
            'tipo_producto': producto.tipo_producto,
            'clase_id': producto.clase.pk if producto.clase else None,
            'clase_nombre': f"{producto.clase.subcategoria.categoria.nombre} / {producto.clase.subcategoria.nombre} / {producto.clase.nombre}" if producto.clase else None,
            'estado': producto.estado
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)


def _cambiar_estado_producto(request, pk, nuevo_estado, verbo):
    """Cambia el estado de un producto de la empresa activa (solo POST) y vuelve a la búsqueda."""
    empresa_actual = obtener_empresa(request)
    producto = get_object_or_404(Producto.objects.para_empresa(empresa_actual), pk=pk)
    # Solo por POST (con CSRF): un cambio de estado no debe dispararse con un simple enlace
    if request.method == 'POST':
        producto.estado = nuevo_estado
        producto.save()
        messages.success(request, f'Producto {producto.codigo} {verbo} con éxito.')
    return _volver_a_busqueda(request)


@control_acceso('Manaudi')
def desactivar_producto(request, pk):
    """Pasa el producto a estado ``inactivo`` (los productos nunca se eliminan)."""
    return _cambiar_estado_producto(request, pk, 'inactivo', 'desactivado')


@control_acceso('Manaudi')
def activar_producto(request, pk):
    """Devuelve el producto al estado ``activo``."""
    return _cambiar_estado_producto(request, pk, 'activo', 'activado')


def _volver_a_busqueda(request):
    """Vuelve a la página de búsqueda conservando los filtros si se venía de ella."""
    referer = request.META.get('HTTP_REFERER')
    if referer and 'productos/busqueda' in referer:
        return redirect(referer)
    return redirect('busqueda_producto')


@control_acceso('Supervisor')
def obtener_modelos_unicos(request):
    """
    Endpoint JSON: lista ordenada de modelos distintos de la empresa activa.
    Alimenta el ``<datalist>`` de autocompletado del campo Modelo en el formulario.
    """
    empresa_actual = obtener_empresa(request)

    modelos = (Producto.objects.para_empresa(empresa_actual)
               .exclude(modelo__isnull=True)
               .exclude(modelo__exact='')
               .values_list('modelo', flat=True)
               .distinct()
               .order_by('modelo'))

    return JsonResponse(list(modelos), safe=False)
