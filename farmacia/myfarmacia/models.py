from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    completed=models.BooleanField(default=False)

class Banco(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nome}"


class TipoSangue(models.TextChoices):
    A_POSITIVO = "A+", "A positivo"
    A_NEGATIVO = "A-", "A negativo"
    B_POSITIVO = "B+", "B positivo"
    B_NEGATIVO = "B-", "B negativo"
    AB_POSITIVO = "AB+", "AB positivo"
    AB_NEGATIVO = "AB-", "AB negativo"
    O_POSITIVO = "O+", "O positivo"
    O_NEGATIVO = "O-", "O negativo"

class Genero(models.TextChoices):
    FEMININO = "F", "Feminino"
    MASCULINO = "M", "Masculino"

class Dador(models.Model):
    nome = models.CharField(max_length=100)
    dataNascimento = models.DateField()
    nif = models.CharField(max_length=10, unique=True)
    genero = models.CharField(max_length=3, choices=Genero.choices)
    peso = models.DecimalField(max_digits=5, decimal_places=2)
    telefone = models.CharField(max_length=9, unique=True)
    tipo_sangue = models.CharField(max_length=3, choices=TipoSangue.choices, default=TipoSangue.O_NEGATIVO)
    ativo = models.BooleanField(default=True)
    ultimaDoacao = models.DateField(null=True, blank=True)
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='dadores')
    
    @property
    def idade(self):
        if self.dataNascimento:
            today = date.today()
            # Calcula a diferença de anos
            age = today.year - self.dataNascimento.year
            
            # Verifica se já fez anos este ano. Se não, subtrai 1.
            if (today.month, today.day) < (self.dataNascimento.month, self.dataNascimento.day):
                age -= 1
            return age
        
        return None # Retorna nada se não tiver data de nascimento
    
    @property
    def pode_doar(self):
        # Vamos buscar o registo real da última doação na tabela Doacao. O '.first()' pega no mais recente porque ordenamos por '-data'
        ultima_doacao_obj = self.doacoes.order_by('-data').first()

        if not ultima_doacao_obj:
            return True

        hoje = timezone.now().date()
        ultimo_tipo = ultima_doacao_obj.componente.lower() # Converter para minúsculas para facilitar
        ultima_data = ultima_doacao_obj.data
        
        # --- VERIFICAR INTERVALO DE TEMPO ---
        intervalo_dias = 0
        if 'sangue' in ultimo_tipo:
            intervalo_dias = 90 if self.genero == 'M' else 120
            
        elif 'globulos' in ultimo_tipo or 'glóbulos' in ultimo_tipo:
            intervalo_dias = 180 # 6 meses
            
        elif 'plasma' in ultimo_tipo:
            intervalo_dias = 14 # 2 semanas
            
        elif 'plaquetas' in ultimo_tipo:
            intervalo_dias = 14 
            
        else:
            # Se for um tipo desconhecido, usamos uma regra segura padrão (3 meses)
            intervalo_dias = 90

        # Calculamos a data em que fica livre
        data_livre = ultima_data + timedelta(days=intervalo_dias)

        return hoje >= data_livre
    
    def save(self, *args, **kwargs):
        # Verifica a idade usando a propriedade que criámos em cima
        if self.idade is not None and self.idade < 18:
            self.ativo = False  # Força inativo se for menor
        elif not self.pode_doar():
            self.ativo = False
        else:
            self.ativo = True 

        # Grava efetivamente na base de dados
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} - {self.dataNascimento} - {self.nif}- {self.genero} - {self.peso} - {self.telefone} - {self.tipo} - {self.ativo} - {self.ultimaDoacao}"

class Componente(models.TextChoices):
    SANGUE = "sangue", "Sangue"
    GLOBULOS_VERMELHOS = "globulos", "Globulos Vermelhos"
    PLASMA = "plasma", "Plasma"
    PLAQUETAS = "plaquetas", "Plaquetas"

class PostoRecolha(models.Model):
    nome = models.CharField(max_length=100)
    morada = models.CharField(max_length=100)
    codigoPostal = models.CharField(max_length=8)
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='postos')

    def __str__(self):
        return f"{self.nome} - {self.morada} - {self.codigoPostal}" 
    

class Doacao(models.Model):
    data = models.DateField(auto_now_add=True)
    componente = models.CharField(max_length=20, choices=Componente.choices, default=Componente.SANGUE)
    valido = models.BooleanField(default=True)
    dador = models.ForeignKey(Dador, on_delete=models.DO_NOTHING, related_name='doacoes')
    posto = models.ForeignKey(PostoRecolha, on_delete=models.SET_NULL, null=True, related_name='doacoes')
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='doacoes')

    def __str__(self):
        return f"{self.data} - {self.componente} - {self.valido}- {self.dador} - {self.posto}"

class Hospital(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=9)
    morada = models.CharField(max_length=100)
    codigoPostal = models.CharField(max_length=8)
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='hospitais')

    def __str__(self):
        return f"{self.nome} - {self.telefone} - {self.morada} - {self.codigoPostal}" 
    
class Pedido(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.DO_NOTHING, related_name='listaPedido')
    data = models.DateField()
    estado = models.BooleanField(default=True)
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='listaPedidos')

    def __str__(self):
        return f"{self.hospital} - {self.data} - {self.estado}" 
    
class LinhaPedido(models.Model):
    tipo = models.CharField(max_length=3, choices=TipoSangue.choices, default=TipoSangue.O_NEGATIVO)
    componente = models.CharField(max_length=20, choices=Componente.choices, default=Componente.SANGUE)
    quantidade = models.IntegerField()
    pedido = models.ForeignKey(Pedido, on_delete=models.DO_NOTHING,related_name='itens')
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='linhaPedido')

    def __str__(self):
        return f"{self.tipo} - {self.componente} - {self.quantidade} - {self.pedido}" 

class Utilizador(AbstractUser):
    TIPOS_UTILIZADOR = (
        ('posto', 'Posto de Recolha'),
        ('hospital', 'Hospital'),
        ('admin', 'Administrador'),
    )
    tipo = models.CharField(max_length=20, choices=TIPOS_UTILIZADOR, default='posto')

    def __str__(self):
        return f"{self.username} ({self.tipo})"
    

class PerfilPosto(models.Model):
    user = models.OneToOneField(Utilizador, on_delete=models.CASCADE, related_name='perfil_posto')
    posto = models.ForeignKey(PostoRecolha, on_delete=models.CASCADE)

    def __str__(self):
        return f"Perfil de {self.user.username} -> {self.posto.nome}"

class PerfilHospital(models.Model):
    user = models.OneToOneField(Utilizador, on_delete=models.CASCADE, related_name='perfil_hospital')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)

    def __str__(self):
        return f"Perfil de {self.user.username} -> {self.hospital.nome}"