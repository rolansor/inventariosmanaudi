from django.db.models import Sum, F, Count
from django.utils.timezone import now
from datetime import timedelta
from django.shortcuts import render
from inventario.models import MovimientoInventario
from usuarios.templatetags.tags import control_acceso


@control_acceso('Supervisor')
def reporte_movimientos_dia(request):
    # Obtener la fecha de hoy
    fecha = now() - timedelta(days=0)
    inicio_dia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Filtrar los movimientos del día actual
    movimientos = MovimientoInventario.objects.filter(fecha__gte=inicio_dia, fecha__lte=fin_dia)

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
    })