from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TodoItem, Utilizador, Banco,TipoSangue, Dador, PostoRecolha, Hospital, Doacao, PerfilPosto, PerfilHospital, Pedido, LinhaPedido
from .forms import CriarUtilizadorForm, PostoForm, HospitalForm, DadorForm, DoacaoForm
from django.db.models import Sum
from django.contrib.auth import logout as django_logout
from datetime import date
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

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
def pagina_admin(request):
    # Verificação de segurança: usa 'admin' conforme o seu AbstractUser
    if request.user.tipo != 'admin':
        messages.error(request, "Acesso negado. Apenas administradores podem entrar aqui.")
        return redirect('home')
    
    # Estatísticas para o Dashboard
    stock_total = Doacao.objects.filter(valido=True).count()
    total_postos = PostoRecolha.objects.count()
    total_hospitais = Hospital.objects.count()

    # Lógica para contar quantos tipos de sangue estão abaixo do limite (5)
    limite = 5
    num_alertas = 0
    tipos = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    
    for t in tipos:
        if Doacao.objects.filter(dador__tipo_sangue=t, valido=True).count() < limite:
            num_alertas += 1

    context = {
        'stock_total': stock_total,
        'total_postos': total_postos,
        'total_hospitais': total_hospitais,
        'num_alertas': num_alertas,
      
    }

    pedidos_pendentes = Pedido.objects.filter(estado=True).count() # True se pendente
    context['pedidos_pendentes'] = pedidos_pendentes


    return render(request, 'admin_dashboard.html', context)

##extra extra
import csv
from django.http import HttpResponse

@login_required
def exportar_stock_csv(request):
    if request.user.tipo != 'admin':
        return redirect('home')

    # Configuração do Response para CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="stock_sangue_{date.today()}.csv"'

    writer = csv.writer(response)
    # Cabeçalho do ficheiro
    writer.writerow(['ID Doação', 'Tipo Sangue', 'Componente', 'Data Colheita', 'Dador', 'Posto', 'Banco'])

    # Dados das doações válidas
    doacoes = Doacao.objects.filter(valido=True)
    for d in doacoes:
        writer.writerow([
            d.id, 
            d.dador.tipo_sangue, 
            d.get_componente_display(), 
            d.data, 
            d.dador.nome, 
            d.posto.nome if d.posto else "N/A", 
            d.banco.nome
        ])

    return response

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
    # Verificação de segurança: usa 'posto' conforme o seu AbstractUser
    if request.user.tipo != 'posto':
        messages.error(request, "Acesso negado. Apenas postos podem entrar aqui.")
        return redirect('login')
    
    # Estatísticas para o Dashboard
    total_dadores = Dador.objects.count()
    total_doacoes = Doacao.objects.count()

    context = {
        'total_dadores': total_dadores,
        'total_doacoes': total_doacoes,
    }
    return render(request, 'posto.html', context)


def todos(request):
    items = TodoItem.objects.all()
    return render(request, "todos.html", {"todosa": items})


@login_required
def stock_por_tipo(request):
    if request.user.tipo != 'admin':
        return redirect('home')

    tipos = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    combinacoes = []
    valores = []

    for t in tipos:
        total = Doacao.objects.filter(dador__tipo_sangue=t, valido=True).count()
        combinacoes.append((t, "Todos os Componentes", total))
        valores.append(total)

    return render(request, 'consultar_stock.html', {
        'titulo': "Stock Total por Grupo Sanguíneo",
        'combinacoes': combinacoes,
        'labels': tipos, # As labels são os tipos A+, A-, etc.
        'valores': valores
    })

@login_required
def stock_por_componente(request):
    if request.user.tipo != 'admin':
        return redirect('home')

    # Lista fixa de componentes que queres que apareçam sempre
    componentes_obrigatorios = ["Sangue", "Plasma", "Globulos Vermelhos"]
    
    combinacoes = []
    valores = []

    for comp in componentes_obrigatorios:
        # Contagem real na base de dados
        # Nota: Certifica-te que 'comp' coincide com o que guardas no Model
        total = Doacao.objects.filter(componente__iexact=comp, valido=True).count()
        
        # Adicionamos à lista, mesmo que o total seja 0
        combinacoes.append(("Geral", comp, total))
        valores.append(total)

    return render(request, 'consultar_stock.html', {
        'titulo': "Stock Total por Componente",
        'combinacoes': combinacoes,
        'labels': componentes_obrigatorios, # As labels aqui são Sangue, Plasma, etc.
        'valores': valores
    })

@login_required
def stock_critico(request):
    
    if str(request.user.tipo).lower() != 'admin':
        print("DEBUG: Acesso negado, redirecionando...")
        return redirect('home')

    # Define um limite (ex: menos de 5 unidades é crítico)
    limite = 5
    alertas = []
    tipos = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    
    for t in tipos:
        total = Doacao.objects.filter(dador__tipo_sangue=t, valido=True).count()
        if total < limite:
            alertas.append({'tipo': t, 'quantidade': total})
            
    return render(request, 'stock_critico.html', {'alertas': alertas})


@login_required
def listar_hospitais(request):
    if request.user.tipo != 'admin':
        return redirect('home')
    
    hospitais = Hospital.objects.all()
    return render(request, 'listar_entidades.html', {
        'entidades': hospitais,
        'titulo': "Hospitais Registados ",
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


@login_required
def logout_view(request):
    django_logout(request) # Usamos o nome que definimos no import
    return redirect('home')


@login_required
def gestao_dadores(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'gestao_dadores.html')


@login_required
def gestao_doacoes(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'gestao_doacoes.html')


@login_required
def consultas_estatisticas(request):
    # Total no último ano (365 dias)
    um_ano_atras = timezone.now() - timedelta(days=365)
    total_ano = Doacao.objects.filter(data__gte=um_ano_atras).count()

    # Totais Gerais
    total_geral = Doacao.objects.count()
    total_dadores = Dador.objects.filter(ativo=True).count()

    # Válidas vs Inválidas
    total_validas = Doacao.objects.filter(valido=True).count()
    
    # Agrupamento por Tipo de Sangue- Isto cria uma lista: [{'dador__tipo_sangue': 'A+', 'total': 15}, {'dador__tipo_sangue': 'O-', 'total': 3}]
    por_tipo = Doacao.objects.values('dador__tipo_sangue').annotate(qtd=Count('id')).order_by('dador__tipo_sangue')
    for item in por_tipo:
        if total_geral > 0:
            item['percentagem'] = round((item['qtd'] / total_geral) * 100, 1)
        else:
            item['percentagem'] = 0

    return render(request, 'consultas_estatisticas.html', {
        'total_ano': total_ano,
        'total_geral': total_geral,
        'total_dadores': total_dadores,
        'total_validas': total_validas,
        'por_tipo': por_tipo,
        'titulo': "Estatísticas e Consultas"
    })



@login_required
def gestao_hospital(request):
    
    return render(request, 'gestao_hospital.html')


@login_required
def gestao_pedidos(request):
    return render(request, 'gestao_pedidos.html')



@login_required
def registar_dador(request):
    if request.user.tipo != 'posto':
        messages.error(request, "Acesso negado. Apenas funcionários de Postos podem registar dadores.")
        return redirect('gestao_dadores') 
    
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

@login_required
def consultar_dador(request):
    dador = None
    search_nif = request.GET.get('nif')
    if search_nif:
        dador = Dador.objects.filter(nif=search_nif).first()
        if not dador:
            messages.warning(request, f"NIF '{search_nif}' não encontrado.")
    return render(request, 'consultar_dador.html', {'dador': dador, 'titulo': "Dador por NIF"})


@login_required
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


@login_required
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


@login_required
def ativar_dador(request):
    dador = None

    if request.method == 'GET':
        search_nif = request.GET.get('nif')
        if search_nif:
            try:
                dador = Dador.objects.get(nif=search_nif)
            except Dador.DoesNotExist:
                messages.warning(request,f"Nenhum dador encontrado com o NIF '{search_nif}'")

    if request.method == 'POST':
        nif = request.POST.get('nif')
        try:
            dador = Dador.objects.get(nif=nif)
            if dador.idade < 18:
                messages.error(request, f"Impossível ativar: {dador.nome} ainda é menor de idade ({dador.idade} anos).")
                return redirect('gestao_dadores')
            
            dador.ativo = True
            dador.save()

            messages.success(request, f"O dador {dador.nome} foi ativado com sucesso!")
            return redirect('gestao_dadores')

        except Dador.DoesNotExist:
            messages.error(request, "Erro ao ativar o dador.")

    return render(request, 'ativar_dador.html', {
        'dador': dador,
        'titulo': "Ativar Dador"
    })


@login_required
def listar_dadores(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'listar_dadores.html')


@login_required
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


@login_required
def dadores_apenas_ativos(request):
    dadores_validos = Dador.objects.filter(ativo=True)
    return render(request, 'dadores_apenas_ativos.html', {
        'dadores': dadores_validos,  # <--- O HTML PROCURA ESTE NOME 'dadores'
        'titulo': "Dadores Ativos"
    })



@login_required
def gestao_hospital(request):
    
    return render(request, 'gestao_hospital.html')



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
def registar_doacao(request):
    if request.user.tipo != 'posto':
        messages.error(request, "Acesso negado.")
        return redirect('home') 
    
    # Inicializamos a variável como None para evitar o erro de "not defined"
    doacao_criada = None 

    if request.method == 'POST':
        doacao_form = DoacaoForm(request.POST)
        if doacao_form.is_valid():
            dador = doacao_form.cleaned_data['nif_dador']
            dador.ativo = False
            dador.ultimaDoacao = timezone.now().date()
            dador.save()
            doacao_criado = doacao_form.save()
            ultima = Doacao.objects.filter(dador=dador).order_by('-data').first()

            
            if ultima:
                hoje = date.today()
     
                dias_passados = (hoje - ultima.data).days
                intervalo = 120 if dador.genero == 'Feminino' else 90

                if dias_passados < intervalo:
                    proxima_data = ultima.data + timedelta(days=intervalo)
                    messages.error(request, f"O dador {dador.nome} ainda não pode doar. Próxima data possível: {proxima_data}")
                    return render(request, 'registar_doacao.html', {
                        'entidade_form': doacao_form,
                        'titulo': "Registar Nova Doação"
                    })
            
            doacao_criada = doacao_form.save()
            
            messages.success(request, f"Doação de {dador.nome} registada com sucesso!")
            return redirect('gestao_doacoes')
        else:
            messages.error(request, "Erro ao validar os dados do formulário.")
    else:
        doacao_form = DoacaoForm()

    return render(request, 'registar_doacao.html', {
        'entidade_form': doacao_form,
        'titulo': "Registar Nova Doação",
        'doacao': doacao_criada  # Passamos a variável (mesmo que seja None)
    })

def historico_dador(request):
    dador_encontrado = None
    lista_doacoes = []
    search_nif = request.GET.get('nif')

    if search_nif:
        try:
            dador_encontrado = Dador.objects.get(nif=search_nif)
            lista_doacoes = Doacao.objects.filter(dador=dador_encontrado).order_by('-data')
        except Dador.DoesNotExist:
            messages.warning(request, f"Nenhum dador encontrado com o NIF '{search_nif}'")

    return render(request, 'historico_dador.html', {
        'dador': dador_encontrado,
        'doacoes': lista_doacoes,
        'nif_pesquisa': search_nif,
        'titulo': "Histórico de Doações"
    })

def historico_tipo_sanguineo(request):
    lista_doacoes = []
    search_tipo = request.GET.get('tipo_sangue')

    if search_tipo:
        lista_doacoes = Doacao.objects.filter(dador__tipo_sangue=search_tipo).order_by('-data')
        if not lista_doacoes.exists():
            messages.warning(request, f"Não existem doações registadas para o tipo  '{search_tipo}'.")

    return render(request, 'historico_tipo_sanguineo.html', {
        'doacoes': lista_doacoes,
        'tipo_pesquisa': search_tipo,
        'titulo': "Histórico por Tipo Sanguíneo"
    })

def consultar_doacoes(request):
    doacoes = Doacao.objects.all().order_by('-data')

    return render(request, 'consultar_doacoes.html', {
        'doacoes': doacoes,
        'titulo': "Consultar doações"
    })



################################################################################################
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    DadorSerializer, DoacaoSerializer, HospitalSerializer, 
    PedidoSerializer, BancoSerializer, PostoRecolhaSerializer, LinhaPedidoSerializer
)

# --- VIEWSETS PARA API (REST FRAMEWORK) ---

class BancoViewSet(viewsets.ModelViewSet):
    queryset = Banco.objects.all()
    serializer_class = BancoSerializer
    permission_classes = [IsAuthenticated]

class PostoRecolhaViewSet(viewsets.ModelViewSet):
    queryset = PostoRecolha.objects.all()
    serializer_class = PostoRecolhaSerializer
    permission_classes = [IsAuthenticated]

class DadorViewSet(viewsets.ModelViewSet):
    queryset = Dador.objects.all()
    serializer_class = DadorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Se quiseres filtrar dadores por banco do utilizador logado:
        user = self.request.user
        if user.tipo == 'posto':
            return Dador.objects.filter(banco=user.perfil_posto.posto.banco)
        return Dador.objects.all()

class DoacaoViewSet(viewsets.ModelViewSet):
    queryset = Doacao.objects.all()
    serializer_class = DoacaoSerializer
    permission_classes = [IsAuthenticated]

class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    permission_classes = [IsAuthenticated]

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        #Hospital só vê os seus pedidos
        if user.tipo == 'hospital':
            return Pedido.objects.filter(hospital=user.perfil_hospital.hospital)
        return Pedido.objects.all()

    def perform_create(self, serializer):
        # Se for um hospital a criar, associa automaticamente o hospital dele ao pedido
        if self.request.user.tipo == 'hospital':
            serializer.save(hospital=self.request.user.perfil_hospital.hospital)
        else:
            serializer.save()

class LinhaPedidoViewSet(viewsets.ModelViewSet):
    queryset = LinhaPedido.objects.all()
    serializer_class = LinhaPedidoSerializer
    permission_classes = [IsAuthenticated]
