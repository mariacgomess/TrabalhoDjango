
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Utilizador, Banco,TipoSangue, Dador, PostoRecolha, Hospital, Doacao, PerfilPosto, PerfilHospital, Pedido, LinhaPedido
from .forms import CriarUtilizadorForm, PostoForm, HospitalForm, DadorForm, DoacaoForm, PedidoForm, PedidoLinhaFormSet
from django.db.models import Sum
from django.contrib.auth import logout as django_logout
from datetime import date
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    DadorSerializer, DoacaoSerializer, HospitalSerializer, 
    PedidoSerializer, BancoSerializer, PostoRecolhaSerializer, LinhaPedidoSerializer
)
import csv
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Pedido # Substitua pelo nome correto do seu modelo
from django.contrib import messages



# --- Navegação Base ---
def home(request):
    return render(request, "base.html")

def ajuda(request):
    return render(request, "ajuda.html")

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
    if request.user.tipo != 'admin':
        return redirect('home')
    
    # KPIs Básicos
    stock_total = Doacao.objects.filter(valido=True).count()
    total_postos = PostoRecolha.objects.count()
    total_hospitais = Hospital.objects.count()
    pedidos_pendentes_contagem = Pedido.objects.filter(estado='ativo').count()

    # Lógica de Alertas Unificada
    limite = 5
    num_alertas = 0
    perigo_critico = False
    
    tipos = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    componentes = ["Sangue", "Plasma", "Globulos Vermelhos"]
    
    for t in tipos:
        for comp in componentes:
            total = Doacao.objects.filter(
                dador__tipo_sangue=t, 
                componente__iexact=comp, 
                valido=True
            ).count()
            
            if total < limite:
                num_alertas += 1
                if total == 0:
                    perigo_critico = True

    context = {
        'stock_total': stock_total,
        'total_postos': total_postos,
        'total_hospitais': total_hospitais,
        'num_alertas': num_alertas,
        'perigo_critico': perigo_critico,
        'pedidos_pendentes': pedidos_pendentes_contagem,
        'nome_banco': Banco.objects.first().nome if Banco.objects.exists() else "Banco Central",
        'ultimo_login': request.user.last_login, # Pega na data real do último login

}
    return render(request, 'admin_dashboard.html', context)

@login_required
def listar_pedidos_admin(request):
    # O Admin vê TUDO de TODOS os hospitais
    pedidos = Pedido.objects.all().prefetch_related('itens').order_by('-data')
    return render(request, 'listar_pedidos_admin.html', {
        'pedidos': pedidos,
        'titulo': "Gestão Global de Pedidos"
    })

@login_required
def rejeitar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    # O Admin pode mudar o estado sem a restrição de "ser dono" do pedido
    pedido.estado = "rejeitado" 
    pedido.save()
    messages.success(request, f"Pedido #{pedido.id} foi rejeitado pela administração.")
    return redirect('listar_pedidos_admin')


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

    # 1. Identificar instâncias
    perfil = getattr(request.user, 'perfil_hospital', None)
    hospital_instancia = perfil.hospital if perfil else None
    banco_instancia = hospital_instancia.banco if hospital_instancia else None

    # 2. Cálculos de Stock e Pedidos
    qtd_stock_global = 0
    if banco_instancia:
        qtd_stock_global = Doacao.objects.filter(banco=banco_instancia, valido=True).count()

    qtd_pedidos_meus = 0
    if hospital_instancia:
        qtd_pedidos_meus = Pedido.objects.filter(
            hospital=hospital_instancia, 
            estado='ativo'
        ).count()

    # 3. Enviar para o HTML com os nomes corretos (stock_total2 e pedidos_pendentes2)
    return render(request, 'hospital.html', {
        'nome_hospital': hospital_instancia.nome if hospital_instancia else "Hospital",
        'nome_banco': banco_instancia.nome if banco_instancia else "Banco Central",
        'ultimo_login': request.user.last_login,
        'stock_total2': qtd_stock_global,
        'pedidos_pendentes2': qtd_pedidos_meus,
    })


@login_required
def pagina_posto(request):
    # Verificação de segurança: usa 'posto' conforme o seu AbstractUser
    if request.user.tipo != 'posto':
        messages.error(request, "Acesso negado. Apenas postos podem entrar aqui.")
        return redirect('login')
    
    # Estatísticas para o Dashboard
    total_dadores = Dador.objects.count()
    total_doacoes = Doacao.objects.filter(valido=True).count()

    context = {
        'total_dadores': total_dadores,
        'total_doacoes': total_doacoes,
        'nome_banco': Banco.objects.first().nome if Banco.objects.exists() else "Banco Central",
        'ultimo_login': request.user.last_login, # Pega na data real do último login
    }
    return render(request, 'posto.html', context)


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
        'titulo': "Stock Total por Tipo Sanguíneo",
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
def stock_total_central(request):
    tipos = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    # Garante que estes nomes batem certo com a tua BD
    comps = ["Sangue", "Plasma", "Globulos Vermelhos"]
    limite = 5
    stock_ideal = 20

    componentes_data = []
    for c in comps:
        itens_do_comp = []
        for t in tipos:
            qtd = Doacao.objects.filter(dador__tipo_sangue=t, componente__iexact=c, valido=True).count()
            perc = min((qtd / stock_ideal) * 100, 100)
            itens_do_comp.append({
                'tipo': t,
                'quantidade': qtd,
                'percentagem': perc,
                'ruptura': qtd == 0,
                'critico': qtd < limite and qtd > 0
            })
        componentes_data.append({'nome': c, 'itens': itens_do_comp})

    return render(request, 'stock_total_central.html', {
        'componentes_data': componentes_data,
        'titulo': "Monitor de Stock Global"
    })


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
    return render(request, 'gestao_dadores.html',
        {'nome_banco': Banco.objects.first().nome if Banco.objects.exists() else "Banco Central",
        'ultimo_login': request.user.last_login, # Pega na data real do último login
        })


@login_required
def gestao_doacoes(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'gestao_doacoes.html',
        {'nome_banco': Banco.objects.first().nome if Banco.objects.exists() else "Banco Central",
        'ultimo_login': request.user.last_login, # Pega na data real do último login
        })

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
            dador = Dador.objects.filter(nif=search_nif).first()
            if not dador:
                messages.warning(request, f"NIF '{search_nif}' não encontrado.")

    if request.method == 'POST':
        nif = request.POST.get('nif')
        dador = get_object_or_404(Dador, nif=nif)
        
        # 1. Verificar idade (já tinhas e está bem)
        if dador.idade < 18:
            messages.error(request, "Impossível ativar: dador menor de idade.")
            return redirect('gestao_dadores')

        # 2. Verificar se o período de repouso já passou
        ultima = Doacao.objects.filter(dador=dador).order_by('-data').first()
        if ultima:
            intervalo = 120 if dador.genero == 'Feminino' else 90
            dias_passados = (date.today() - ultima.data).days
            
            if dias_passados < intervalo:
                messages.error(request, f"Impossível ativar! O dador ainda está em período de carência (faltam {intervalo - dias_passados} dias).")
                return redirect('gestao_dadores')

        dador.ativo = True
        dador.save()
        messages.success(request, f"O dador {dador.nome} está agora APTO para doar.")
        return redirect('gestao_dadores')

    return render(request, 'ativar_dador.html', {'dador': dador, 'titulo': "Ativar Dador"})


@login_required
def listar_dadores(request):
    # Lógica futura aqui. Por agora, apenas mostra a página.
    return render(request, 'listar_dadores.html')


@login_required
def dadores_tipo_sangue(request):
    dadores_por_grupo = {}
    for codigo, nome_bonito in TipoSangue.choices:
        # Filtramos pelo código (que é o que está guardado na base de dados)
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
def gestao_pedidos(request):
    return render(request, 'gestao_pedidos.html')


@login_required
def atualizar_hospital(request):
    if request.user.tipo != 'hospital':
        messages.error(request, "Acesso negado.")
        return redirect('home')
    
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

    perfil = getattr(request.user, 'perfil_hospital', None)
    hospital_instancia = perfil.hospital if perfil else None
    banco_instancia = hospital_instancia.banco if hospital_instancia else None

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        formset = PedidoLinhaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # 1. Salvar o cabeçalho do pedido
            pedido = form.save(commit=False)
            pedido.hospital = hospital_instancia
            pedido.banco = banco_instancia
            pedido.save()

            # 2. Salvar as linhas do pedido e guardá-las numa lista para verificação
            linhas_criadas = []
            for f in formset:
                if f.cleaned_data.get('quantidade') and f.cleaned_data.get('quantidade') > 0:
                    linha = f.save(commit=False)
                    linha.pedido = pedido
                    linha.banco = banco_instancia
                    linha.save()
                    linhas_criadas.append(linha)

            # 3. VERIFICAÇÃO DE STOCK AUTOMÁTICA
            pode_satisfazer_agora = True
            for linha in linhas_criadas:
                stock_atual = Doacao.objects.filter(
                    dador__tipo_sangue=linha.tipo,
                    componente=linha.componente,
                    valido=True, # Apenas contamos o que está disponível
                    banco=banco_instancia
                ).count()
                
                if stock_atual < linha.quantidade:
                    pode_satisfazer_agora = False
                    break

            # 4. CONSUMO DE STOCK (Mudar estado para inválido)
            if pode_satisfazer_agora and linhas_criadas:
                for linha in linhas_criadas:
                    # Seleciona as doações mais antigas para usar primeiro (FIFO)
                    doacoes_a_consumir = Doacao.objects.filter(
                        dador__tipo_sangue=linha.tipo,
                        componente=linha.componente,
                        valido=True,
                        banco=banco_instancia
                    ).order_by('data')[:linha.quantidade]
                    
                    # Ciclo para mudar o estado de cada bolsa individualmente
                    for d in doacoes_a_consumir:
                        d.valido = False
                        d.save()
                
                pedido.estado = "concluido"
                pedido.save()
                messages.success(request, "Pedido satisfeito automaticamente com o stock existente!")
            else:
                messages.warning(request, "Pedido registado em espera por falta de stock disponível.")

            return redirect('listar_pedidos')
    else:
        form = PedidoForm()
        formset = PedidoLinhaFormSet()

    return render(request, 'criar_pedido.html', {
        'form': form, 
        'formset': formset, 
        'titulo': "Novo Pedido de Sangue"
    }) 

@login_required
def cancelar_pedido(request, pedido_id):
    """Cancela um pedido pendente mudando o estado para 'cancelado'"""
    # Procura o pedido pelo ID
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Obtém o perfil do hospital logado
    perfil = getattr(request.user, 'perfil_hospital', None)
    hospital_logado = perfil.hospital if perfil else None

    # Verifica se o pedido pertence ao hospital logado e se ainda está ativo
    if hospital_logado and pedido.hospital == hospital_logado:
        if pedido.estado == "ativo":
            pedido.estado = "cancelado" # Usa a string definida no teu EstadoPedido
            pedido.save()
            messages.success(request, f"Pedido #{pedido.id} cancelado com sucesso!")
        else:
            messages.warning(request, "Apenas pedidos ativos podem ser cancelados.")
    else:
        messages.error(request, "Não tem permissão para cancelar este pedido.")

    return redirect('listar_pedidos') # Nome definido no teu urls.py

@login_required
def listar_pedidos_hospital(request):
    """Lista o histórico de pedidos do hospital logado"""
    if request.user.tipo != 'hospital':
        return redirect('home')

    # Obtém a instância do hospital associada ao utilizador
    perfil = getattr(request.user, 'perfil_hospital', None)
    hospital_instancia = perfil.hospital if perfil else None

    # Carrega os pedidos e as respetivas linhas (itens) para evitar múltiplas consultas
    pedidos = Pedido.objects.filter(hospital=hospital_instancia).prefetch_related('itens').order_by('-data')

    return render(request, 'listar_pedidos.html', {
        'pedidos': pedidos,
        'titulo': "Histórico de Pedidos"
    })

@login_required
def registar_doacao(request):
    if request.user.tipo != 'posto':
        return redirect('home') 

    if request.method == 'POST':
        doacao_form = DoacaoForm(request.POST)
        if doacao_form.is_valid():
            dador = doacao_form.cleaned_data['nif_dador']
            
            # BLOQUEIO: Só doa se dador estiver apto
            if not dador.ativo:
                messages.error(request, f"O dador {dador.nome} não está apto para doar atualmente.")
                return redirect('gestao_doacoes')

            # Salvar a nova doação como disponível (valido=True)
            doacao_nova = doacao_form.save(commit=False)

            # 2. ATRIBUIÇÃO AUTOMÁTICA DO POSTO E VALIDADE
            perfil = getattr(request.user, 'perfil_posto', None)
            if perfil:
                doacao_nova.posto = perfil.posto # Preenche o posto automaticamente

            doacao_nova.banco = dador.banco
            doacao_nova.valido = True
            doacao_nova.save()

            # Atualizar dador: data e ficar inapto pelo período de carência
            dador.ultimaDoacao = date.today()
            dador.ativo = False 
            dador.save()

            # --- TENTAR SATISFAZER PEDIDOS ATIVOS LOGO APÓS A DOAÇÃO ---
            pedidos_ativos = Pedido.objects.filter(
                estado="ativo", 
                banco=doacao_nova.banco
            ).order_by('data')

            for pedido in pedidos_ativos:
                linhas = pedido.itens.all()
                pode_fechar = True
                
                # Verificar se o stock total (incluindo a nova doação) satisfaz este pedido
                for linha in linhas:
                    stock = Doacao.objects.filter(
                        dador__tipo_sangue=linha.tipo,
                        componente=linha.componente,
                        valido=True,
                        banco=pedido.banco
                    ).count()
                    if stock < linha.quantidade:
                        pode_fechar = False
                        break
                
                # Se houver stock, "consome" as bolsas mudando o estado
                if pode_fechar:
                    for linha in linhas:
                        doacoes_em_stock = Doacao.objects.filter(
                            dador__tipo_sangue=linha.tipo,
                            componente=linha.componente,
                            valido=True,
                            banco=pedido.banco
                        ).order_by('data')[:linha.quantidade]
                        
                        for d in doacoes_em_stock:
                            d.valido = False
                            d.save()
                    
                    pedido.estado = "concluido"
                    pedido.save()
            
            messages.success(request, f"Doação de {dador.nome} registada com sucesso.")
            return redirect('gestao_doacoes')
    else:
        doacao_form = DoacaoForm()

    return render(request, 'registar_doacao.html', {
        'entidade_form': doacao_form, 
        'titulo': "Nova Doação"
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
    dias_restantes = 0
    if dador_encontrado:
        ultima = lista_doacoes.first() # Já está order_by -data
        if ultima:
            intervalo = 120 if dador_encontrado.genero == 'Feminino' else 90
            dias_passados = (date.today() - ultima.data).days
            dias_restantes = max(0, intervalo - dias_passados)
            
    return render(request, 'historico_dador.html', {
        'dador': dador_encontrado,
        'doacoes': lista_doacoes,
        'dias_restantes': dias_restantes,
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
    # Usamos select_related para carregar os dados do dador de forma eficiente
    doacoes = Doacao.objects.all().select_related('dador').order_by('-data')
    
    total_geral = doacoes.count()
    
    # Se precisares destas estatísticas para esta página, o cálculo continua aqui:
    por_tipo = Doacao.objects.values('dador__tipo_sangue').annotate(qtd=Count('id'))
    for item in por_tipo:
        item['percentagem'] = (item['qtd'] / total_geral * 100) if total_geral > 0 else 0

    # IMPORTANTE: O return deve estar fora do loop 'for'
    return render(request, 'consultar_doacoes.html', {
        'doacoes': doacoes,
        'titulo': "Consultar doações",
        'por_tipo': por_tipo # Caso queiras mostrar o resumo algures
    })
   
@login_required
def estatisticas_hospital(request):
    if request.user.tipo != 'hospital':
        return redirect('home')
    
    perfil = getattr(request.user, 'perfil_hospital', None)
    hospital = perfil.hospital if perfil else None
    
    # KPIs (Cartões Superiores)
    total_pedidos = Pedido.objects.filter(hospital=hospital).count()
    concluidos = Pedido.objects.filter(hospital=hospital, estado='concluido').count()
    ativos = Pedido.objects.filter(hospital=hospital, estado='ativo').count()
    total_unidades = LinhaPedido.objects.filter(pedido__hospital=hospital).aggregate(Sum('quantidade'))['quantidade__sum'] or 0

    # Gráfico de Barras: Distribuição por Tipo de Sangue mais pedido
    # Calculamos a percentagem para as barras de progresso
    por_tipo = LinhaPedido.objects.filter(pedido__hospital=hospital).values('tipo').annotate(qtd=Sum('quantidade')).order_by('-qtd')
    
    for item in por_tipo:
        if total_unidades > 0:
            item['percentagem'] = (item['qtd'] / total_unidades) * 100
        else:
            item['percentagem'] = 0

    context = {
        'hospital': hospital,
        'total_pedidos': total_pedidos,
        'concluidos': concluidos,
        'ativos': ativos,
        'total_unidades': total_unidades,
        'por_tipo': por_tipo,
        'titulo': "Estatísticas do Hospital",
        'nome_banco': hospital.banco.nome if hospital else "Banco Central"
    }
    return render(request, 'estatisticas_hospital.html', context)


#######################################################

from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from .models import (
    Utilizador, Banco, PostoRecolha, Hospital, 
    Dador, Doacao, Pedido, LinhaPedido
)
from .serializers import (
    UtilizadorSerializer, BancoSerializer, PostoRecolhaSerializer, 
    HospitalSerializer, DadorSerializer, DoacaoSerializer, 
    PedidoSerializer, LinhaPedidoSerializer
)

class UtilizadorViewSet(viewsets.ModelViewSet):
    queryset = Utilizador.objects.all()
    serializer_class = UtilizadorSerializer
    permission_classes = [IsAuthenticated] # Ou IsAdminUser para segurança extra

class BancoViewSet(viewsets.ModelViewSet):
    queryset = Banco.objects.all()
    serializer_class = BancoSerializer
    permission_classes = [IsAuthenticated]

class PostoRecolhaViewSet(viewsets.ModelViewSet):
    queryset = PostoRecolha.objects.all()
    serializer_class = PostoRecolhaSerializer
    permission_classes = [IsAuthenticated]

class DadorViewSet(viewsets.ModelViewSet):
    serializer_class = DadorSerializer
    permission_classes = [IsAuthenticated]
    queryset = Dador.objects.all() 
    serializer_class = DadorSerializer

    def get_queryset(self):
        user = self.request.user
        # Se for admin, vê tudo. Se for posto, vê apenas os dadores do banco dele.
        if user.tipo == 'posto' and hasattr(user, 'perfil_posto'):
            return Dador.objects.filter(banco=user.perfil_posto.posto.banco)
        elif user.tipo == 'admin':
            return Dador.objects.all()
        return Dador.objects.none() # Hospital não deve ver dadores

class DoacaoViewSet(viewsets.ModelViewSet):
    queryset = Doacao.objects.all()
    serializer_class = DoacaoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Associa automaticamente o posto do utilizador logado à doação
        if self.request.user.tipo == 'posto':
            serializer.save(
                posto=self.request.user.perfil_posto.posto,
                banco=self.request.user.perfil_posto.posto.banco
            )
        else:
            serializer.save()

class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    permission_classes = [IsAuthenticated]

class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo == 'hospital' and hasattr(user, 'perfil_hospital'):
            return Pedido.objects.filter(hospital=user.perfil_hospital.hospital)
        elif user.tipo == 'admin':
            return Pedido.objects.all()
        return Pedido.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.tipo == 'hospital':
            # Associa o hospital e o banco automaticamente para evitar fraudes
            serializer.save(
                hospital=user.perfil_hospital.hospital,
                banco=user.perfil_hospital.hospital.banco
            )
        else:
            serializer.save()

class LinhaPedidoViewSet(viewsets.ModelViewSet):
    queryset = LinhaPedido.objects.all()
    serializer_class = LinhaPedidoSerializer
    permission_classes = [IsAuthenticated]