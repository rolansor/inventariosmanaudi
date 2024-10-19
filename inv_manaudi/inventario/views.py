from django.db.models import Q
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from productos.models import Producto
from usuarios.models import Sucursal
from usuarios.templatetags.tags import control_acceso
from .models import MovimientoInventario, Traslado
from .forms import MovimientoInventarioForm, ProductoSelectForm, SucursalSelectForm, \
    TrasladoForm, ConfirmarRecepcionForm


@control_acceso('Encargado')
def movimiento_inventario(request):
    empresa_actual = request.user.perfil.empresa

    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST, request.FILES)
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_actual)
        form.fields['sucursal'].queryset = Sucursal.objects.filter(empresa=empresa_actual)

        if form.is_valid():
            try:
                movimiento = form.save(commit=False)
                movimiento.usuario = request.user
                movimiento.save()
                messages.success(request, 'Movimiento registrado exitosamente.')
                return redirect('movimiento_inventario')
            except ValueError as e:
                form.add_error(None, str(e))
        else:
            messages.error(request, 'Por favor, corrige los errores indicados.')

    else:
        form = MovimientoInventarioForm()
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_actual)
        form.fields['sucursal'].queryset = Sucursal.objects.filter(empresa=empresa_actual)

    movimientos = MovimientoInventario.objects.filter(producto__empresa=empresa_actual).order_by('-fecha')[:10]

    return render(request, 'movimiento_inventario.html', {
        'form': form,
        'movimientos': movimientos,
    })


@control_acceso('Encargado')
def iniciar_traslado(request):
    empresa_actual = request.user.perfil.empresa

    if request.method == 'POST':
        form = TrasladoForm(request.POST)
        # Aplicar filtros de productos y sucursales según la empresa actual
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_origen'].queryset = Sucursal.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa_actual)

        if form.is_valid():
            traslado = form.save(commit=False)  # No se guarda aún en la base de datos
            traslado.usuario = request.user  # Asignar el usuario que inicia el traslado

            try:
                traslado.save()  # Guardar el traslado
                messages.success(request, 'Traslado iniciado exitosamente.')
                return redirect('iniciar_traslado')  # Redireccionar después de guardar
            except ValueError as e:
                form.add_error(None, str(e))  # Manejar errores con un mensaje adecuado
        else:
            messages.error(request, 'Por favor, corrige los errores indicados.')

    else:
        form = TrasladoForm()
        # Filtrar productos y sucursales por la empresa actual
        form.fields['producto'].queryset = Producto.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_origen'].queryset = Sucursal.objects.filter(empresa=empresa_actual)
        form.fields['sucursal_destino'].queryset = Sucursal.objects.filter(empresa=empresa_actual)

    # Obtener los últimos 10 traslados
    traslados_recientes = Traslado.objects.filter(
        producto__empresa=empresa_actual
    ).order_by('-fecha_creacion')[:10]

    return render(request, 'iniciar_traslado.html', {
        'form': form,
        'traslados_recientes': traslados_recientes,  # Pasamos los traslados a la plantilla
    })


@control_acceso('Encargado')
def traslados_pendientes(request):
    """Mostrar todos los traslados pendientes de confirmación que pertenecen a la sucursal del usuario."""
    # Obtener la sucursal del usuario actual
    sucursal_usuario = request.user.perfil.sucursal

    # Filtrar solo los traslados pendientes donde la sucursal destino es la del usuario
    movimientos_pendientes = Traslado.objects.filter(
        estado='pendiente',
        sucursal_destino=sucursal_usuario
    ).order_by('-fecha_creacion')

    return render(request, 'traslados_pendientes.html', {
        'movimientos_pendientes': movimientos_pendientes,
    })


@control_acceso('Encargado')
def confirmar_traslado(request, pk):
    movimiento = get_object_or_404(Traslado, pk=pk, estado='pendiente')
    if request.method == 'POST':
        form = ConfirmarRecepcionForm(request.POST, instance=movimiento)
        if form.is_valid():
            try:
                movimiento.confirmar()
                messages.success(request, 'Recepción confirmada exitosamente.')
                return redirect('traslados_pendientes')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = ConfirmarRecepcionForm(instance=movimiento)

    return render(request, 'confirmar_traslado.html', {
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
