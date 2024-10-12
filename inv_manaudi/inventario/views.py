from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

from inv_manaudi.productos.models import Producto
from inv_manaudi.usuarios.models import Empresa, Sucursal
from models import MovimientoInventario
from forms import MovimientoInventarioForm


def movimiento_inventario(request):
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                movimiento = form.save(commit=False)  # No guarda aún en la base de datos
                movimiento.usuario = request.user  # Asigna el usuario actual
                movimiento.save()  # Guarda en la base de datos
                return redirect('movimiento_inventario')
            except ValueError as e:
                form.add_error(None, str(e))
        else:
            return render(request, 'movimiento_inventario.html', {
                'form': form,
                'movimientos': MovimientoInventario.objects.all().order_by('-fecha')[:10]
            })
    else:
        form = MovimientoInventarioForm()

    movimientos = MovimientoInventario.objects.all().order_by('-fecha')[:10]

    return render(request, 'movimiento_inventario.html', {
        'form': form,
        'movimientos': movimientos,
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