from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario

class RegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'telefono', 'direccion', 'password1', 'password2']

class EdicionUsuarioForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'telefono', 'direccion']
