from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario, UsuarioPerfil
from django import forms


# Formulario para el registro de usuario
class RegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'telefono', 'direccion', 'password1', 'password2']


# Formulario para la edición de usuario
class EdicionUsuarioForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'telefono', 'direccion']


# Nuevo formulario para UsuarioPerfil
class UsuarioPerfilForm(forms.ModelForm):
    class Meta:
        model = UsuarioPerfil
        fields = ['empresa', 'sucursal']