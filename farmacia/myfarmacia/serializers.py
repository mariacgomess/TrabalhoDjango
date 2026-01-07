from rest_framework import serializers
from django.db import transaction
from datetime import date
from .models import (
    Utilizador, Banco, PostoRecolha, Hospital, 
    Dador, Doacao, Pedido, LinhaPedido, PerfilPosto, PerfilHospital
)

# Utilizador (Essencial para Auth e Perfis)
class UtilizadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilizador
        fields = ['id', 'username', 'email', 'tipo', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = Utilizador.objects.create_user(**validated_data)
        return user

# Banco
class BancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banco
        fields = '__all__'

# Postos de Recolha e Perfil
class PostoRecolhaSerializer(serializers.ModelSerializer):
    banco_nome = serializers.ReadOnlyField(source='banco.nome')

    class Meta:
        model = PostoRecolha
        fields = ['id', 'nome', 'morada', 'codigoPostal', 'banco', 'banco_nome']

class PerfilPostoSerializer(serializers.ModelSerializer):
    user_details = UtilizadorSerializer(source='user', read_only=True)
    posto_nome = serializers.ReadOnlyField(source='posto.nome')

    class Meta:
        model = PerfilPosto
        fields = ['id', 'user', 'user_details', 'posto', 'posto_nome']

# Hospitais e Perfil
class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'nome', 'telefone', 'morada', 'codigoPostal', 'banco']

class PerfilHospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilHospital
        fields = '__all__'

# Dadores 
class DadorSerializer(serializers.ModelSerializer):
    idade = serializers.ReadOnlyField() 
    pode_doar = serializers.ReadOnlyField()
    dias_espera = serializers.ReadOnlyField(source='dias_espera_restantes')

    class Meta:
        model = Dador
        fields = [
            'id', 'nome', 'nif', 'dataNascimento', 'telefone', 'genero', 'tipo_sangue', 
            'idade', 'peso', 'ativo', 'pode_doar', 'dias_espera', 'banco'
        ]

    # Validacao da idade
    def validate_dataNascimento(self, value):
        hoje = date.today()
        # Cálculo preciso da idade
        idade = hoje.year - value.year - ((hoje.month, hoje.day) < (value.month, value.day))

        if idade < 18:
            raise serializers.ValidationError("O dador deve ser maior de idade (mínimo 18 anos).")
        
        if idade > 65:
            raise serializers.ValidationError("A idade limite para doação é 65 anos.")

        return value
    
    # validacao de peso
    def validate_peso(self, value):
        if value < 50.0:
            raise serializers.ValidationError("O dador deve pesar no mínimo 50kg para poder doar.")
        return value
    
    #validacao do nif
    def validate_nif(self, value):
        nif_str = str(value)
        # Verifica formato (9 dígitos)
        if len(nif_str) != 9 or not nif_str.isdigit():
            raise serializers.ValidationError("O NIF deve conter exatamente 9 dígitos numéricos.")

        # Verifica unicidade (se já existe na base de dados)
        if Dador.objects.filter(nif=value).exists():
            raise serializers.ValidationError("Este NIF já se encontra registado no sistema.")
        return value

# Doações
class DoacaoSerializer(serializers.ModelSerializer):
    dador_nome = serializers.ReadOnlyField(source='dador.nome')
    tipo_sangue = serializers.ReadOnlyField(source='dador.tipo_sangue')

    class Meta:
        model = Doacao
        fields = ['id', 'data', 'componente', 'valido', 'dador', 'dador_nome', 'tipo_sangue', 'posto', 'banco']

    def validate_dador(self, value):
        if not value.ativo:
             raise serializers.ValidationError(f"O dador {value.nome} está inativo e não pode doar.")

        return value
    
    def create(self, validated_data):
        # Cria a doação usando a lógica padrão
        doacao = super().create(validated_data)

        # Recupera o dador associado a esta doação
        dador_atual = doacao.dador

        # Atualiza o estado do dador
        dador_atual.ativo = False
        dador_atual.save()

        # Retorna a doação criada
        return doacao

# Pedidos e Linhas 
class LinhaPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinhaPedido
        fields = ['id', 'tipo', 'componente', 'quantidade', 'banco']

class PedidoSerializer(serializers.ModelSerializer):
    itens = LinhaPedidoSerializer(many=True) # Retirado o read_only para permitir criação
    hospital_nome = serializers.ReadOnlyField(source='hospital.nome')

    class Meta:
        model = Pedido
        fields = ['id', 'hospital', 'hospital_nome', 'data', 'estado', 'banco', 'itens']

    def create(self, validated_data):
        # Lógica para criar o Pedido e as Linhas em simultâneo (Atomic Transaction)
        itens_data = validated_data.pop('itens')
        with transaction.atomic():
            pedido = Pedido.objects.create(**validated_data)
            for item in itens_data:
                LinhaPedido.objects.create(pedido=pedido, **item)
        return pedido