from django.shortcuts import render, HttpResponse
from .models import TodoItem
from .models import Utilizador
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

# Create your views here.
def home(request):
    #return HttpResponse("hello world!")
    return render(request, "base.html") 
def todos(request):
    items= TodoItem.objects.all()
    return render (request, "todos.html", {"todos":items})
def login_view(request):
    if request.method == 'POST':
        tipo_recebido = request.POST.get('tipo')
        username_recebido = request.POST.get('username')           
        password_recebida = request.POST.get('password')
        user = authenticate(request, username=username_recebido, password=password_recebida)

        if user is not None:
            # O utilizador e a password estão corretos.
            if user.tipo == tipo_recebido: 
                login(request, user) # Faz o login oficial (cria a sessão)
                
                # Redireciona consoante o tipo, se quiseres
                if user.tipo == 'admin':
                    return redirect('pagina_admin')
                elif user.tipo == 'hospital':
                    return redirect('pagina_hospital')
                else:
                    return redirect('pagina_posto')
            else:
                # O utilizador existe, mas escolheu o tipo errado no dropdown
                messages.error(request, f"Este utilizador não é do tipo {tipo_recebido}")
        else:
            # Username ou Password errados
            messages.error(request, "Username ou Password inválidos")
    items= Utilizador.objects.all()
    return render(request, 'login.html')

def pagina_posto(request):
    return render(request, 'posto.html')
