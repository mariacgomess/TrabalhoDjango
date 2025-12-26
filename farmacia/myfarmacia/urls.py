from django.urls import path
from . import views
urlpatterns = [
    path("",views.home, name="home"),
    path("todos/", views.todos, name="Todos"),
    path("login/", views.login_view, name="Login"),
    path('posto/', views.pagina_posto, name='pagina_posto')
]