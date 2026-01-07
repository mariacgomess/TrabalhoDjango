from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    Banco, Dador, PostoRecolha, Doacao, 
    Hospital, Pedido, LinhaPedido, Utilizador, PerfilPosto, PerfilHospital
)

# --- INLINES (Para edição na mesma página) ---

class PostoInline(admin.TabularInline):
    model = PostoRecolha
    extra = 0
    fields = ('nome', 'morada')

class HospitalInline(admin.TabularInline):
    model = Hospital
    extra = 0
    fields = ('nome', 'telefone')

class LinhaPedidoInline(admin.TabularInline):
    model = LinhaPedido
    extra = 0

# --- CONFIGURAÇÕES DOS MODELOS ---

@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'contar_postos', 'contar_hospitais', 'contar_dadores')
    inlines = [PostoInline, HospitalInline]

    def contar_postos(self, obj): return obj.postos.count()
    contar_postos.short_description = "Nº de Postos"

    def contar_hospitais(self, obj): return obj.hospitais.count()
    contar_hospitais.short_description = "Nº de Hospitais"

    def contar_dadores(self, obj): return obj.dadores.count()
    contar_dadores.short_description = "Total Dadores"

@admin.register(Dador)
class DadorAdmin(admin.ModelAdmin):
    # Organizei a lista para ser mais legível
    list_display = ('nome', 'tipo_sangue', 'nif', 'idade', 'status_aptidao', 'ativo', 'banco')
    list_filter = ('tipo_sangue', 'ativo', 'genero', 'banco')
    search_fields = ('nome', 'nif', 'telefone')
    readonly_fields = ('idade', 'dias_espera_restantes')
    
    # Agrupamento de campos na edição
    fieldsets = (
        ('Informação Pessoal', {'fields': ('nome', 'dataNascimento', 'genero', 'nif', 'telefone')}),
        ('Dados Clínicos', {'fields': ('tipo_sangue', 'peso', 'ativo')}),
        ('Administração', {'fields': ('banco', 'ultimaDoacao')}),
    )

    def status_aptidao(self, obj):
        if not obj:  # segurança extra
            return "-"
        
        pode = getattr(obj, "pode_doar", True)
        dias = getattr(obj, "dias_espera_restantes", 0) or 0
        
        if pode:
            return format_html(
                '<span style="color:white; background:#2ecc71; padding:3px 10px; border-radius:10px; font-weight:bold;">{}</span>',
                "APTO"
            )
        else:
            return format_html(
                '<span style="color:white; background:#e74c3c; padding:3px 10px; border-radius:10px; font-weight:bold;">{} DIAS</span>',
                dias
            )
    
    status_aptidao.short_description = 'Disponibilidade'

@admin.register(Doacao)
class DoacaoAdmin(admin.ModelAdmin):
    list_display = ('data', 'dador_link', 'get_tipo', 'componente', 'valido', 'posto')
    list_filter = ('valido', 'componente', 'posto', 'data')
    list_editable = ('valido',)
    autocomplete_fields = ['dador'] # Ativa busca rápida em listas longas de dadores

    def get_tipo(self, obj): return obj.dador.tipo_sangue
    get_tipo.short_description = 'Grupo'

    def dador_link(self, obj):
        # Link direto para a ficha do dador
        return format_html('<a href="/admin/myfarmacia/dador/{}/change/">{}</a>', obj.dador.id, obj.dador.nome)
    dador_link.short_description = 'Dador'

    def save_model(self, request, obj, form, change):
        # Guarda a doação 
        super().save_model(request, obj, form, change)
        
        # Atualiza o dador automaticamente
        if obj.dador:
            obj.dador.ativo = False
            obj.dador.ultimaDoacao = obj.data
            obj.dador.save()

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'hospital', 'data', 'exibir_estado_colorido', 'banco')
    list_filter = ('estado', 'banco', 'data')
    inlines = [LinhaPedidoInline]
    actions = ['marcar_como_concluido'] # Ação rápida para fechar pedidos

    def exibir_estado_colorido(self, obj):
        colors = {'ativo': '#f39c12', 'concluido': '#27ae60', 'cancelado': '#c0392b'}
        return format_html(
            '<span style="color: {}; font-weight: bold; text-transform: uppercase;">{}</span>',
            colors.get(obj.estado, 'black'),
            obj.get_estado_display()
        )
    exibir_estado_colorido.short_description = 'Estado'

    @admin.action(description="Marcar pedidos selecionados como concluídos")
    def marcar_como_concluido(self, request, queryset):
        queryset.update(estado='concluido')

@admin.register(LinhaPedido)
class LinhaPedidoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'componente', 'quantidade', 'pedido_link')
    list_filter = ('tipo', 'componente', 'banco')

    def pedido_link(self, obj):
        return format_html('<a href="/admin/myfarmacia/pedido/{}/change/">Pedido #{}</a>', obj.pedido.id, obj.pedido.id)
    pedido_link.short_description = 'Ver Pedido'

# --- UTILIZADORES E PERFIS ---

@admin.register(Utilizador)
class UtilizadorAdmin(UserAdmin):
    list_display = ('username', 'email', 'tipo', 'is_staff', 'is_active')
    # Adicionamos o campo 'tipo' aos painéis do UserAdmin original
    fieldsets = UserAdmin.fieldsets + (
        ('Informação de Função', {'fields': ('tipo',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informação de Função', {'fields': ('tipo',)}),
    )

@admin.register(PerfilPosto)
class PerfilPostoAdmin(admin.ModelAdmin):
    list_display = ('user', 'posto', 'get_banco')
    search_fields = ('user__username', 'posto__nome')
    
    def get_banco(self, obj): return obj.posto.banco
    get_banco.short_description = 'Banco Responsável'

@admin.register(PerfilHospital)
class PerfilHospitalAdmin(admin.ModelAdmin):
    list_display = ('user', 'hospital', 'get_banco')
    search_fields = ('user__username', 'hospital__nome')

    def get_banco(self, obj): return obj.hospital.banco
    get_banco.short_description = 'Banco Responsável'

# Modelos simples (Posto e Hospital já registrados via @admin.register ou no fim)
@admin.register(PostoRecolha)
class PostoRecolhaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'morada', 'banco')
    list_filter = ('banco',)
    search_fields = ('nome',)

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'banco')
    list_filter = ('banco',)
    search_fields = ('nome',)