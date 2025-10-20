# app_shivazen/urls.py
from django.urls import path
from . import views

app_name = 'shivazen'

urlpatterns = [
    # --- Rotas Abertas (Públicas) ---
    path('', views.home, name='inicio'),
    path('quemsomos/', views.quemsomos, name='quemsomos'),
    path('termos-de-uso/', views.termosUso, name='termosUso'),
    path('politica-de-privacidade/', views.politicaPrivacidade, name='politicaPrivacidade'),
    path('contato/', views.agendaContato, name='agendaContato'),

    # --- Rotas de Autenticação ---
    path('cadastro/', views.usuarioCadastro, name='usuarioCadastro'),
    path('login/', views.usuarioLogin, name='usuarioLogin'),
    path('logout/', views.usuarioLogout, name='usuarioLogout'),
    path('esqueci-senha/', views.esqueciSenha, name='esqueciSenha'),

    # --- Rotas da Área Restrita (Painel do Cliente/Admin) ---
    path('painel/', views.painel, name='painel'),
    path('painel/agendamento/', views.agendaCadastro, name='agendaCadastro'),
    path('painel/prontuario/', views.prontuarioconsentimento, name='prontuarioconsentimento'),
    path('painel/cadastrar-profissional/', views.profissionalCadastro, name='profissionalCadastro'),
    path('painel/editar-profissional/', views.profissionalEditar, name='profissionalEditar'),

    # --- Rotas para chamadas AJAX do agendamento ---
    path('ajax/buscar-procedimentos/', views.buscar_procedimentos, name='buscar_procedimentos'),
    path('ajax/buscar-horarios/', views.buscar_horarios, name='buscar_horarios'),
]