from rest_framework import serializers
from .models import (
    Utilizador, Banco, PostoRecolha, Hospital, 
    Dador, Doacao, Pedido, LinhaPedido
)

# 1. Serializer para o Banco (A entidade central)
class BancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banco
        fields = '__all__'

# 2. Serializer para Postos de Recolha
class PostoRecolhaSerializer(serializers.ModelSerializer):
    banco_nome = serializers.ReadOnlyField(source='banco.nome')

    class Meta:
        model = PostoRecolha
        fields = ['id', 'nome', 'morada', 'codigoPostal', 'banco', 'banco_nome']

# 3. Serializer para Hospitais
class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'nome', 'telefone', 'morada', 'codigoPostal']

# 4. Serializer para Dadores (Com campos calculados no Model)
class DadorSerializer(serializers.ModelSerializer):
    idade = serializers.ReadOnlyField() 
    pode_doar = serializers.ReadOnlyField()

    class Meta:
        model = Dador
        fields = [
            'id', 'nome', 'nif', 'genero', 'tipo_sangue', 
            'idade', 'peso', 'ativo', 'pode_doar', 'banco'
        ]

# 5. Serializer para Doações
class DoacaoSerializer(serializers.ModelSerializer):
    dador_nome = serializers.ReadOnlyField(source='dador.nome')
    tipo_sangue = serializers.ReadOnlyField(source='dador.tipo_sangue')

    class Meta:
        model = Doacao
        fields = ['id', 'data', 'componente', 'valido', 'dador', 'dador_nome', 'tipo_sangue', 'posto']

# 6. Serializer para as Linhas do Pedido (O que o hospital pede especificamente)
class LinhaPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinhaPedido
        fields = ['id', 'tipo', 'componente', 'quantidade']

# 7. Serializer para Pedidos (Agrupa as linhas do pedido)
class PedidoSerializer(serializers.ModelSerializer):
    itens = LinhaPedidoSerializer(many=True, read_only=True) # Usa o related_name do Model
    hospital_nome = serializers.ReadOnlyField(source='hospital.nome')

    class Meta:
        model = Pedido
        fields = ['id', 'hospital', 'hospital_nome', 'data', 'estado', 'itens']