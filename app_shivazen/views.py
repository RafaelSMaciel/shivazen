# app_shivazen/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import *

# --- Páginas Abertas ---
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

# --- Autenticação e Cadastro ---
def usuarioCadastro(request):
    if request.method == 'POST':
        nome = request.POST.get('nome-completo')
        cpf = request.POST.get('cpf')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        senha = request.POST.get('senha')

        if Cliente.objects.filter(cpf=cpf).exists() or Usuario.objects.filter(email=email).exists():
            messages.error(request, 'CPF ou E-mail já cadastrado.')
            return redirect('shivazen:usuarioCadastro')

        senha_hash = make_password(senha)
        
        novo_cliente = Cliente.objects.create(nome_completo=nome, cpf=cpf, email=email, telefone=telefone)
        Prontuario.objects.create(cliente=novo_cliente)

        perfil_cliente, _ = Perfil.objects.get_or_create(nome='Cliente', defaults={'descricao': 'Perfil para clientes da clínica.'})
        
        Usuario.objects.create(perfil=perfil_cliente, nome=nome, email=email, senha_hash=senha_hash, ativo=True)

        messages.success(request, 'Cadastro realizado com sucesso! Faça o login.')
        return redirect('shivazen:usuarioLogin')

    return render(request, 'usuario/cadastro.html')

def usuarioLogin(request):
    if request.method == 'POST':
        login_identifier = request.POST.get('login')
        senha = request.POST.get('senha')
        usuario = None
        try:
            if '@' in login_identifier:
                usuario = Usuario.objects.get(email=login_identifier)
            else:
                try:
                    cliente = Cliente.objects.get(cpf=login_identifier)
                    usuario = Usuario.objects.get(email=cliente.email)
                except (Cliente.DoesNotExist, Usuario.DoesNotExist):
                    from django.contrib.auth.models import User
                    try:
                        django_user = User.objects.get(username=login_identifier)
                        usuario = Usuario.objects.get(email=django_user.email)
                    except (User.DoesNotExist, Usuario.DoesNotExist):
                        raise Usuario.DoesNotExist
        except (Usuario.DoesNotExist, Cliente.DoesNotExist):
            messages.error(request, 'Usuário não encontrado.')
            return redirect('shivazen:usuarioLogin')

        senha_valida = check_password(senha, usuario.senha_hash)
        if not senha_valida:
            try:
                from django.contrib.auth.models import User
                django_user = User.objects.get(email=usuario.email)
                if django_user.check_password(senha):
                    senha_valida = True
            except User.DoesNotExist:
                pass
        
        if senha_valida:
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_nome'] = usuario.nome
            request.session['usuario_perfil'] = usuario.perfil.nome
            
            if usuario.perfil.nome in ['Administrador', 'Recepcionista', 'Profissional']:
                from django.contrib.auth import login as auth_login
                from django.contrib.auth.models import User
                try:
                    django_user = User.objects.get(email=usuario.email)
                    auth_login(request, django_user)
                    messages.success(request, f'Bem-vindo(a), {usuario.nome}!')
                    return redirect('/admin/')
                except User.DoesNotExist:
                    messages.error(request, 'Conta de administrador não sincronizada.')
                    return redirect('shivazen:usuarioLogin')
            else:
                try:
                    cliente = Cliente.objects.get(email=usuario.email)
                    request.session['cliente_id'] = cliente.id_cliente
                except Cliente.DoesNotExist:
                    pass
                messages.success(request, f'Bem-vindo(a), {usuario.nome}!')
                return redirect('shivazen:painel')
        else:
            messages.error(request, 'E-mail/CPF ou senha incorretos.')
            return redirect('shivazen:usuarioLogin')
    return render(request, 'usuario/login.html')

def usuarioLogout(request):
    from django.contrib.auth import logout
    logout(request)
    request.session.flush()
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('shivazen:inicio')

def esqueciSenha(request):
    return render(request, 'usuario/esqueciSenha.html')

# --- Área Restrita ---
@login_required(login_url='/login/')
def painel(request):
    if request.session.get('usuario_perfil') != 'Cliente':
        return redirect('/admin/')
    return render(request, 'telas/tela_painel.html')

@login_required(login_url='/login/')
def agendaCadastro(request):
    if request.method == 'POST':
        try:
            id_cliente = request.session.get('cliente_id')
            id_profissional = request.POST.get('profissional')
            id_procedimento = request.POST.get('procedimento')
            data_hora_str = request.POST.get('horario_selecionado')
            
            if not all([id_cliente, id_profissional, id_procedimento, data_hora_str]):
                messages.error(request, 'Todos os campos são obrigatórios.')
                return redirect('shivazen:agendaCadastro')

            data_hora_inicio = datetime.fromisoformat(data_hora_str)
            
            cliente = Cliente.objects.get(pk=id_cliente)
            profissional = Profissional.objects.get(pk=id_profissional)
            procedimento = Procedimento.objects.get(pk=id_procedimento)

            data_hora_fim = data_hora_inicio + timedelta(minutes=procedimento.duracao_minutos)

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

        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao agendar: {e}')
            return redirect('shivazen:agendaCadastro')

    profissionais = Profissional.objects.filter(ativo=True)
    context = {'profissionais': profissionais}
    return render(request, 'agenda/agendamento.html', context)

# --- VIEWS AUXILIARES PARA AJAX ---
@login_required(login_url='/login/')
def buscar_procedimentos(request):
    if request.method == 'POST':
        id_profissional = request.POST.get('id_profissional')
        try:
            profissional = Profissional.objects.get(pk=id_profissional)
            procedimentos = profissional.procedimento_set.filter(ativo=True).values('id_procedimento', 'nome')
            return JsonResponse(list(procedimentos), safe=False)
        except Profissional.DoesNotExist:
            return JsonResponse({'error': 'Profissional não encontrado'}, status=404)
    return JsonResponse({'error': 'Requisição inválida'}, status=400)

@login_required(login_url='/login/')
def buscar_horarios(request):
    if request.method == 'POST':
        id_profissional = request.POST.get('id_profissional')
        data_selecionada_str = request.POST.get('data')
        try:
            data_selecionada = datetime.strptime(data_selecionada_str, '%Y-%m-%d').date()
            dia_semana = data_selecionada.isoweekday() % 7 + 1 
            profissional = Profissional.objects.get(pk=id_profissional)
            disponibilidade = DisponibilidadeProfissional.objects.filter(profissional=profissional, dia_semana=dia_semana).first()

            if not disponibilidade:
                return JsonResponse({'horarios': []})

            agendamentos = Atendimento.objects.filter(profissional=profissional, data_hora_inicio__date=data_selecionada, status_atendimento__in=['AGENDADO', 'CONFIRMADO'])
            bloqueios = BloqueioAgenda.objects.filter(profissional=profissional, data_hora_inicio__date__lte=data_selecionada, data_hora_fim__date__gte=data_selecionada)

            horarios_disponiveis = []
            hora_atual = datetime.combine(data_selecionada, disponibilidade.hora_inicio)
            hora_fim_expediente = datetime.combine(data_selecionada, disponibilidade.hora_fim)

            while hora_atual < hora_fim_expediente:
                horario_ocupado = False
                for ag in agendamentos:
                    if hora_atual >= ag.data_hora_inicio and hora_atual < ag.data_hora_fim:
                        horario_ocupado = True
                        break
                if not horario_ocupado:
                    for bl in bloqueios:
                        if hora_atual >= bl.data_hora_inicio and hora_atual < bl.data_hora_fim:
                            horario_ocupado = True
                            break
                if not horario_ocupado:
                    horarios_disponiveis.append(hora_atual.strftime('%H:%M'))
                
                hora_atual += timedelta(minutes=30)

            return JsonResponse({'horarios': horarios_disponiveis})
        except (Profissional.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Dados inválidos'}, status=400)
    return JsonResponse({'error': 'Requisição inválida'}, status=400)

# --- Telas Administrativas (Stubs) ---
@login_required(login_url='/login/')
def prontuarioconsentimento(request):
    return render(request, 'telas/ProntuarioConsentimento.html') 

@login_required(login_url='/login/')
def profissionalCadastro(request):
    return render(request, 'telas/tela_cadastro_profissional.html') 
    
@login_required(login_url='/login/')
def profissionalEditar(request):
    return render(request, 'telas/tela_editar_profissional.html')