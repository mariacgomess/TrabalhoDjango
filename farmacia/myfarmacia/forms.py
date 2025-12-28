from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilizador, PostoRecolha, Hospital, Banco, Dador
from django.forms import inlineformset_factory
from .models import Pedido, LinhaPedido

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se estivermos a EDITAR (já existe um ID/pk)
        if self.instance and self.instance.pk:
            # Tornamos o campo "Readonly" (O utilizador vê mas não consegue escrever)
            self.fields['nif'].widget.attrs['readonly'] = True
            
            # Mudamos a cor para cinzento para se perceber que está bloqueado
            self.fields['nif'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'
    
    def clean_nif(self):
        nif = self.cleaned_data.get('nif')

        # Se 'self.instance.pk' existir, significa que estamos a EDITAR um dador antigo.
        if self.instance.pk:
            # Se é uma edição, devolvemos logo o NIF original do dador.
            return self.instance.nif

        # --- AQUI É SÓ PARA QUANDO ESTÁS A CRIAR NOVOS ---
        if Dador.objects.filter(nif=nif).exists():
            raise forms.ValidationError("Este NIF já se encontra registado no sistema.")
            
        return nif

# forms.py
# 1. Formulário para o cabeçalho do Pedido (Data)
class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = []

# 2. Formulário para cada linha individual
class LinhaPedidoForm(forms.ModelForm):
    class Meta:
        model = LinhaPedido
        fields = ['tipo', 'componente', 'quantidade']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove os valores padrão para não salvar lixo se o utilizador não preencher
        self.fields['tipo'].initial = None
        self.fields['componente'].initial = None
        self.fields['quantidade'].required = False

# 3. O Formset que une o Pedido às suas várias Linhas
PedidoLinhaFormSet = inlineformset_factory(
    Pedido, 
    LinhaPedido,
    form=LinhaPedidoForm,
    extra=1,              # Começa com apenas 1 linha
    can_delete=True       # Permite apagar linhas
)
