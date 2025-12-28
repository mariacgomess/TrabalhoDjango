from django import forms
from django.contrib.auth.forms import UserCreationForm
<<<<<<< HEAD
from .models import Utilizador, PostoRecolha, Hospital, Banco, Dador
from django.forms import inlineformset_factory
from .models import Pedido, LinhaPedido
=======
from .models import Utilizador, PostoRecolha, Hospital, Banco, Dador, Doacao
from datetime import date
>>>>>>> 4d2ea59594878bfe2252ed6ef14e654cbb6d6927

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
            # Calendário Prático: Ativa o seletor visual de datas do navegador
            'dataNascimento': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'max': date.today().isoformat() # Impede selecionar datas no futuro
            }),
            # Peso Interativo: Aumenta de 0.1 em 0.1 (ex: 70.1, 70.2)
            'peso': forms.NumberInput(attrs={
                'step': '0.1', 
                'min': '0', 
                'class': 'form-control',
                'placeholder': 'Ex: 75.5'
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
    
    def clean(self):
        cleaned_data = super().clean()
        data_nasc = cleaned_data.get('dataNascimento')
        peso = cleaned_data.get('peso')

        if data_nasc:
            # Criamos uma instância temporária para usar a @property idade do Model
            temp_dador = Dador(dataNascimento=data_nasc)
            idade = temp_dador.idade
            if temp_dador.idade < 18:
                self.add_error('dataNascimento', "O dador deve ter pelo menos 18 anos.")
            if not self.instance.pk and idade > 65:
                self.add_error('dataNascimento', "A idade máxima para o primeiro registo é 65 anos.")
            
        
        if peso is not None and peso < 50:
            self.add_error('peso', "O dador deve pesar pelo menos 50kg para poder doar.")
            
        return cleaned_data
    
    def clean_nif(self):
        nif = self.cleaned_data.get('nif')

        # Se 'self.instance.pk' existir, significa que estamos a EDITAR um dador antigo.
        if self.instance.pk:
            # Se é uma edição, devolvemos logo o NIF original do dador.
            return self.instance.nif
        
        # Verifica se tem 9 dígitos
        if nif and (len(nif) != 9 or not nif.isdigit()):
            raise forms.ValidationError("O NIF deve conter exatamente 9 dígitos numéricos.")

        # --- AQUI É SÓ PARA QUANDO ESTÁS A CRIAR NOVOS ---
        if Dador.objects.filter(nif=nif).exists():
            raise forms.ValidationError("Este NIF já se encontra registado no sistema.")
            
        return nif
<<<<<<< HEAD

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
=======
    
class DoacaoForm(forms.ModelForm):
    # Criamos um campo extra que NÃO existe no modelo Doacao
    nif_dador = forms.CharField(
        label="NIF do Dador",
        max_length=9,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 123456789'})
    )

    class Meta:
        model = Doacao
        # REMOVEMOS o campo 'dador' desta lista para não aparecer o dropdown
        fields = ["componente", "valido", "posto", "banco"] # Podes adicionar data/hora se precisares

    # Validar se o NIF existe e se o dador é válido
    def clean_nif_dador(self):
        nif = self.cleaned_data.get('nif_dador')
        
        # Tenta encontrar o dador na BD
        try:
            dador = Dador.objects.get(nif=nif)
        except Dador.DoesNotExist:
            raise forms.ValidationError("Não existe nenhum dador registado com esse NIF.")

        # Verifica se o dador está ativo
        if not dador.ativo:
            raise forms.ValidationError(f"O dador {dador.nome} está inativo e não pode doar.")

        # Se tudo estiver bem, devolvemos o OBJETO Dador
        return dador

    # Sobrescrever o Save para ligar as peças
    def save(self, commit=True):
        # Cria a doação na memória mas não grava ainda (commit=False)
        doacao = super().save(commit=False)
        
        # Vamos buscar o Dador que encontrámos na função clean_nif_dador e associamos à doação manualmente
        doacao.dador = self.cleaned_data['nif_dador']

        if commit:
            doacao.save()
        return doacao
>>>>>>> 4d2ea59594878bfe2252ed6ef14e654cbb6d6927
