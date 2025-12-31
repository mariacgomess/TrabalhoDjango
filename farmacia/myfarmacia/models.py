from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date
from django.utils import timezone
from datetime import timedelta

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
    # ... (mantenha os campos conforme o seu código)
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
    def dias_espera_restantes(self):
        #Calcula quanto tempo falta para poder doar novamente.
        ultima_doacao = self.doacoes.order_by('-data').first()
        if not ultima_doacao:
            return 0
        
        hoje = date.today()
        tipo = ultima_doacao.componente.lower()
        
        # Regras de intervalo
        if 'sangue' in tipo:
            intervalo = 90 if self.genero == 'M' else 120
        elif 'plasma' in tipo or 'plaquetas' in tipo:
            intervalo = 14
        else:
            intervalo = 180 # Glóbulos
            
        dias_passados = (hoje - ultima_doacao.data).days
        return max(0, intervalo - dias_passados)

    @property
    def pode_doar(self):
        return self.ativo and self.idade >= 18 and self.peso >= 50 and self.dias_espera_restantes == 0

    def __str__(self):
        # CORREÇÃO: Usar tipo_sangue em vez de tipo
        return f"{self.nome} - {self.nif} - {self.tipo_sangue}"
    
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
    

class EstadoPedido(models.TextChoices):
    ATIVO = "ativo", "Ativo"
    CANCELADO = "cancelado", "Cancelado"
    CONCLUIDO = "concluido", "Concluído"
 
class Pedido(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.DO_NOTHING, related_name='listaPedido')
    data = models.DateField(auto_now_add=True) # Adicione auto_now_add=True
    estado = models.CharField(
        max_length=20, 
        choices=EstadoPedido.choices, 
        default=EstadoPedido.ATIVO
    )
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='listaPedidos')

    def __str__(self):
        return f"{self.hospital} - {self.data} - {self.estado}" 
    

class LinhaPedido(models.Model):
    tipo = models.CharField(max_length=3, choices=TipoSangue.choices, default=TipoSangue.O_NEGATIVO)
    componente = models.CharField(max_length=20, choices=Componente.choices, default=Componente.SANGUE)
    quantidade = models.IntegerField()
    # CORREÇÃO: CASCADE para permitir apagar pedidos no Admin
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
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