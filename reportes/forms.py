from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class RegistroPersonalizadoForm(UserCreationForm):
    # Definimos los campos extra que pediste
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    email = forms.EmailField(max_length=254, required=True, label='Correo electrónico')
    telefono = forms.CharField(max_length=15, required=True, label='Número de teléfono')

    class Meta:
        model = User
        # NOTA: El modelo User de Django no tiene "teléfono" por defecto, 
        # lo ponemos en el formulario visualmente, pero requerirá un modelo Perfil para guardarse en BD.
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bucle para eliminar los textos de ayuda (help_text) de TODOS los campos
        for field in self.fields.values():
            field.help_text = ''
            field.widget.attrs.update({'class': 'input-estetico'}) # Clase para nuestro CSS


class PerfilUpdateForm(forms.ModelForm):
    # Sobrescribimos los campos para ponerles etiquetas en español
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    email = forms.EmailField(max_length=254, required=True, label='Correo electrónico')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le aplicamos la misma clase CSS que usamos en el registro para que se vea bonito
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input-estetico'})