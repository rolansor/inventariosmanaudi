from django.db.models import Q
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from productos.models import Producto
from usuarios.models import Sucursal
from usuarios.templatetags.tags import control_acceso
from .models import MovimientoInventario
from .forms import MovimientoInventarioForm, ConfirmarRecepcionForm, ProductoSelectForm, SucursalSelectForm


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


@control_acceso('Encargado')
def movimientos_por_empresa(request):
    empresa = request.user.perfil.empresa  # Asumimos que el perfil del usuario tiene un campo 'empresa'
    sucursales = Sucursal.objects.filter(empresa=empresa)

    movimientos = MovimientoInventario.objects.filter(
        Q(sucursal__in=sucursales) | Q(sucursal_destino__in=sucursales)
    ).order_by('-fecha')

    return render(request, 'movimientos_por_empresa.html', {
        'movimientos': movimientos,
        'empresa': empresa,
    })


@control_acceso('Encargado')
def movimientos_por_sucursal(request):
    """
    Vista que muestra los movimientos de inventario para una sucursal específica.
    Si el usuario pertenece al grupo 'Manaudi', muestra los movimientos de todas las sucursales de la empresa.
    Si es 'Encargado', muestra solo los movimientos de la sucursal actual seleccionada.
    """
    # Obtener la empresa del usuario actual
    empresa = request.user.perfil.empresa  # Asume que el perfil del usuario tiene el campo 'empresa'

    # Inicializar los formularios con las sucursales de la empresa del usuario
    form = SucursalSelectForm(empresa=empresa)
    movimientos = None

    if request.method == 'POST':
        form = SucursalSelectForm(request.POST, empresa=empresa)
        if form.is_valid():
            sucursal = form.cleaned_data['sucursal']
            movimientos = MovimientoInventario.objects.filter(sucursal=sucursal).order_by('-fecha')

    return render(request, 'movimientos_por_sucursal.html', {
        'form': form,
        'movimientos': movimientos,
    })


def movimientos_por_producto(request):
    # Obtener la empresa del usuario actual
    empresa = request.user.perfil.empresa  # Ajustar según cómo se obtenga la empresa en tu proyecto

    # Inicializar el formulario con los productos filtrados por empresa
    form = ProductoSelectForm(empresa=empresa)

    entradas = None
    salidas = None
    traslados = None
    resumen = {
        'entradas': 0,
        'salidas': 0,
        'traslados': 0,
        'total': 0
    }

    if request.method == 'POST':
        form = ProductoSelectForm(request.POST, empresa=empresa)
        if form.is_valid():
            producto = form.cleaned_data['producto']

            # Filtrar los movimientos por tipo
            entradas = MovimientoInventario.objects.filter(producto=producto, tipo_movimiento='entrada').order_by(
                '-fecha')
            salidas = MovimientoInventario.objects.filter(producto=producto, tipo_movimiento='salida').order_by(
                '-fecha')
            traslados = MovimientoInventario.objects.filter(producto=producto, tipo_movimiento='traslado').order_by(
                '-fecha')

            # Calcular los totales
            resumen['entradas'] = entradas.aggregate(total=models.Sum('cantidad'))['total'] or 0
            resumen['salidas'] = salidas.aggregate(total=models.Sum('cantidad'))['total'] or 0
            resumen['traslados'] = traslados.aggregate(total=models.Sum('cantidad'))['total'] or 0

            # Calcular el total disponible
            resumen['total'] = resumen['entradas'] - resumen['salidas']

    return render(request, 'movimientos_por_producto.html', {
        'form': form,
        'entradas': entradas,
        'salidas': salidas,
        'traslados': traslados,
        'resumen': resumen,
    })
