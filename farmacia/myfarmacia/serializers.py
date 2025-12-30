from rest_framework import serializers
from django.db import transaction
from .models import (
    Utilizador, Banco, PostoRecolha, Hospital, 
    Dador, Doacao, Pedido, LinhaPedido, PerfilPosto, PerfilHospital
)

# 1. Utilizador (Essencial para Auth e Perfis)
class UtilizadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilizador
        fields = ['id', 'username', 'email', 'tipo', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = Utilizador.objects.create_user(**validated_data)
        return user

# 2. Banco
class BancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banco
        fields = '__all__'

# 3. Postos de Recolha e Perfil
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

# 4. Hospitais e Perfil
class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'nome', 'telefone', 'morada', 'codigoPostal', 'banco']

class PerfilHospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilHospital
        fields = '__all__'

# 5. Dadores (Com campos de negócio calculados)
class DadorSerializer(serializers.ModelSerializer):
    idade = serializers.ReadOnlyField() 
    pode_doar = serializers.ReadOnlyField()
    dias_espera = serializers.ReadOnlyField(source='dias_espera_restantes')

    class Meta:
        model = Dador
        fields = [
            'id', 'nome', 'nif', 'genero', 'tipo_sangue', 
            'idade', 'peso', 'ativo', 'pode_doar', 'dias_espera', 'banco'
        ]

# 6. Doações
class DoacaoSerializer(serializers.ModelSerializer):
    dador_nome = serializers.ReadOnlyField(source='dador.nome')
    tipo_sangue = serializers.ReadOnlyField(source='dador.tipo_sangue')

    class Meta:
        model = Doacao
        fields = ['id', 'data', 'componente', 'valido', 'dador', 'dador_nome', 'tipo_sangue', 'posto', 'banco']

# 7. Pedidos e Linhas (Com lógica de criação aninhada)
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