# app_shivazen/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
# Removido 'make_password' e 'check_password', 'login_required'
# Adicionado sistema de autenticação padrão do Django
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, timedelta
import json
# Importamos o NOVO modelo de usuário
from .models import * # --- Páginas Abertas ---
def home(request):
    return render(request, 'inicio/home.html')

def termosUso(request):
    return render(request, 'inicio/termosUso.html')

def politicaPrivacidade(request):
    return render(request, 'inicio/politicaPrivacidade.html')

def quemsomos(request):
    return render(request, 'inicio/quemsomos.html')

def agendaContato(request):
    return render(request, 'agenda/contato.html')

# --- Autenticação e Cadastro (Refatorado) ---
def usuarioCadastro(request):
    if request.method == 'POST':
        nome = request.POST.get('nome-completo')
        cpf = request.POST.get('cpf')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        senha = request.POST.get('senha')

        # Verifica se Cliente (CPF) ou Usuário (Email) já existem
        if Cliente.objects.filter(cpf=cpf).exists() or Usuario.objects.filter(email=email).exists():
            messages.error(request, 'CPF ou E-mail já cadastrado.')
            return redirect('shivazen:usuarioCadastro')

        try:
            # Cria o Cliente
            novo_cliente = Cliente.objects.create(nome_completo=nome, cpf=cpf, email=email, telefone=telefone)
            # Cria o Prontuário associado
            Prontuario.objects.create(cliente=novo_cliente)

            # Busca ou cria o Perfil de 'Cliente'
            perfil_cliente, _ = Perfil.objects.get_or_create(nome='Cliente', defaults={'descricao': 'Perfil para clientes da clínica.'})
            
            # --- Cria o Usuário (Método Django) ---
            # Usa 'create_user' que cuida automaticamente do hash da senha
            Usuario.objects.create_user(
                username=email, # Usamos email como username também
                email=email,
                password=senha,
                first_name=nome, # Usamos first_name para o nome
                perfil=perfil_cliente,
                is_active=True # is_active substitui o campo 'ativo'
            )

            messages.success(request, 'Cadastro realizado com sucesso! Faça o login.')
            return redirect('shivazen:usuarioLogin')
        
        except Exception as e:
            messages.error(request, f'Ocorreu um erro durante o cadastro: {e}')
            # Se deu erro, tentamos remover o cliente (se foi criado)
            Cliente.objects.filter(cpf=cpf).delete() 
            return redirect('shivazen:usuarioCadastro')

    return render(request, 'usuario/cadastro.html')

def usuarioLogin(request):
    if request.method == 'POST':
        login_identifier = request.POST.get('login') # Pode ser email ou CPF
        senha = request.POST.get('senha')
        email_para_auth = None

        try:
            # 1. Tenta identificar o email
            if '@' in login_identifier:
                email_para_auth = login_identifier
            else:
                # Se não for email, busca o cliente pelo CPF
                try:
                    cliente = Cliente.objects.get(cpf=login_identifier)
                    email_para_auth = cliente.email
                except Cliente.DoesNotExist:
                    pass # Se não achar, o 'authenticate' vai falhar
            
            if not email_para_auth:
                messages.error(request, 'E-mail/CPF ou senha incorretos.')
                return redirect('shivazen:usuarioLogin')

            # 2. Autentica com o sistema do Django (usando 'email' e 'password')
            usuario_autenticado = authenticate(request, email=email_para_auth, password=senha)

            if usuario_autenticado is not None:
                # 3. Faz o login
                auth_login(request, usuario_autenticado) 
                
                # 4. Armazena dados da sessão
                request.session['usuario_id'] = usuario_autenticado.id
                request.session['usuario_nome'] = usuario_autenticado.first_name
                if usuario_autenticado.perfil:
                    request.session['usuario_perfil'] = usuario_autenticado.perfil.nome

                # 5. Redireciona baseado no perfil
                # 'is_staff' é um campo padrão do Django para acesso ao Admin
                if usuario_autenticado.is_staff:
                    messages.success(request, f'Bem-vindo(a), {usuario_autenticado.first_name}!')
                    return redirect('shivazen:adminDashboard')
                else:
                    # Se for cliente, guarda o ID do cliente na sessão
                    try:
                        cliente = Cliente.objects.get(email=usuario_autenticado.email)
                        request.session['cliente_id'] = cliente.id_cliente
                    except Cliente.DoesNotExist:
                        pass # Usuário sem cliente associado
                    messages.success(request, f'Bem-vindo(a), {usuario_autenticado.first_name}!')
                    return redirect('shivazen:painel')
            else:
                # Falha na autenticação
                messages.error(request, 'E-mail/CPF ou senha incorretos.')
                return redirect('shivazen:usuarioLogin')

        except Exception as e:
            messages.error(request, f'Ocorreu um erro inesperado: {e}')
            return redirect('shivazen:usuarioLogin')
            
    return render(request, 'usuario/login.html')


def usuarioLogout(request):
    auth_logout(request) # Usa o logout padrão do Django
    # request.session.flush() # O auth_logout já limpa a sessão de autenticação
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('shivazen:inicio')

def esqueciSenha(request):
    return render(request, 'usuario/esqueciSenha.html')

# --- Área Restrita ---
@login_required(login_url='/login/')
def painel(request):
    # 'is_staff' é a forma correta de verificar se é admin/profissional
    if request.user.is_staff:
        return redirect('shivazen:adminDashboard')
    
    # Busca o cliente associado ao usuário
    try:
        cliente = Cliente.objects.get(email=request.user.email)
        cliente_id = cliente.id_cliente
        
        # Busca agendamentos do cliente
        agendamentos = Atendimento.objects.filter(
            cliente_id=cliente_id
        ).select_related('profissional', 'procedimento').order_by('-data_hora_inicio')[:10]
        
        # Estatísticas do cliente
        agendamentos_proximos = Atendimento.objects.filter(
            cliente_id=cliente_id,
            data_hora_inicio__gte=datetime.now(),
            status_atendimento__in=['AGENDADO', 'CONFIRMADO']
        ).select_related('profissional', 'procedimento').order_by('data_hora_inicio')[:5]
        
        total_agendamentos = Atendimento.objects.filter(cliente_id=cliente_id).count()
        agendamentos_realizados = Atendimento.objects.filter(
            cliente_id=cliente_id,
            status_atendimento='REALIZADO'
        ).count()
        
        context = {
            'cliente': cliente,
            'agendamentos': agendamentos,
            'agendamentos_proximos': agendamentos_proximos,
            'total_agendamentos': total_agendamentos,
            'agendamentos_realizados': agendamentos_realizados,
        }
        
        return render(request, 'telas/tela_painel.html', context)
    except Cliente.DoesNotExist:
        messages.error(request, 'Cliente não encontrado. Entre em contato com o suporte.')
        return redirect('shivazen:usuarioLogout')

@login_required(login_url='/login/')
def agendaCadastro(request):
    if request.method == 'POST':
        try:
            id_cliente = request.session.get('cliente_id')
            id_profissional = request.POST.get('profissional')
            id_procedimento = request.POST.get('procedimento')
            data_hora_str = request.POST.get('horario_selecionado') # Ex: "2024-10-30T10:30:00"
            
            if not all([id_cliente, id_profissional, id_procedimento, data_hora_str]):
                messages.error(request, 'Todos os campos são obrigatórios.')
                return redirect('shivazen:agendaCadastro')

            data_hora_inicio = datetime.fromisoformat(data_hora_str)
            
            cliente = Cliente.objects.get(pk=id_cliente)
            profissional = Profissional.objects.get(pk=id_profissional)
            procedimento = Procedimento.objects.get(pk=id_procedimento)

            data_hora_fim = data_hora_inicio + timedelta(minutes=procedimento.duracao_minutos)

            # Lógica de conflito (mantida)
            conflitos = Atendimento.objects.filter(
                profissional=profissional,
                data_hora_inicio__lt=data_hora_fim,
                data_hora_fim__gt=data_hora_inicio,
                status_atendimento__in=['AGENDADO', 'CONFIRMADO']
            ).exists()

            if conflitos:
                messages.error(request, 'Este horário já foi agendado. Por favor, escolha outro.')
                return redirect('shivazen:agendaCadastro')

            Atendimento.objects.create(
                cliente=cliente,
                profissional=profissional,
                procedimento=procedimento,
                data_hora_inicio=data_hora_inicio,
                data_hora_fim=data_hora_fim,
                status_atendimento='AGENDADO'
            )
            messages.success(request, 'Seu agendamento foi realizado com sucesso!')
            return redirect('shivazen:painel')

        except (Cliente.DoesNotExist, Profissional.DoesNotExist, Procedimento.DoesNotExist):
            messages.error(request, 'Erro ao encontrar dados essenciais (cliente, profissional ou procedimento).')
        except ValueError:
             messages.error(request, 'Formato de data ou hora inválido.')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao agendar: {e}')
        
        return redirect('shivazen:agendaCadastro')

    profissionais = Profissional.objects.filter(ativo=True)
    context = {'profissionais': profissionais}
    return render(request, 'agenda/agendamento.html', context)

# --- VIEWS AUXILIARES PARA AJAX (Refatoradas) ---
@login_required(login_url='/login/')
def buscar_procedimentos(request):
    if request.method == 'POST':
        id_profissional = request.POST.get('id_profissional')
        try:
            profissional = Profissional.objects.get(pk=id_profissional)
            # 'procedimento_set' é o related_name reverso do ManyToMany
            procedimentos = profissional.procedimento_set.filter(ativo=True).values('id_procedimento', 'nome')
            return JsonResponse(list(procedimentos), safe=False)
        except Profissional.DoesNotExist:
            return JsonResponse({'error': 'Profissional não encontrado'}, status=404)
    return JsonResponse({'error': 'Requisição inválida'}, status=400)

@login_required(login_url='/login/')
def buscar_horarios(request):
    if request.method == 'POST':
        id_profissional = request.POST.get('id_profissional')
        data_selecionada_str = request.POST.get('data') # Ex: "2024-10-30"
        try:
            data_selecionada = datetime.strptime(data_selecionada_str, '%Y-%m-%d').date()
            profissional = Profissional.objects.get(pk=id_profissional)
            
            # --- LÓGICA MOVIDA PARA O MODELO ---
            # Chamamos a função que criamos no models.py
            horarios_disponiveis = profissional.get_horarios_disponiveis(data_selecionada)
            # --- FIM DA LÓGICA MOVIDA ---

            return JsonResponse({'horarios': horarios_disponiveis})
        
        except Profissional.DoesNotExist:
            return JsonResponse({'error': 'Profissional não encontrado'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Data em formato inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Erro interno: {e}'}, status=500)
            
    return JsonResponse({'error': 'Requisição inválida'}, status=400)

# --- Telas Administrativas (Stubs) ---
@login_required(login_url='/login/')
def prontuarioconsentimento(request):
    return render(request, 'telas/ProntuarioConsentimento.html') 

@login_required(login_url='/login/')
def profissionalCadastro(request):
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Você precisa ser administrador.')
        return redirect('shivazen:painel')
    
    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            especialidade = request.POST.get('especialidade', '')
            ativo = request.POST.get('ativo') == 'on'
            
            profissional = Profissional.objects.create(
                nome=nome,
                especialidade=especialidade,
                ativo=ativo
            )
            
            # Processa disponibilidades
            dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
            dia_numero = {'segunda': 2, 'terca': 3, 'quarta': 4, 'quinta': 5, 'sexta': 6, 'sabado': 7, 'domingo': 1}
            
            for dia in dias_semana:
                hora_inicio = request.POST.get(f'hora_inicio_{dia}')
                hora_fim = request.POST.get(f'hora_fim_{dia}')
                trabalha = request.POST.get(f'trabalha_{dia}') == 'on'
                
                if trabalha and hora_inicio and hora_fim:
                    DisponibilidadeProfissional.objects.create(
                        profissional=profissional,
                        dia_semana=dia_numero[dia],
                        hora_inicio=hora_inicio,
                        hora_fim=hora_fim
                    )
            
            # Processa procedimentos
            procedimentos_ids = request.POST.getlist('procedimentos')
            for proc_id in procedimentos_ids:
                try:
                    procedimento = Procedimento.objects.get(pk=proc_id)
                    ProfissionalProcedimento.objects.get_or_create(
                        profissional=profissional,
                        procedimento=procedimento
                    )
                except Procedimento.DoesNotExist:
                    pass
            
            messages.success(request, f'Profissional {nome} cadastrado com sucesso!')
            return redirect('shivazen:adminDashboard')
            
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar profissional: {e}')
    
    procedimentos = Procedimento.objects.filter(ativo=True)
    dias_semana = {
        'segunda': 'Segunda-feira',
        'terca': 'Terça-feira',
        'quarta': 'Quarta-feira',
        'quinta': 'Quinta-feira',
        'sexta': 'Sexta-feira',
        'sabado': 'Sábado',
        'domingo': 'Domingo'
    }
    context = {
        'procedimentos': procedimentos,
        'dias_semana': dias_semana
    }
    return render(request, 'telas/tela_cadastro_profissional.html', context) 
    
@login_required(login_url='/login/')
def profissionalEditar(request):
    return render(request, 'telas/tela_editar_profissional.html')

# --- Dashboard Administrativo ---
@login_required(login_url='/login/')
def adminDashboard(request):
    """
    Dashboard administrativo com estatísticas e informações gerais
    """
    # Verifica se o usuário é staff/admin
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Você precisa ser administrador.')
        return redirect('shivazen:painel')
    
    from django.db.models import Count, Q, Sum
    from datetime import datetime, timedelta
    
    # Estatísticas gerais
    total_clientes = Cliente.objects.filter(ativo=True).count()
    total_profissionais = Profissional.objects.filter(ativo=True).count()
    total_procedimentos = Procedimento.objects.filter(ativo=True).count()
    
    # Agendamentos
    hoje = datetime.now().date()
    agendamentos_hoje = Atendimento.objects.filter(
        data_hora_inicio__date=hoje
    ).count()
    
    agendamentos_mes = Atendimento.objects.filter(
        data_hora_inicio__month=hoje.month,
        data_hora_inicio__year=hoje.year
    ).count()
    
    agendamentos_pendentes = Atendimento.objects.filter(
        status_atendimento='AGENDADO'
    ).count()
    
    agendamentos_confirmados = Atendimento.objects.filter(
        status_atendimento='CONFIRMADO'
    ).count()
    
    # Agendamentos recentes (últimos 10)
    agendamentos_recentes = Atendimento.objects.select_related(
        'cliente', 'profissional', 'procedimento'
    ).order_by('-data_hora_inicio')[:10]
    
    # Agendamentos por status
    agendamentos_por_status = Atendimento.objects.values('status_atendimento').annotate(
        total=Count('id_atendimento')
    ).order_by('-total')
    
    # Agendamentos dos próximos 7 dias
    proximos_7_dias = hoje + timedelta(days=7)
    agendamentos_proximos = Atendimento.objects.filter(
        data_hora_inicio__date__gte=hoje,
        data_hora_inicio__date__lte=proximos_7_dias
    ).select_related('cliente', 'profissional', 'procedimento').order_by('data_hora_inicio')[:10]
    
    # Receita do mês (se houver valores)
    receita_mes = Atendimento.objects.filter(
        data_hora_inicio__month=hoje.month,
        data_hora_inicio__year=hoje.year,
        valor_cobrado__isnull=False
    ).aggregate(total=Sum('valor_cobrado'))['total'] or 0
    
    # Profissionais mais ocupados (top 5)
    profissionais_ocupados = Profissional.objects.annotate(
        total_agendamentos=Count('atendimento')
    ).filter(ativo=True).order_by('-total_agendamentos')[:5]
    
    # Procedimentos mais solicitados (top 5)
    procedimentos_populares = Procedimento.objects.annotate(
        total_agendamentos=Count('atendimento')
    ).filter(ativo=True).order_by('-total_agendamentos')[:5]
    
    # Gráfico de agendamentos por dia da semana (últimos 30 dias)
    from django.db.models.functions import ExtractWeekDay
    agendamentos_semana = Atendimento.objects.filter(
        data_hora_inicio__gte=hoje - timedelta(days=30)
    ).annotate(
        dia_semana=ExtractWeekDay('data_hora_inicio')
    ).values('dia_semana').annotate(
        total=Count('id_atendimento')
    ).order_by('dia_semana')
    
    # Preparar dados para gráfico
    dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    dados_grafico_semana = [0] * 7
    for item in agendamentos_semana:
        # Django retorna 1=Dom, 2=Seg, etc. Ajustamos para índice do array
        idx = (item['dia_semana'] - 1) % 7
        dados_grafico_semana[idx] = item['total']
    
    context = {
        'total_clientes': total_clientes,
        'total_profissionais': total_profissionais,
        'total_procedimentos': total_procedimentos,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_mes': agendamentos_mes,
        'agendamentos_pendentes': agendamentos_pendentes,
        'agendamentos_confirmados': agendamentos_confirmados,
        'agendamentos_recentes': agendamentos_recentes,
        'agendamentos_proximos': agendamentos_proximos,
        'agendamentos_por_status': agendamentos_por_status,
        'receita_mes': float(receita_mes),
        'profissionais_ocupados': profissionais_ocupados,
        'procedimentos_populares': procedimentos_populares,
        'dados_grafico_semana': json.dumps(dados_grafico_semana),
        'dias_semana': json.dumps(dias_semana),
    }
    
    return render(request, 'admin/dashboard.html', context)

# --- Views Administrativas Adicionais ---
@login_required(login_url='/login/')
def adminAgendamentos(request):
    """Lista todos os agendamentos para administradores"""
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Você precisa ser administrador.')
        return redirect('shivazen:painel')
    
    status_filter = request.GET.get('status', '')
    data_filter = request.GET.get('data', '')
    
    agendamentos = Atendimento.objects.select_related(
        'cliente', 'profissional', 'procedimento'
    ).order_by('-data_hora_inicio')
    
    if status_filter:
        agendamentos = agendamentos.filter(status_atendimento=status_filter)
    
    if data_filter:
        try:
            data = datetime.strptime(data_filter, '%Y-%m-%d').date()
            agendamentos = agendamentos.filter(data_hora_inicio__date=data)
        except ValueError:
            pass
    
    context = {
        'agendamentos': agendamentos[:50],  # Limita a 50 para performance
        'status_filter': status_filter,
        'data_filter': data_filter,
    }
    
    return render(request, 'admin/agendamentos.html', context)

@login_required(login_url='/login/')
def adminProcedimentos(request):
    """Gestão de procedimentos e preços"""
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Você precisa ser administrador.')
        return redirect('shivazen:painel')
    
    procedimentos = Procedimento.objects.prefetch_related('preco_set').filter(ativo=True)
    profissionais = Profissional.objects.filter(ativo=True)
    
    context = {
        'procedimentos': procedimentos,
        'profissionais': profissionais,
    }
    
    return render(request, 'admin/procedimentos.html', context)

@login_required(login_url='/login/')
def adminBloqueios(request):
    """Lista bloqueios de agenda"""
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Você precisa ser administrador.')
        return redirect('shivazen:painel')
    
    bloqueios = BloqueioAgenda.objects.select_related('profissional').order_by('-data_hora_inicio')
    
    # Filtra apenas bloqueios futuros ou ativos
    hoje = datetime.now()
    bloqueios_ativos = bloqueios.filter(data_hora_fim__gte=hoje)
    
    context = {
        'bloqueios': bloqueios_ativos[:30],
    }
    
    return render(request, 'admin/bloqueios.html', context)

@login_required(login_url='/login/')
def criarBloqueio(request):
    """Cria um novo bloqueio de agenda"""
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Você precisa ser administrador.')
        return redirect('shivazen:painel')
    
    if request.method == 'POST':
        try:
            profissional_id = request.POST.get('profissional')
            data_hora_inicio_str = request.POST.get('data_hora_inicio')
            data_hora_fim_str = request.POST.get('data_hora_fim')
            motivo = request.POST.get('motivo', '')
            
            data_hora_inicio = datetime.fromisoformat(data_hora_inicio_str.replace('T', ' '))
            data_hora_fim = datetime.fromisoformat(data_hora_fim_str.replace('T', ' '))
            
            profissional = None
            if profissional_id:
                profissional = Profissional.objects.get(pk=profissional_id)
            
            BloqueioAgenda.objects.create(
                profissional=profissional,
                data_hora_inicio=data_hora_inicio,
                data_hora_fim=data_hora_fim,
                motivo=motivo
            )
            
            messages.success(request, 'Bloqueio criado com sucesso!')
            return redirect('shivazen:adminBloqueios')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar bloqueio: {e}')
    
    profissionais = Profissional.objects.filter(ativo=True)
    context = {'profissionais': profissionais}
    return render(request, 'admin/criar_bloqueio.html', context)

@login_required(login_url='/login/')
def excluirBloqueio(request, bloqueio_id):
    """Exclui um bloqueio de agenda"""
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Você precisa ser administrador.')
        return redirect('shivazen:painel')
    
    try:
        bloqueio = BloqueioAgenda.objects.get(pk=bloqueio_id)
        bloqueio.delete()
        messages.success(request, 'Bloqueio excluído com sucesso!')
    except BloqueioAgenda.DoesNotExist:
        messages.error(request, 'Bloqueio não encontrado.')
    except Exception as e:
        messages.error(request, f'Erro ao excluir bloqueio: {e}')
    
    return redirect('shivazen:adminBloqueios')