from django.contrib import admin
from .models import (
    Banco, Dador, PostoRecolha, Doacao, 
    Hospital, Pedido, LinhaPedido, Utilizador, PerfilPosto, PerfilHospital
)

# --- Configurações Visuais do Painel ---

@admin.register(Dador)
class DadorAdmin(admin.ModelAdmin):
    # Colunas que aparecem na lista de dadores
    list_display = ('nome', 'nif', 'tipo_sangue', 'peso', 'ativo', 'ultimaDoacao')
    # Filtros rápidos na barra lateral
    list_filter = ('tipo_sangue', 'ativo', 'genero', 'banco')
    # Barra de pesquisa para encontrar dadores rapidamente
    search_fields = ('nome', 'nif')
    # Organização por data
    date_hierarchy = 'ultimaDoacao'

@admin.register(Doacao)
class DoacaoAdmin(admin.ModelAdmin):
    list_display = ('data', 'dador', 'componente', 'valido', 'posto')
    list_filter = ('valido', 'componente', 'posto', 'data')
    # Permite editar o campo "valido" diretamente na lista sem abrir o registo
    list_editable = ('valido',)

# Permite gerir os itens do pedido (Linhas) dentro da página do Pedido
class LinhaPedidoInline(admin.TabularInline):
    model = LinhaPedido
    extra = 0 # Alterado para 0 para um visual mais limpo

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # Mudámos 'estado' para 'exibir_estado_bonito' para usar a nossa função
    list_display = ('id', 'hospital', 'data', 'exibir_estado_bonito', 'banco')
    list_filter = ('estado', 'banco')
    inlines = [LinhaPedidoInline]

    def exibir_estado_bonito(self, obj):
        # Esta função limpa os valores "1" ou "0" antigos e mostra o texto das choices
        return obj.get_estado_display()
    
    exibir_estado_bonito.short_description = 'Estado Atual'

@admin.register(PostoRecolha)
class PostoRecolhaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'morada', 'banco')
    search_fields = ('nome',)

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'banco')

# Registar os restantes modelos
admin.site.register(Utilizador)
admin.site.register(Banco)
admin.site.register(PerfilPosto)
admin.site.register(PerfilHospital)