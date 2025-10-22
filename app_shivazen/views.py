# app_shivazen/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
# Removido 'make_password' e 'check_password', 'login_required'
# Adicionado sistema de autenticação padrão do Django
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime, timedelta
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
                    return redirect('/admin/')
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
        return redirect('/admin/')
    return render(request, 'telas/tela_painel.html')

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
    return render(request, 'telas/tela_cadastro_profissional.html') 
    
@login_required(login_url='/login/')
def profissionalEditar(request):
    return render(request, 'telas/tela_editar_profissional.html')