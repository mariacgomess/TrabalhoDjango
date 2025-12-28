from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TodoItem, Utilizador, Banco,TipoSangue, Dador, PostoRecolha, Hospital, Doacao, PerfilPosto, PerfilHospital
from .forms import CriarUtilizadorForm, PostoForm, HospitalForm, DadorForm, PedidoForm, PedidoLinhaFormSet
from django.db.models import Sum
from django.contrib.auth import logout as django_logout
from datetime import date

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


def registar_dador(request):
    if request.user.tipo != 'posto':
        return redirect('gestao_dadores')


def registar_dador(request):
    if request.method == 'POST':
        dador_form = DadorForm(request.POST)
        if dador_form.is_valid():
            dador_criado = dador_form.save()
            
            messages.success(request, f"Dador '{dador_criado.nome}' criado com sucesso!")
            return redirect('gestao_dadores')
    else:
        dador_form = DadorForm()

    return render(request, 'registar_dador.html', {
        'entidade_form': dador_form,
        'titulo': "Registar Novo Dador"
    })

def consultar_dador(request):
    dador = None
    search_nif = request.GET.get('nif')

    if search_nif:
        try:
            dador = Dador.objects.get(nif=search_nif)
        except Dador.DoesNotExist:
            messages.warning(request, f"Nenhum dador encontrado com o NIF '{search_nif}'")

    return render(request, 'consultar_dador.html', {
        'dador': dador,
        'titulo': "Dador por NIF"
    })

def atualizar_informacao(request):
    dador = None
    form = None
    #Verificar se foi feita uma pesquisa (pelo GET do URL)
    nif_pesquisa = request.GET.get('nif_search')

    if nif_pesquisa:
        try:
            # Tenta encontrar o dador pelo NIF
            dador = Dador.objects.get(nif=nif_pesquisa)
        except Dador.DoesNotExist:
            messages.error(request, f"Dador com NIF {nif_pesquisa} não encontrado.")
            # Se não encontrar, mantemos dador=None

    # Lógica do Formulário (Só ativa se tivermos encontrado um dador)
    if dador:
        if request.method == 'POST':
            # Se carregou em "Gravar Alterações", atualizamos os dados
            form = DadorForm(request.POST, instance=dador)
            if form.is_valid():
                form.save()
                messages.success(request, f"Dados de {dador.nome} atualizados com sucesso!")
                return redirect('gestao_dadores') # Ou redireciona para onde quiseres
        else:
            # Se acabou de pesquisar, mostramos o formulário preenchido
            form = DadorForm(instance=dador)

    return render(request, 'atualizar_informacao.html', {
        'form': form,
        'dador_encontrado': dador,
        'nif_pesquisa': nif_pesquisa,
        'titulo': "Pesquisar e Atualizar Dador"
    })

def desativar_dador(request):
    dador = None

    if request.method == 'GET':
        search_nif = request.GET.get('nif')
        if search_nif:
            try:
                dador = Dador.objects.get(nif=search_nif)
            except Dador.DoesNotExist:
                messages.warning(
                    request,
                    f"Nenhum dador encontrado com o NIF '{search_nif}'"
                )

    if request.method == 'POST':
        nif = request.POST.get('nif')
        try:
            dador = Dador.objects.get(nif=nif)
            dador.ativo = False
            dador.save()

            messages.success(
                request,
                f"O dador {dador.nome} foi desativado com sucesso!"
            )
            return redirect('gestao_dadores')

        except Dador.DoesNotExist:
            messages.error(request, "Erro ao ativar o dador.")

    return render(request, 'desativar_dador.html', {
        'dador': dador,
        'titulo': "Desativar Dador"
    })

def ativar_dador(request):
    dador = None

    if request.method == 'GET':
        search_nif = request.GET.get('nif')
        if search_nif:
            try:
                dador = Dador.objects.get(nif=search_nif)
            except Dador.DoesNotExist:
                messages.warning(
                    request,
                    f"Nenhum dador encontrado com o NIF '{search_nif}'"
                )

    if request.method == 'POST':
        nif = request.POST.get('nif')
        try:
            dador = Dador.objects.get(nif=nif)
            dador.ativo = True
            dador.save()

            messages.success(
                request,
                f"O dador {dador.nome} foi ativado com sucesso!"
            )
            return redirect('gestao_dadores')

        except Dador.DoesNotExist:
            messages.error(request, "Erro ao ativar o dador.")

    return render(request, 'ativar_dador.html', {
        'dador': dador,
        'titulo': "Ativar Dador"
    })

def listar_dadores(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'listar_dadores.html')

def dadores_tipo_sangue(request):
    dadores_por_grupo = {}
    for codigo, nome_bonito in TipoSangue.choices:
        # Filtramos pelo CÓDIGO (que é o que está guardado na base de dados)
        dadores = Dador.objects.filter(tipo_sangue=codigo)
        dadores_por_grupo[nome_bonito] = dadores
            
    return render(request, 'dadores_tipo_sangue.html', {
        'grupos_sangue': dadores_por_grupo,
        'titulo': "Dadores por Tipo de Sangue"
    })

def dadores_apenas_ativos(request):
    dadores_validos = Dador.objects.filter(ativo=True)
    return render(request, 'dadores_apenas_ativos.html', {
        'dadores': dadores_validos,  # <--- O HTML PROCURA ESTE NOME 'dadores'
        'titulo': "Dadores Ativos"
    })

    hoje = date.today()
    data_limite = date(hoje.year - 18, hoje.month, hoje.day)
    dadores = Dador.objects.filter(dataNascimento__lte=data_limite)

    return render(request, 'dadores_idade_minima.html', {
        'entidades': dadores,
        'titulo': "Dadores registados com idade mínima",
        'tipo_entidade': 'dadores' 
    })

def gestao_hospital(request):
    
    return render(request, 'gestao_hospital.html')

def gestao_pedidos(request):
    return render(request, 'gestao_pedidos.html')

@login_required
def atualizar_hospital(request):
    if request.user.tipo != 'hospital':
        messages.error(request, "Acesso negado.")
        return redirect('home')
    
    # IMPORTANTE: Mude de 'perfilhospital' para 'perfil_hospital' 
    # para coincidir com o related_name do seu models.py
    perfil_hospital = getattr(request.user, 'perfil_hospital', None)
    
    hospital = None
    if perfil_hospital:
        hospital = perfil_hospital.hospital
    else:
        # Se entrar aqui, é porque o utilizador logado não tem um PerfilHospital criado no Admin
        messages.warning(request, "Este utilizador não tem um hospital associado.")

    if request.method == 'POST':
        if hospital:
            form = HospitalForm(request.POST, instance=hospital)
            if form.is_valid():
                form.save()
                messages.success(request, "Informações atualizadas com sucesso!")
                return redirect('pagina_hospital')
        else:
            form = None
    else:
        form = HospitalForm(instance=hospital) if hospital else None

    return render(request, 'atualizar_hospital.html', {
        'hospital': hospital,
        'form': form,
        'titulo': "Atualizar Informações do Hospital"
    })

@login_required
def consultar_hospital(request):
    if request.user.tipo != 'hospital':
        messages.error(request, "Acesso negado.")
        return redirect('home')

    # Usa o related_name 'perfil_hospital' definido no models.py
    perfil = getattr(request.user, 'perfil_hospital', None)
    hospital = perfil.hospital if perfil else None

    # Certifique-se que o nome do .html aqui é igual ao nome do ficheiro na pasta
    return render(request, 'consultar_hospital.html', {
        'hospital': hospital,
        'titulo': "Informações da Instituição"
    })

@login_required
def criar_pedido(request):
    if request.user.tipo != 'hospital':
        return redirect('home')

    # 1. Procuramos o hospital e o banco associado ao utilizador logado
    perfil = getattr(request.user, 'perfil_hospital', None)
    hospital_instancia = perfil.hospital if perfil else None
    # No teu model, o Hospital tem uma ForeignKey para Banco, por isso:
    banco_instancia = hospital_instancia.banco if hospital_instancia else None

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        formset = PedidoLinhaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # 2. Guardamos o Pedido (Cabeçalho)
            pedido = form.save(commit=False)
            pedido.hospital = hospital_instancia
            pedido.banco = banco_instancia  # Preenche o banco automaticamente
            pedido.save()

            # 3. Guardamos as Linhas (Componentes)
            linhas = formset.save(commit=False)
            for linha in linhas:
                # SÓ guarda se preencheram uma quantidade (evita lixo na DB)
                if linha.quantidade and linha.quantidade > 0:
                    linha.pedido = pedido
                    linha.banco = banco_instancia # Importante: o teu model exige banco aqui
                    linha.save()
            
            # 4. Processa remoções feitas no HTML
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "Pedido enviado com sucesso!")
            return redirect('pagina_hospital')
    else:
        form = PedidoForm()
        formset = PedidoLinhaFormSet()

    return render(request, 'criar_pedido.html', {
        'form': form,
        'formset': formset,
        'titulo': "Novo Pedido de Sangue"
    })



