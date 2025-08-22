from django.db.models import Sum, F, Count, DecimalField, ExpressionWrapper
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import render
from inventario.models import MovimientoInventario, Inventario
from productos.models import Producto
from usuarios.models import Sucursal
from usuarios.views import obtener_empresa
from usuarios.templatetags.tags import control_acceso


@control_acceso('Supervisor')
def reporte_movimientos_dia(request):
    # Obtener empresa del usuario
    empresa_actual = obtener_empresa(request)
    
    # Obtener la fecha de hoy
    fecha = now() - timedelta(days=0)
    inicio_dia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Filtrar los movimientos del día actual por empresa
    movimientos = MovimientoInventario.objects.filter(
        fecha__gte=inicio_dia, 
        fecha__lte=fin_dia,
        producto__empresa=empresa_actual
    )

    # Agrupar movimientos por usuario y resumir cantidades
    resumen_por_usuario = movimientos.values('usuario__username').annotate(
        total_cantidad=Sum('cantidad'),
        total_movimientos=Count('id')
    )

    # Agrupar movimientos por tipo y resumir cantidades
    resumen_por_tipo = movimientos.values('tipo_movimiento').annotate(
        total_cantidad=Sum('cantidad'),
        total_movimientos=Count('id')
    )

    # Detalles completos para la tabla
    detalles_movimientos = movimientos.select_related('producto', 'sucursal').order_by('-fecha')

    return render(request, 'reporte_movimientos_dia.html', {
        'fecha_hoy': fecha,
        'resumen_por_usuario': resumen_por_usuario,
        'resumen_por_tipo': resumen_por_tipo,
        'detalles_movimientos': detalles_movimientos,
        'empresa': empresa_actual,
    })


@control_acceso('Supervisor')
def reporte_inventario_valorizado(request):
    """
    Reporte de inventario valorizado mostrando el valor total del inventario
    por producto, sucursal y categoría.
    """
    empresa_actual = obtener_empresa(request)
    
    # Obtener inventarios con stock > 0
    inventarios = Inventario.objects.filter(
        producto__empresa=empresa_actual,
        cantidad__gt=0
    ).select_related(
        'producto', 
        'producto__clase__subcategoria__categoria',
        'sucursal'
    ).annotate(
        valor_total=ExpressionWrapper(
            F('cantidad') * F('producto__precio'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('sucursal__nombre', 'producto__nombre')
    
    # Calcular totales por sucursal
    totales_por_sucursal = inventarios.values(
        'sucursal__id', 
        'sucursal__nombre'
    ).annotate(
        total_productos=Count('producto', distinct=True),
        total_unidades=Sum('cantidad'),
        valor_total=Sum(
            ExpressionWrapper(
                F('cantidad') * F('producto__precio'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
    ).order_by('sucursal__nombre')
    
    # Calcular totales por categoría
    totales_por_categoria = inventarios.values(
        'producto__clase__subcategoria__categoria__id',
        'producto__clase__subcategoria__categoria__nombre'
    ).annotate(
        total_productos=Count('producto', distinct=True),
        total_unidades=Sum('cantidad'),
        valor_total=Sum(
            ExpressionWrapper(
                F('cantidad') * F('producto__precio'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
    ).order_by('-valor_total')
    
    # Productos con mayor valor en inventario
    productos_top = inventarios.values(
        'producto__id',
        'producto__codigo',
        'producto__nombre'
    ).annotate(
        stock_total=Sum('cantidad'),
        precio=F('producto__precio'),
        valor_total=Sum(
            ExpressionWrapper(
                F('cantidad') * F('producto__precio'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
    ).order_by('-valor_total')[:10]
    
    # Productos con stock bajo
    productos_stock_bajo = Inventario.objects.filter(
        producto__empresa=empresa_actual,
        cantidad__lte=F('stock_minimo')
    ).select_related('producto', 'sucursal').order_by('cantidad')
    
    # Calcular totales generales
    total_general = inventarios.aggregate(
        total_productos=Count('producto', distinct=True),
        total_unidades=Sum('cantidad'),
        valor_total=Sum(
            ExpressionWrapper(
                F('cantidad') * F('producto__precio'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
    )
    
    return render(request, 'reporte_inventario_valorizado.html', {
        'inventarios': inventarios,
        'totales_por_sucursal': totales_por_sucursal,
        'totales_por_categoria': totales_por_categoria,
        'productos_top': productos_top,
        'productos_stock_bajo': productos_stock_bajo,
        'total_general': total_general,
        'empresa': empresa_actual,
        'fecha_reporte': now()
    })