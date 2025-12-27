from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilizador, PostoRecolha, Hospital, Banco, Dador

# Formulário para criar a conta de login
class CriarUtilizadorForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Utilizador
        fields = ["username", "email"]

# Formulário para os dados técnicos do Posto
class PostoForm(forms.ModelForm):
    class Meta:
        model = PostoRecolha
        fields = ["nome", "morada", "codigoPostal", "banco"]

# Formulário para os dados técnicos do Hospital
class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ["nome", "telefone", "morada", "codigoPostal", "banco"]

# Formulário para os dados técnicos do Dador
class DadorForm(forms.ModelForm):
    class Meta:
        model = Dador
        fields = ["nome", "dataNascimento", "nif", "genero", "peso", "telefone", "tipo_sangue", "banco"]
        widgets = {
            'dataNascimento': forms.DateInput(attrs={
                'type': 'date',     # Isto ativa o calendário do navegador
                'class': 'form-control' # Opcional: para ficar bonito se usares Bootstrap
            })
        }