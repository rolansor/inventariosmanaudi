from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from productos.models import Producto
from usuarios.models import Empresa, Sucursal
from usuarios.templatetags.tags import control_acceso
from .models import MovimientoInventario
from .forms import MovimientoInventarioForm, ConfirmarRecepcionForm


@control_acceso('Encargado')
def movimiento_inventario(request):
    # Obtener la empresa del usuario logueado
    empresa_actual = request.user.perfil.empresa

    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST, request.FILES)

        # Filtrar los productos y sucursales de la empresa actual para el formulario
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_actual)
        form.fields['sucursal'].queryset = Sucursal.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa_actual)

        if form.is_valid():
            try:
                movimiento = form.save(commit=False)
                movimiento.usuario = request.user  # Asigna el usuario actual
                movimiento.save()  # Guarda en la base de datos
                return redirect('movimiento_inventario')
            except ValueError as e:
                form.add_error(None, str(e))
        else:
            # Si el formulario no es válido, retornar los errores
            return render(request, 'movimiento_inventario.html', {
                'form': form,
                'movimientos': MovimientoInventario.objects.filter(producto__empresa=empresa_actual).order_by('-fecha')[:10]
            })
    else:
        form = MovimientoInventarioForm()

        # Filtrar los productos y sucursales de la empresa actual para el formulario
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_actual)
        form.fields['sucursal'].queryset = Sucursal.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa_actual)

    # Filtrar los movimientos de inventario por la empresa actual
    movimientos = MovimientoInventario.objects.filter(producto__empresa=empresa_actual).order_by('-fecha')[:10]

    return render(request, 'movimiento_inventario.html', {
        'form': form,
        'movimientos': movimientos,
    })


@control_acceso('Encargado')
def confirmar_recepcion(request):
    """Mostrar todos los movimientos de traslado pendientes de confirmación."""
    movimientos_pendientes = MovimientoInventario.objects.filter(
        tipo_movimiento='traslado',
        estado_recepcion='pendiente'
    ).order_by('-fecha')

    return render(request, 'confirmar_recepcion.html', {
        'movimientos_pendientes': movimientos_pendientes,
    })


@control_acceso('Encargado')
def confirmar_recepcion_detalle(request, pk):
    """Permite confirmar la recepción de un traslado en particular."""
    movimiento = get_object_or_404(MovimientoInventario, pk=pk, tipo_movimiento='traslado', estado_recepcion='pendiente')

    if request.method == 'POST':
        form = ConfirmarRecepcionForm(request.POST, instance=movimiento)
        if form.is_valid():
            cantidad_recibida = form.cleaned_data['cantidad_recibida']
            try:
                movimiento.confirmar_recepcion(cantidad_recibida)
                messages.success(request, f'Recepción confirmada para {movimiento.producto.nombre}.')
                return redirect('confirmar_recepcion')
            except ValueError as e:
                form.add_error(None, str(e))
    else:
        form = ConfirmarRecepcionForm(instance=movimiento)

    return render(request, 'confirmar_recepcion_detalle.html', {
        'form': form,
        'movimiento': movimiento,
    })


def movimientos_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    movimientos = MovimientoInventario.objects.filter(producto=producto).order_by('-fecha')

    data = []
    for movimiento in movimientos:
        data.append({
            'sucursal': movimiento.sucursal.nombre,
            'sucursal_destino': movimiento.sucursal_destino.nombre if movimiento.sucursal_destino else 'N/A',
            'tipo_movimiento': movimiento.get_tipo_movimiento_display(),
            'cantidad': movimiento.cantidad,
            'usuario': movimiento.usuario.username,
            'fecha': movimiento.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            'comentario': movimiento.comentario,
        })

    return JsonResponse({'data': data})


def lista_movimientos(request):
    """Vista que muestra todos los movimientos en una tabla, sin usar Ajax."""
    movimientos = MovimientoInventario.objects.all().order_by('-fecha')
    return render(request, 'lista_movimientos.html', {'movimientos': movimientos})


def buscar_productos_por_sucursal(request, empresa_id, sucursal_id):

    # Obtener el filtro de producto opcional
    producto_id = request.GET.get('producto_id', None)

    if sucursal_id == 'all':
        # Si no se seleccionó una sucursal, obtener todos los productos de la empresa
        inventarios = Inventario.objects.filter(sucursal__empresa_id=empresa_id)
    else:
        # Obtener la sucursal y filtrar por ella
        sucursal = get_object_or_404(Sucursal, pk=sucursal_id, empresa_id=empresa_id)
        inventarios = Inventario.objects.filter(sucursal=sucursal)

        # Filtrar opcionalmente por producto
    if producto_id:
        inventarios = inventarios.filter(producto_id=producto_id)

    # Construir la respuesta en formato DataTables
    data = []
    for inventario in inventarios:
        data.append({
            'codigo': inventario.producto.codigo,
            'nombre': inventario.producto.nombre,
            'precio': inventario.producto.precio,
            'cantidad': inventario.cantidad,
            'tipo_producto': inventario.producto.get_tipo_producto_display(),
            'categoria': inventario.producto.categoria.nombre if inventario.producto.categoria else 'Sin categoría',
        })

    return JsonResponse({'data': data})


def productos_sucursales(request):
    empresas = Empresa.objects.all()  # Lista de empresas
    return render(request, 'productos_sucursal.html', {'empresas': empresas})


def sucursales_por_empresa(request, empresa_id):
    sucursales = Sucursal.objects.filter(empresa_id=empresa_id)
    sucursal_data = [{'id': s.id, 'nombre': s.nombre} for s in sucursales]
    return JsonResponse({'sucursales': sucursal_data})


def productos_por_sucursal(request, sucursal_id):
    productos = Producto.objects.filter(inventarios__sucursal_id=sucursal_id).distinct()
    producto_data = [{'id': p.id, 'nombre': p.codigo + ' -- ' + p.nombre} for p in productos]
    return JsonResponse({'productos': producto_data})