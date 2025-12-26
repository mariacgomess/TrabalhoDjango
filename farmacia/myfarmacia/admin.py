from django.contrib import admin
from .models import (
    Banco, Dador, PostoRecolha, Doacao, 
    Hospital, Pedido, LinhaPedido, Utilizador, PerfilPosto, PerfilHospital
)

# --- Configurações Visuais do Painel ---

@admin.register(Dador)
class DadorAdmin(admin.ModelAdmin):
    # Colunas que aparecem na lista de dadores
    list_display = ('nome', 'nif', 'tipo', 'peso', 'ativo', 'ultimaDoacao')
    # Filtros rápidos na barra lateral
    list_filter = ('tipo', 'ativo', 'genero', 'banco')
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
    extra = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'data', 'estado', 'banco')
    list_filter = ('estado', 'banco')
    inlines = [LinhaPedidoInline]

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