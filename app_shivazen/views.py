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
            # Tenta autenticar tanto como um usuário do sistema (admin/recepção) quanto como cliente
            if '@' in login_identifier:
                usuario = Usuario.objects.get(email=login_identifier)
            else:
                # Se não for um email, pode ser um CPF de cliente ou um nome de usuário de admin
                try:
                    cliente = Cliente.objects.get(cpf=login_identifier)
                    usuario = Usuario.objects.get(email=cliente.email)
                except (Cliente.DoesNotExist, Usuario.DoesNotExist):
                     # Se não for CPF de cliente, pode ser um nome de usuário do admin do Django
                    from django.contrib.auth.models import User
                    try:
                        django_user = User.objects.get(username=login_identifier)
                        usuario = Usuario.objects.get(email=django_user.email) # Assumindo que o email é o mesmo
                    except (User.DoesNotExist, Usuario.DoesNotExist):
                        raise Usuario.DoesNotExist

        except (Usuario.DoesNotExist, Cliente.DoesNotExist):
            messages.error(request, 'Usuário não encontrado.')
            return redirect('shivazen:usuarioLogin')

        # Verifica se a senha está correta
        senha_valida = check_password(senha, usuario.senha_hash)

        # Para superusuários, também verifica a senha do sistema Django
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
            
            # *** LÓGICA DE REDIRECIONAMENTO ***
            if usuario.perfil.nome in ['Administrador', 'Recepcionista', 'Profissional']:
                # Se for um perfil administrativo, redireciona para a interface de admin
                from django.contrib.auth import login as auth_login
                from django.contrib.auth.models import User
                try:
                    # Loga o usuário no sistema de admin do Django para dar acesso
                    django_user = User.objects.get(email=usuario.email)
                    auth_login(request, django_user)
                    messages.success(request, f'Bem-vindo(a), {usuario.nome}!')
                    return redirect('/admin/') # URL do painel admin
                except User.DoesNotExist:
                    messages.error(request, 'Conta de administrador não sincronizada. Contate o suporte.')
                    return redirect('shivazen:usuarioLogin')
            else:
                # Se for um cliente, redireciona para o painel do cliente
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
    logout(request) # Faz o logout do sistema de admin do Django
    request.session.flush() # Limpa a sessão personalizada
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('shivazen:inicio')

def esqueciSenha(request):
    return render(request, 'usuario/esqueciSenha.html')


# --- Área Restrita (Protegida por Login) ---
@login_required(login_url='/login/')
def painel(request):
    # Verifica se quem está acessando não é um admin para evitar acesso indevido
    if request.session.get('usuario_perfil') != 'Cliente':
        return redirect('/admin/')
    return render(request, 'telas/tela_painel.html')

@login_required(login_url='/login/')
def agendaCadastro(request):
    if request.method == 'POST':
        # (Lógica de POST do agendamento aqui...)
        pass
    
    profissionais = Profissional.objects.filter(ativo=True)
    context = {'profissionais': profissionais}
    return render(request, 'agenda/agendamento.html', context)

# --- VIEWS AUXILIARES PARA AJAX ---
@login_required(login_url='/login/')
def buscar_procedimentos(request):
    # (Código da view AJAX aqui...)
    pass

@login_required(login_url='/login/')
def buscar_horarios(request):
    # (Código da view AJAX aqui...)
    pass

# Manter estas views protegidas
@login_required(login_url='/login/')
def prontuarioconsentimento(request):
    return render(request, 'telas/ProntuarioConsentimento.html') 

@login_required(login_url='/login/')
def profissionalCadastro(request):
    return render(request, 'telas/tela_cadastro_profissional.html') 
    
@login_required(login_url='/login/')
def profissionalEditar(request):
    return render(request, 'telas/tela_editar_profissional.html')