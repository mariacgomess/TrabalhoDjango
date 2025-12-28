from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilizador, PostoRecolha, Hospital, Banco, Dador, Doacao
from datetime import date

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
    
    # 1. Validação de Idade (Mínimo 18 anos)
    def clean_dataNascimento(self):
        data_nasc = self.cleaned_data.get('dataNascimento')
        if data_nasc:
            hoje = date.today()
            # Cálculo exato da idade
            idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
            
            if idade < 18:
                raise forms.ValidationError("O dador deve ter pelo menos 18 anos.")
            if idade > 65 and not self.instance.pk:
                raise forms.ValidationError("A idade máxima para o primeiro registo é 65 anos.")
        return data_nasc
    
    # 2. Validação de Peso (Mínimo 50kg)
    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None and peso < 50:
            raise forms.ValidationError("O dador deve pesar pelo menos 50kg para poder doar sangue.")
        return peso
    
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