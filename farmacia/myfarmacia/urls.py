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
    path("logout/", views.logout_view, name="logout"),
    path("posto/gestao_dadores/", views.gestao_dadores, name="gestao_dadores"),
    path("posto/gestao_doacoes/", views.gestao_doacoes, name="gestao_doacoes"),
    path("posto/consultas_estatisticas/", views.consultas_estatisticas, name="consultas_estatisticas"),
]