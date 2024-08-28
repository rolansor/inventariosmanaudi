from django.shortcuts import render, redirect, get_object_or_404
from .forms import EmpresaForm
from .models import Empresa


def empresa_list(request):
    # Obtener todas las empresas
    empresas = Empresa.objects.all()

    # Manejo del formulario para crear/editar una empresa
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('empresa_list')
    else:
        form = EmpresaForm()

    return render(request, 'empresas.html', {'empresas': empresas, 'form': form})


# Editar una empresa existente (llamado con ajax u otro mecanismo)
def empresa_edit(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            return redirect('empresa_list')
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'empresas.html', {'form': form, 'empresas': Empresa.objects.all()})


# Eliminar una empresa existente
def empresa_delete(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        return redirect('empresa_list')
    return render(request, 'empresas.html', {'form': EmpresaForm(), 'empresas': Empresa.objects.all()})