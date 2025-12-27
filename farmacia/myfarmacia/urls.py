from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("todos/", views.todos, name="Todos"),
    path("login/", views.login_view, name="Login"),
    path("admin-dashboard/", views.pagina_admin, name="pagina_admin"),
    path("admin-dashboard/criar-posto/", views.criar_posto_view, name="criar_posto"),
    path("admin-dashboard/criar-hospital/", views.criar_hospital_view, name="criar_hospital"),
    path("admin-dashboard/hospitais/", views.listar_hospitais, name="listar_hospitais"),
    path("admin-dashboard/postos/", views.listar_postos, name="listar_postos"),
    path("admin-dashboard/stock-tipo/", views.stock_por_tipo, name="stock_tipo"),
    path("admin-dashboard/stock-componente/", views.stock_por_componente, name="stock_componente"),
    path('posto/', views.pagina_posto, name='pagina_posto'),

    path('hospital/', views.pagina_hospital, name='pagina_hospital'),
    path('hospital/gestao_hospital/',views.gestao_hospital, name='gestao_hospital'),
    path('hospital/gestao_hospital/atualizar_hospital/',views.atualizar_hospital, name='atualizar_hospital'),
    path('hospital/gestao_pedidos/', views.gestao_pedidos, name='gestao_pedidos'),

    path("logout/", views.logout_view, name="logout"),
    path("posto/gestao_dadores/", views.gestao_dadores, name="gestao_dadores"),
    path("posto/gestao_doacoes/", views.gestao_doacoes, name="gestao_doacoes"),
    path("posto/consultas_estatisticas/", views.consultas_estatisticas, name="consultas_estatisticas"),
    path("posto/gestao_dadores/registar_dador/", views.registar_dador, name="registar_dador"),
    path("posto/gestao_dadores/consultar_dador/", views.consultar_dador, name="consultar_dador"),
    path("posto/gestao_dadores/atualizar_informacao/", views.atualizar_informacao, name="atualizar_informacao"),
    path("posto/gestao_dadores/desativar_dador/", views.desativar_dador, name="desativar_dador"),
    path("posto/gestao_dadores/ativar_dador/", views.ativar_dador, name="ativar_dador"),
    path("posto/gestao_dadores/listar_dadores/", views.listar_dadores, name="listar_dadores"),
    path("posto/gestao_dadores/listar_dadores/dadores_tipo_sangue/", views.dadores_tipo_sangue, name="dadores_tipo_sangue"),
    path("posto/gestao_dadores/listar_dadores/dadores_apenas_ativos/", views.dadores_apenas_ativos, name="dadores_apenas_ativos"),
    path("posto/gestao_doacoes/registar_doacao/", views.registar_doacao, name="registar_doacao"),
    path("posto/gestao_doacoes/historico_dador/", views.historico_dador, name="historico_dador"),
    path("posto/gestao_doacoes/historico_tipo_sanguineo/", views.historico_tipo_sanguineo, name="historico_tipo_sanguineo"),
    path("posto/gestao_doacoes/consultar_doacoes/", views.consultar_doacoes, name="consultar_doacoes")
]