from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TodoItem, Utilizador, Banco, PostoRecolha, Hospital, Doacao, PerfilPosto, PerfilHospital
from .forms import CriarUtilizadorForm, PostoForm, HospitalForm
from django.db.models import Sum
from django.contrib.auth import logout as django_logout

# --- Navegação Base ---
def home(request):
    return render(request, "base.html")

def login_view(request):
    if request.method == 'POST':
        username_recebido = request.POST.get('username')
        password_recebida = request.POST.get('password')

        # O Django verifica se as credenciais existem
        user = authenticate(request, username=username_recebido, password=password_recebida)

        if user is not None:
            login(request, user)
            
            # O sistema decide o destino com base no perfil guardado
            if user.tipo == 'admin':
                return redirect('pagina_admin')
            elif user.tipo == 'hospital':
                return redirect('pagina_hospital')
            elif user.tipo == 'posto':
                return redirect('pagina_posto')
            else:
                # Caso o user não tenha tipo definido (ex: superuser novo)
                messages.warning(request, "Utilizador sem perfil atribuído.")
                return redirect('home')
        else:
            messages.error(request, "Utilizador ou Password incorretos.")

    return render(request, 'login.html')

# --- Painel do Administrador ---
@login_required
def pagina_admin(request):
    # Verificação de segurança: usa 'admin' conforme o seu AbstractUser
    if request.user.tipo != 'admin':
        messages.error(request, "Acesso negado. Apenas administradores podem entrar aqui.")
        return redirect('home')
    
    # Estatísticas para o Dashboard
    stock_total = Doacao.objects.filter(valido=True).count()
    total_postos = PostoRecolha.objects.count()
    total_hospitais = Hospital.objects.count()

    context = {
        'stock_total': stock_total,
        'total_postos': total_postos,
        'total_hospitais': total_hospitais,
    }
    return render(request, 'admin_dashboard.html', context)

# --- Criação de Entidades (Apenas Admin) ---
@login_required
def criar_posto_view(request):
    if request.user.tipo != 'admin':
        return redirect('home')

    if request.method == 'POST':
        user_form = CriarUtilizadorForm(request.POST)
        posto_form = PostoForm(request.POST)

        if user_form.is_valid() and posto_form.is_valid():
            novo_user = user_form.save(commit=False)
            novo_user.tipo = 'posto'
            novo_user.save()

            posto_criado = posto_form.save()
            PerfilPosto.objects.create(user=novo_user, posto=posto_criado)
            
            messages.success(request, f"Posto '{posto_criado.nome}' criado com sucesso!")
            return redirect('pagina_admin')
    else:
        user_form = CriarUtilizadorForm(initial={'tipo': 'posto'})
        posto_form = PostoForm()

    return render(request, 'criar_entidade.html', {
        'user_form': user_form,
        'entidade_form': posto_form,
        'titulo': "Registar Novo Posto de Recolha"
    })

@login_required
def criar_hospital_view(request):
    if request.user.tipo != 'admin':
        return redirect('home')

    if request.method == 'POST':
        user_form = CriarUtilizadorForm(request.POST)
        hosp_form = HospitalForm(request.POST)

        if user_form.is_valid() and hosp_form.is_valid():
            novo_user = user_form.save(commit=False)
            novo_user.tipo = 'hospital'
            novo_user.save()
            
            hospital = hosp_form.save()
            PerfilHospital.objects.create(user=novo_user, hospital=hospital)

            messages.success(request, f"Hospital '{hospital.nome}' criado com sucesso!")
            return redirect('pagina_admin')
    else:
        user_form = CriarUtilizadorForm(initial={'tipo': 'hospital'})
        hosp_form = HospitalForm()

    return render(request, 'criar_entidade.html', {
        'user_form': user_form, 
        'entidade_form': hosp_form,
        'titulo': "Criar Novo Hospital"
    })

# --- Páginas Simples ---

@login_required
def pagina_hospital(request):
    if request.user.tipo != 'hospital':
        return redirect('login')
    return render(request, 'hospital.html')


@login_required
def pagina_posto(request):
    if request.user.tipo != 'posto':
        return redirect('login')
    return render(request, 'posto.html')


def todos(request):
    items = TodoItem.objects.all()
    return render(request, "todos.html", {"todosa": items})


@login_required
def stock_por_tipo(request):
    if request.user.tipo != 'admin':
        return redirect('home')

    tipos = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    combinacoes = []

    for t in tipos:
        total = Doacao.objects.filter(dador__tipo=t, valido=True).count()
        combinacoes.append((t, "Todos os Componentes", total))

    return render(request, 'consultar_stock.html', {
        'titulo': "Stock Total por Grupo Sanguíneo",
        'combinacoes': combinacoes
    })

@login_required
def stock_por_componente(request):
    if request.user.tipo != 'admin':
        return redirect('home')

    # Lista fixa de componentes que queres que apareçam sempre
    componentes_obrigatorios = ["Sangue", "Plasma", "Globulos Vermelhos"]
    
    combinacoes = []

    for comp in componentes_obrigatorios:
        # Contagem real na base de dados
        # Nota: Certifica-te que 'comp' coincide com o que guardas no Model
        total = Doacao.objects.filter(componente__iexact=comp, valido=True).count()
        
        # Adicionamos à lista, mesmo que o total seja 0
        combinacoes.append(("Geral", comp, total))

    return render(request, 'consultar_stock.html', {
        'titulo': "Stock Total por Componente",
        'combinacoes': combinacoes
    })



@login_required
def listar_hospitais(request):
    if request.user.tipo != 'admin':
        return redirect('home')
    
    hospitais = Hospital.objects.all()
    return render(request, 'listar_entidades.html', {
        'entidades': hospitais,
        'titulo': "Hospitais Registados",
        'tipo_entidade': 'hospital' 
    })

@login_required
def listar_postos(request):
    if request.user.tipo != 'admin':
        return redirect('home')
    
    postos = PostoRecolha.objects.all()
    return render(request, 'listar_entidades.html', {
        'entidades': postos,
        'titulo': "Postos de Recolha Registados",
        'tipo_entidade': 'posto' 
    })


def logout_view(request):
    django_logout(request) # Usamos o nome que definimos no import
    return redirect('home')

def gestao_dadores(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'gestao_dadores.html')

def gestao_doacoes(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'gestao_doacoes.html')

def consultas_estatisticas(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'consultas_estatisticas.html')

def gestao_hospital(request):
    
    return render(request, 'gestao_hospital.html')

def gestao_pedidos(request):
    return render(request, 'gestao_pedidos')