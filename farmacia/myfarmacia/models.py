from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date

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

class Dador(models.Model):
    nome = models.CharField(max_length=100)
    dataNascimento = models.DateField()
    nif = models.CharField(max_length=12)
    genero = models.CharField(max_length = 50)
    peso = models.DecimalField(max_digits=5, decimal_places=2)
    telefone = models.CharField(max_length=9)
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
    
    def __str__(self):
        return f"{self.nome} - {self.dataNascimento} - {self.nif}- {self.genero} - {self.peso} - {self.telefone} - {self.tipo} - {self.ativo} - {self.ultimaDoacao}"

class Componente(models.TextChoices):
    SANGUE = "sangue", "Sangue"
    GLOBULOS_VERMELHOS = "globulos", "Globulos Vermelhos"
    PLASMA = "plasma", "plasma"

class PostoRecolha(models.Model):
    nome = models.CharField(max_length=100)
    morada = models.CharField(max_length=100)
    codigoPostal = models.CharField(max_length=8)
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='postos')

    def __str__(self):
        return f"{self.nome} - {self.morada} - {self.codigoPostal}" 
    

class Doacao(models.Model):
    data = models.DateField()
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